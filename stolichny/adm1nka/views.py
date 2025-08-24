from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth import login as auth_login

from store.models import Order, Courier
from .models import LoginAttempt
from .forms import ProductForm
from store.models import Product


from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.contrib import messages

@csrf_protect
def login_view(request):
    error = ""

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        ip = get_client_ip(request)

        # Проверка блокировки
        if is_ip_blocked(ip):
            return HttpResponseForbidden("Вы заблокированы на неделю из-за 10 неудачных попыток входа.")

        try:
            user = User.objects.get(email=email, first_name=first_name, last_name=last_name)
        except User.DoesNotExist:
            user = None

        # Сначала аутентификация, потом проверка прав
        auth_user = authenticate(request, username=user.username, password=password)
        if auth_user is not None:  # Явная проверка на None
            if not auth_user.is_superuser:
                LoginAttempt.objects.create(ip=ip)
                return redirect('/')
            
            reset_login_attempts(ip)
            auth_login(request, auth_user) 
            return redirect('admin_dashboard')
        else:
            LoginAttempt.objects.create(ip=ip)
            return render(request, 'adm1nka/login.html', {'error': "Неверные данные"})

    return render(request, 'adm1nka/login.html', {'error': error})


def admin_dashboard(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('/')
    
    show_inactive = request.GET.get('show_inactive')
    couriers = Courier.objects.all()

    if show_inactive:
        print('show_inactive')
        orders = Order.objects.filter(status__in=('inactive', 'canceled', 'delivered')).order_by('-created_at')
    else:
        print('show_active')
        orders = Order.objects.exclude(status__in=('inactive', 'canceled', 'delivered')).order_by('-created_at')

    try:
        page_number = int(request.GET.get('page', 1))
    except (TypeError, ValueError):
        page_number = 1

    paginator = Paginator(orders, 30)
    orders_obj = paginator.get_page(page_number)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        print('ajax')
        html = render_to_string('adm1nka/includes/order_card.html',
                                {'orders': orders_obj, 'couriers': couriers, 'show_inactive': show_inactive, 'has_next': orders_obj.has_next()})
        
        return JsonResponse({'html': html, 'has_next': orders_obj.has_next(), 'show_inactive': show_inactive})
    
    return render(request, 'adm1nka/dashboard.html', {'orders': orders_obj, 'couriers': couriers, 'show_inactive': show_inactive, 'has_next': orders_obj.has_next()})


@require_POST
def update_order_status(request, order_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('/')

    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status')
    new_courier_id = request.POST.get('courier_id')
    corrections = request.POST.get('corrections')

    if new_status:
        order.status = new_status
    if new_courier_id:
        order.courier = get_object_or_404(Courier, id=new_courier_id)

    if corrections:
        order.corrections = corrections

    order.save()

    user = order.user  # или конкретный пользователь
    has_active_orders = Order.objects.filter(
        user=user
    ).exclude(
        status__in=['canceled', 'delivered', 'inactive']
    ).exists()

    if has_active_orders:
        user.profile.active_deliveries = True
        user.profile.save()
    else:
        user.profile.active_deliveries = False
        user.profile.save()

    return redirect('admin_dashboard')


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

def is_ip_blocked(ip):
    week_ago = timezone.now() - timedelta(days=7)
    recent_attempts = LoginAttempt.objects.filter(ip=ip, timestamp__gte=week_ago)
    return recent_attempts.count() >= 10

def reset_login_attempts(ip):
    LoginAttempt.objects.filter(ip=ip).delete()

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

@login_required
def product_create_or_edit(request, product_id=None):
    # только staff или админ
    if not request.user.is_staff:
        return redirect('/')

    product = None
    if product_id:
        product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        # ВАЖНО: если product существует — передаём instance=product
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            # безопасное сохранение: сначала commit=False чтобы можно было управлять полями
            obj = form.save(commit=False)

            # --- сохранение картинки: если редактирование и пользователь НЕ загрузил новую картинку
            # и не поставил чекбокс очистки, то оставляем старую картинку
            if product is not None:
                # form.cleaned_data['image'] будет:
                # - File объект при загрузке нового файла
                # - False/None если чекбокс 'очистить' установлен (ClearableFileInput)
                # - None если ничего не трогали — тогда нужно сохранить старую
                new_image = form.cleaned_data.get('image')
                clear_flag = f"{form.add_prefix('image')}-clear" in request.POST
                # если нет нового файла и флага очистки — сохраняем старую картинку
                if not new_image and not clear_flag:
                    obj.image = product.image
            
            # любые дополнительные поля (владелец и т.д.) можно установить здесь
            obj.save()
            form.save_m2m()

            messages.success(request, f'Продукт \"{obj.name}\" успешно сохранен!')
            return redirect('/')
        else:
            messages.error(request, 'Форма содержит ошибки, исправьте их.')
    else:
        # GET: instance достаточно
        form = ProductForm(instance=product)

    return render(request, 'adm1nka/product_form.html', {
        'form': form,
        'product': product,   # передаём сам объект (или None) — удобно в шаблоне
    })


def product_delete(req, product_id=None):
    if not req.user.is_authenticated or not req.user.is_staff or product_id is None:
        return redirect('/')
    
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(req, f'Продукт "{product.name}" успешно удален!')
    return redirect('/')