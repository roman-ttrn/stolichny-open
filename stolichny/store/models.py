from django.db import models
from django.contrib.auth.models import User

from django.core.validators import ValidationError

class Courier(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=20, unique=True, null=False, blank=False, default='+79999999999')

    def __str__(self):
        return f"Курьер {self.first_name} {self.last_name}"

class Category(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=50)
    parent = models.ForeignKey(
        'self',                  # Ссылка на эту же модель (чтобы делать вложенность)
        blank=True,
        null=True,
        related_name='children',  # Как обращаться к подкатегориям
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    categories = models.ManyToManyField(Category, related_name='products', blank=True)
    image = models.ImageField(upload_to='products/', blank=True, default='default.png')
    protein = models.PositiveIntegerField(blank=True, null=True)
    fat = models.PositiveIntegerField(blank=True, null=True)
    carbs = models.PositiveIntegerField(blank=True, null=True)
    kkal = models.PositiveIntegerField(blank=True, null=True)
    weight = models.PositiveIntegerField(blank=True, null=True)
    weight_dependence = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('processing', 'В обработке'),
        ('setting up', 'Собираем'),
        ('shipped', 'В пути'),
        ('delivered', 'Доставлен'),
        ('inactive', 'Не активен'),
        ('canceled', 'Отменен'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    products = models.ManyToManyField(Product, through='OrderItem')
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    courier = models.ForeignKey(Courier, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    comment = models.TextField(blank=True, null=True, max_length=255)
    cash = models.BooleanField(default=False)
    promocode_applied = models.BooleanField(default=False)
    discount_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    discount_percent = models.PositiveIntegerField(default=0)
    delivery_area = models.CharField(max_length=100, blank=True, null=True)
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    pickup = models.BooleanField(default=False)
    to_door = models.BooleanField(default=False)
    corrections = models.TextField(
        blank=True,
        null=True,
        max_length=500
    )
    change_from = models.IntegerField(default=0)

    def __str__(self):
        return f"Заказ от {self.user.username} — {self.status}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} x {self.quantity} шт."
    
class StoryResponse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    contnent = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class SupportReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

DISCOUNT_TYPE_CHOICES = [
    ('delivery', 'Скидка на доставку'),
    ('cart', 'Скидка на всю корзину'),
    ('item', 'Скидка на конкретный товар'),
    ('category', 'Скидка на категорию'),
]

class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    max_usage_count = models.PositiveIntegerField(blank=True, null=True)
    min_order_price = models.PositiveIntegerField(blank=True, null=True)
    discount_percent = models.PositiveIntegerField()
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='cart')
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)

class UserPromoCodeUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    promo_code = models.ForeignKey(PromoCode, on_delete=models.CASCADE, related_name='promo')
    usage_count = models.PositiveIntegerField(default=0)
    used_at = models.DateTimeField(auto_now_add=True)
    active_usage = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Проверяем — нужно ли менять active_usage
        if self.usage_count >= self.promo_code.max_usage_count:
            self.active_usage = False

        # Сохраняем уже с актуальным значением
        super(UserPromoCodeUsage, self).save(*args, **kwargs)


    def __str__(self):
        return f"Промокод {self.promo_code.code} использован {self.usage_count} раз"

    class Meta:
        unique_together = ('user', 'promo_code')  # запретить повторное использование одним пользователем

class LoginAttempt(models.Model):
    ip = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ip} — {self.timestamp}"