from decimal import Decimal
import time as tm


from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST, require_GET
from django.template.loader import render_to_string
from django_ratelimit.decorators import ratelimit
from django.shortcuts import get_object_or_404
from dotenv import load_dotenv
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import F

from .models import *
from userapp.utils.utils import *

load_dotenv()

from decimal import Decimal
from store.models import Product, PromoCode

DELIVERY_ZONES = {
    'пгт. Сокол (частный сектор)': 250,
    'пгт. Сокол (ул. Гагарина)': 100,
    'пгт. Сокол (ул. Королева)': 200,
    'пгт. Уптар': 600,
    'пгт. Стекольный': 650,
}

def calculate_cart_total_with_discount(cart, user):
    product_ids = cart.keys()
    products = Product.objects.filter(id__in=product_ids)
    product_dict = {str(product.id): product for product in products}

    total_price = Decimal('0.00')
    for product_id, item_data in cart.items():
        product = product_dict.get(product_id)
        if product:
            quantity = int(item_data['quantity'])
            total_price += Decimal(str(product.price)) * quantity

    total_price = total_price.quantize(Decimal('0.01'))

    discount_percent = 0
    discount_price = 0

    if user.is_authenticated:
        user_promos = PromoCode.objects.filter(
            promo__user=user,
            promo__active_usage=True,
            active=True
        ).prefetch_related('promo').distinct()
        discount_percent = sum(promo.discount_percent for promo in user_promos)

        if discount_percent:
            discount_price = total_price * (Decimal('1.00') - Decimal(discount_percent) / Decimal('100'))
            discount_price = discount_price.quantize(Decimal('0.01'))
    total_price = total_price.quantize(Decimal('0.01'))
    return {
        'total_price': total_price,
        'discount_price': discount_price,
        'discount_percent': discount_percent
    }

def get_price(req):
    rea_name = req.GET.get('area')
    is_pickup = req.GET.get('pickup') == 'true'
    is_door_delivery = req.GET.get('door_delivery') == 'true'

    # Если самовывоз — доставка бесплатна
    if is_pickup:
        delivery_fee = Decimal('0')
    else:
        delivery_fee = Decimal(str(DELIVERY_ZONES.get(rea_name, 0)))
        if is_door_delivery:
            delivery_fee += Decimal('50')

    cart = req.session.get('cart', {})
    product_ids = cart.keys()
    products = Product.objects.filter(id__in=product_ids)
    product_dict = {str(product.id): product for product in products}

    total_price = Decimal('0.00')
    for product_id, item_data in cart.items():
        product = product_dict.get(product_id)
        if product:
            quantity = int(item_data['quantity'])
            total_price += Decimal(str(product.price)) * quantity

    total_price = total_price.quantize(Decimal('0.01'))
    full_price_with_delivery = (total_price + delivery_fee).quantize(Decimal('0.01'))

    discount_percent = 0
    discount_price = full_price_with_delivery

    if req.user.is_authenticated:
        user_promos = PromoCode.objects.filter(
            promo__user=req.user,
            promo__active_usage=True,
            active=True
        ).prefetch_related('promo').distinct()
        discount_percent = sum(promo.discount_percent for promo in user_promos)

        if discount_percent:
            discount_price = full_price_with_delivery * (Decimal('1.00') - Decimal(discount_percent) / Decimal('100'))
            discount_price = discount_price.quantize(Decimal('0.01'))
    
    tm.sleep(1)

    return JsonResponse({
        'old_total': full_price_with_delivery,
        'final_total': discount_price,
        'delivery_fee': int(delivery_fee) if delivery_fee else '-'
    })



