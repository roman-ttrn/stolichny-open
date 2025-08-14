from django import template

register = template.Library() #Создаёт объект Library, который регистрирует кастомные фильтры/теги для Django

@register.filter # make this function a filter
def get_item(dictionary, key):
    quantity = dictionary.get(str(key))
    if quantity is None:
        return quantity
    return quantity['quantity']

