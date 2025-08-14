def cart_item_count(request):
    cart = request.session.get('cart', {})
    cart_item_count = 0
    for id, item_data in cart.items():
        cart_item_count += item_data['quantity']
        print(cart_item_count)
    return {'cart_item_count': cart_item_count}