def catalog(request, category_slug=None):

    cart = request.session.get('cart', {})
    sub_categories = None
    category_name = None

    try:
        category = Category.objects.get(slug=category_slug)
    except Category.DoesNotExist:
        category = Category.objects.get(slug='all-products')

    products = Product.objects.filter(categories=category)
    if category.parent:
        category_name = category.parent.name
        category_slug = category.parent.slug
        sub_categories = category.parent.children.all()
    else:
        category_name = category.name
        category_slug = category.slug
        sub_categories = category.children.all()

    # Пагинация
    try:
        page_number = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page_number = 1

    paginator = Paginator(products, 30)

    page_obj = paginator.get_page(page_number)

    # AJAX-запрос — отдаем HTML карточек
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('store/includes/product_cards.html', {
            'products': page_obj,
            'cart': cart
        })
        return JsonResponse({'html': html, 'has_next': page_obj.has_next()})
    return render(request, 'store/catalog.html', {
        'products': page_obj,
        'category_name': category_name,
        'category_slug': category_slug,
        'sub': {slug: name for slug, name in sub_categories.values_list('slug', 'name')} if sub_categories else None,
        'cart': cart,
        'cart_count': sum(item.get('quantity', 0) for item in cart.values()),
        'has_next': page_obj.has_next()
    })

# Cart logic:
def cart(request):
    discount_percent = None
    discount_price = None
    cart = request.session.get('cart', {})
    previous_page = request.META.get('HTTP_REFERER')
    
    # Оптимизация 1: Получаем все данные за 2 запроса
    product_ids = cart.keys()
    
    # Запрос 1: Получаем все продукты из корзины одним запросом
    products = Product.objects.filter(id__in=product_ids)
    product_dict = {str(product.id): product for product in products}
    
    # Запрос 2: Получаем промокоды (только для авторизованных)
    user_promos = []
    if request.user.is_authenticated:
        user_promos = PromoCode.objects.filter(
            promo__user=request.user,
            promo__active_usage=True,
            active=True
        ).prefetch_related('promo').distinct()
        
        # Считаем общую скидку из уже полученных промокодов
        discount_percent = sum(promo.discount_percent for promo in user_promos)

    # Расчет total price and discount price
    prices = calculate_cart_total_with_discount(cart, request.user)
    total_price = prices['total_price']
    discount_price = prices['discount_price']
    discount_percent = prices['discount_percent']

    # Применяем скидку
    if discount_percent:
        discount_price = total_price * (Decimal('1.00') - Decimal(discount_percent) / Decimal('100'))
        discount_price = discount_price.quantize(Decimal('0.01'))

    return render(request, 'store/cart.html', {
        'cart_items': products,  # Готовый список товаров с доп. данными
        'total_price': total_price,
        'user_promos': user_promos,
        'discount_percent': discount_percent,
        'discount_price': discount_price,
        'cart': cart,
        'previous_page': previous_page, 
    })


def get_cart_count(request):
    cart = request.session.get('cart', {})
    cart_item_count = sum(data_item.get('quantity', 0) for item, data_item in cart.items())
    
    return JsonResponse({
        'count': cart_item_count,  # Общее количество товаров
        'cart_items': cart  # Список товаров
    })


def add_to_cart(request):
    if request.method == 'POST':
        # Получаем id продукта
        product_id = str(request.POST.get('product_id'))

        cart = request.session.get('cart', {})
        
        # Получаем продукт (можно оптимизировать bulk-запросом, если нужно несколько товаров)
        product = Product.objects.get(id=product_id)

        # Инициализация записи товара в корзине
        if product_id not in cart:
            cart[product_id] = {'quantity': 0}
        
        if cart[product_id]['quantity'] >= 20:
            return 

        # Обновляем количество
        cart[product_id]['quantity'] += 1
        new_quantity = cart[product_id]['quantity']

        # Оптимизированный расчет общей стоимости
        product_ids = cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        product_dict = {str(product.id): product for product in products}

        # Расчет total price and discount price
        prices = calculate_cart_total_with_discount(cart, request.user)
        total_price = prices['total_price']
        discount_price = prices['discount_price']
        discount_percent = prices['discount_percent']

        # Обновляем сессию
        request.session['cart'] = cart
        total_items = sum(item['quantity'] for item in cart.values())
        if total_items > 90:
            return 

        return JsonResponse({
            'cart_item_count': total_items,
            'new_quantity': new_quantity,
            'price': str(total_price),  # Decimal -> str для JSON
            'product_id': product_id,
            'discount_percent': discount_percent,
            'discount_price': discount_price
        })

