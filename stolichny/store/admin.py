from django.contrib import admin
from .models import *

admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(StoryResponse)
admin.site.register(Courier)
admin.site.register(Category)
admin.site.register(UserPromoCodeUsage)
admin.site.register(PromoCode)