def remove_from_cart(request):
    if request.method == 'POST':
        product_id = str(request.POST.get('product_id'))
        cart = request.session.get('cart', {})

        try:
            # Получаем продукт (можно убрать, если используем только product_dict)
            product = Product.objects.get(id=product_id)

            if product_id in cart:
                cart[product_id]["quantity"] -= 1
                if cart[product_id]["quantity"] <= 0:
                    del cart[product_id]

            # Расчет total price and discount price
            prices = calculate_cart_total_with_discount(cart, request.user)
            total_price = prices['total_price']

            request.session['cart'] = cart
            total_items = sum(item['quantity'] for item in cart.values())
            discount_price = prices['discount_price']
            discount_percent = prices['discount_percent']

            return JsonResponse({
                'cart_item_count': total_items,
                'new_quantity': cart.get(product_id, {}).get("quantity", 0),
                'price': str(total_price),  # Decimal -> str для JSON
                'product_id': product_id,
                'discount_percent': discount_percent,
                'discount_price': discount_price
            })

        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)

# Endcart logic
def checkout(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Вы не авторизованы')
        return redirect('login')
    orders = Order.objects.filter(user=request.user).exclude(status__in=['inactive', 'canceled', 'delivered']).order_by('-created_at')
    return render(request, 'store/checkout.html', {'orders': orders})

def product_page(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        previous_page = request.META.get('HTTP_REFERER')
        return render(request, 'store/product_page.html', {'product': product, 'previous_page': previous_page})
    except Product.DoesNotExist:
        messages.error(request, 'Товар не найден')
        return redirect('catalog')

def categories(request):
    return render(request, 'store/categories.html')

def custom_404_view(request, exception):
    return render(request, 'store/404.html', status=404)

@require_GET
def search_products(request):
    try:
        query = request.GET.get('q', '').strip()
        
        if not query:
            return JsonResponse({'result': []})

        # Фильтруем по названию (регистр не важен), ограничиваем 10ю результатами
        matched_products = Product.objects.filter(name__iregex=rf'{query}')[:10] # дружит с русскими буквами на основе регулярок 

        result = [{'id': p.id, 'name': p.name} for p in matched_products]
        
        return JsonResponse({'result': result})
    
    except Exception as e:
        return JsonResponse({'result': []})

def order_placing(request):
    if request.user.is_authenticated:
        discount_percent = None
        discount_price = None
        try:
            cart = request.session.get('cart', {})
            cart_items = [{'product': product, 'quantity': cart.get(str(product.id), {}).get('quantity', 0)} for product in Product.objects.filter(id__in=cart.keys())]

            if len(cart_items) > 0:
                total = sum(item['product'].price * item['quantity'] for item in cart_items)

                promo_codes = PromoCode.objects.filter(promo__user=request.user, promo__active_usage=True, active=True,)
                if promo_codes.exists():
                    discount_percent = sum(promo.discount_percent for promo in promo_codes)
                    discount_price = total * (Decimal('1.00') - Decimal(discount_percent) / Decimal('100'))
                    discount_price = discount_price.quantize(Decimal('0.01'))  # округление до копеек

                total = total.quantize(Decimal('0.01'))  # округление до копеек
                return render(request, 'store/order_placing.html', {
                    'cart_items': cart_items,
                    'total': total,
                    'discount_price': discount_price,
                    'discount_percent': discount_percent,
                    'delivery_zones': DELIVERY_ZONES,
                })

            else:
                messages.error(request, 'Корзина пуста')
                return redirect('cart')

        except Product.DoesNotExist:
            request.session['cart'] = {}
            messages.error(request, 'Продукт не найден, корзина очищена в целях безопасности')
            return redirect('cart')

    else:
        messages.error(request, 'Войдите в учетную запись или зарегестрируйтесь для оформления заказов')
        return redirect('signup_email')


from datetime import datetime, time

from datetime import datetime, time, timedelta

def is_within_working_hours():
    now = datetime.now()
    weekday = now.weekday()  # Пн=0, Вс=6

    if weekday < 4:  # Пн–Чт
        start, end = time(8, 0), time(22, 0)
    else:  # Пт–Вс
        start, end = time(9, 0), time(23, 0)

    # Вычитаем 20 минут из конца рабочего времени
    end_dt = datetime.combine(now.date(), end) - timedelta(minutes=20)
    end_adjusted = end_dt.time()

    return start <= now.time() <= end_adjusted


@ratelimit(key='ip', rate='6/h', method='POST', block=True)
def order_sending(request):
    if request.user.is_authenticated:

        if request.method == 'POST':
            if not is_within_working_hours():
                messages.error(request, 'Заказы можно оформлять только в рабочее время:\nПн–Чт: 8:00–22:00, Пт–Вс: 9:00–23:00.')
                return redirect('checkout')
            
            if request.user.profile.active_deliveries:
                messages.error(request, 'У Вас уже есть активный заказ, он скоро приедет!')
                return redirect('checkout')
            address = request.POST.get('address')
            delivery_area = request.POST.get('delivery_area')
            delivery_fee = Decimal(DELIVERY_ZONES.get(delivery_area, 0))
            to_door = 'door_delivery' in request.POST
            if to_door:
                delivery_fee += Decimal(50)
            user = request.user
            phone = user.profile.phone_number
            email = request.POST.get('email')
            cart = request.session.get('cart', {})
            payment_method = request.POST.get('payment_method')
            pickup = 'pickup' in request.POST
            change_from = request.POST.get('change_from') if request.POST.get('change_from') else 0

            if not cart:
                return redirect('cart')  # если корзина пуста

            order = Order.objects.create(
            user=user,
            address= address,
            phone=phone,
            comment=request.POST.get('comment'),
            cash=(payment_method == 'cash'),
            delivery_area=delivery_area,
            delivery_fee=delivery_fee,
            pickup=pickup,
            to_door= to_door,
            change_from = change_from
            )   

            order_price = 0

            try:
                # Привязка продуктов и их количества
                products_map = {str(product.id): product for product in Product.objects.filter(id__in=cart.keys())}
                order_items = []
                for product_id, product_data in cart.items():
                    product = products_map.get(product_id)
                    if not product:
                        messages.error(request, f"Продукт с ID {product_id} не существует")
                        return redirect('order_placing')

                    order_items.append(OrderItem(
                        order=order,
                        product=product,
                        quantity=product_data['quantity']
                    ))
                    order_price += product.price * product_data['quantity']

                OrderItem.objects.bulk_create(order_items)
            
            except Exception as e:
                order.delete()
                messages.error(request, f"Произошла ошибка при создании заказа, попробуйте позже.")
                return redirect('order_placing')


            promo_codes = PromoCode.objects.filter(promo__user=request.user, promo__active_usage=True, active=True,)
            if promo_codes.exists():
                UserPromoCodeUsage.objects.filter(
                    user=request.user,
                    active_usage=True,
                    promo_code__active=True
                ).update(usage_count=F('usage_count') + 1) #!!!!!!!!!!!!!!!

                discount_percent = sum(promo.discount_percent for promo in promo_codes)
                discount_price = (order_price  + delivery_fee) * (Decimal('1.00') - Decimal(discount_percent) / Decimal('100'))
                discount_price = discount_price.quantize(Decimal('0.01'))  # округление до копеек

                order.discount_price = discount_price
                order.discount_percent = discount_percent
                order.promocode_applied = True 


            order.price = order_price + delivery_fee
            order.save()


            # Очистка корзины
            request.session['cart'] = {}
            request.user.profile.active_deliveries = True
            if address:
                user.profile.address = address
            email_price =  order.discount_price if order.discount_price else order.price

            request.user.profile.save()

            if email:
                user.email = email
                send_email(email, 'Спасибо за заказ в нашем магазине "Столичный"!', f'Номер заказа - {order.id}. Сумма заказа - {email_price}₽. Более подробная информация представлена в разделе "Заказы" на нашем сайте.')
            request.user.save()

            # Перенаправление на страницу успешного оформления
            return render(request, 'store/thank_u.html')

        else:
            return redirect('order_placing')
    else:
        messages.error(request, 'Войдите в учетную запись или зарегестрийтесь для оформления заказов')
        return redirect('signup_email')


def cancel_order(request, order_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Войдите в учетную запись или зарегестрийтесь для взаимодействия с заказами')
        return redirect('signup_email')
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        messages.error(request, 'Заказ не найден')
        return redirect('checkout')
    try:
        if order.status != 'processing' and order.status != 'setting up':
            messages.error(request, 'Заказ не может быть отменен')
            return redirect('checkout')
        
        if request.user.email:
            send_email(request.user.email, 'Заказ отменен', f'Заказ No{order.id} отменен.')
        
        order.status = 'canceled'
        order.save()

        has_active_orders = Order.objects.filter(
            user=request.user
        ).exclude(
            status__in=['delivered', 'inactive', 'canceled']
        ).exists()  # Только проверка наличия (не загружает объекты)
        
        if not has_active_orders:
            request.user.profile.active_deliveries = False
            request.user.profile.save()

        messages.info(request, 'Заказ отменен, но учтите, теперь наш курьер расстроен, что не сможет порадовать Вас доставкой...')
        return redirect('checkout')
    except Exception as e:
        messages.error(request, 'Ошибка.')
        return redirect('checkout')

def user_story_response(req):
    try:
        if req.user.is_authenticated:
            if req.method == 'POST':
                content = req.POST.get('content')
                StoryResponse.objects.create(user=req.user, contnent=content)
                messages.success(req, 'Ответ отправлен! Мы все читаем 😉')
                return redirect('catalog')
        messages.error(req, 'Войдите в аккаунт перед использованием.')
        return redirect('login_email')
    except Exception as e:
        messages.error(req, 'Ошибка.')
        return redirect('catalog')

def save_story_reaction(request):
    try:
        if request.method == 'POST':
            story_image = request.POST.get('image_src')  # пусть будет ключом
            reaction = request.POST.get('reaction')

            if story_image and reaction:
                reactions = request.session.get('story_reactions', {})
                reactions[story_image] = reaction
                request.session['story_reactions'] = reactions
                return JsonResponse({'status': 'ok'})
        
        return JsonResponse({'status': 'error'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error'}, status=400)

def get_story_reaction(request):
    try:
        image_src = request.GET.get('image_src')
        reactions = request.session.get('story_reactions', {})
        return JsonResponse({'reaction': reactions.get(image_src)})
    except Exception as e:
        return JsonResponse({'status': 'error'}, status=400)

@ratelimit(key='ip', rate='10/h', method='POST', block=True)
def support(req):
    if not req.user.is_authenticated:
        messages.error(req, 'Войдите в аккаунт перед использованием.')
        return redirect('signup_email')
    if req.method == 'POST':
        try:
            content = req.POST.get('error_description')
            email = req.POST.get('email')
            SupportReport.objects.create(user=req.user, content=content, email=email)
            messages.success(req, 'Сообщение отправлено! Мы ответим в течение 24 часов.')
            return redirect('catalog')
        except Exception as e:
            messages.error(req, f'Произошла ошибка.')
            return redirect('catalog')
        
    return render(req, 'store/support.html')


@ratelimit(key='ip', rate='10/h', method='POST', block=True)
def promo(req):
    if req.user.is_authenticated:
        if req.method == 'POST':
            promocode_user = req.POST.get('promocode').lower()

            try:
                promocode_db = PromoCode.objects.get(code=promocode_user)
            except PromoCode.DoesNotExist:
                promocode_db = None

            if promocode_db:
                try:
                    promo_already_activated = UserPromoCodeUsage.objects.get(promo_code=promocode_db, user=req.user)
                except UserPromoCodeUsage.DoesNotExist:
                    promo_already_activated = None

                if promo_already_activated:
                    messages.info(req, 'Этот промокод уже был активирован Вами ранее.')
                    return render(req, 'store/promo.html')

                else:
                    UserPromoCodeUsage.objects.create(promo_code=promocode_db, user=req.user)
                    messages.success(req, 'Промокод активирован.')
                    return redirect('cart')

            else:
                messages.error(req, 'Такого промокода не существует.')
                return render(req, 'store/promo.html')
    else:
        messages.error(req, 'Подтвердите почту перед использованием.')
        return redirect('/')
    return render(req, 'store/promo.html')
 