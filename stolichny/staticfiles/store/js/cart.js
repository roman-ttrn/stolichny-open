   function getCSRFToken() {
        return document.querySelector('#csrf-form input[name="csrfmiddlewaretoken"]').value;
    }

    function updateCartItem(productId, quantity, cartItemCount) {
        const item = document.querySelector(`.cart-item[data-id="${productId}"]`);
        if (!item) return;

        if (quantity > 0) {
            const quantitySpan = item.querySelector('.quantity');
            if (quantitySpan) quantitySpan.textContent = quantity;
        } else {
            item.remove();
        }
    
        if (cartItemCount === 0) {
            document.querySelector('.cart-container').innerHTML = '<h2>Корзина</h2>{% if user_promos %}<div class="active-promos"><h4>Ваши активные акции:</h4><ul>{% for promo in user_promos %}<li class="promo-item">{{ promo.description|default:"Без описания" }}</li>{% endfor %}</ul></div>{% endif %} <p class="empty-cart">Корзина пуста</p>';
        }
    }
    

    function updateCartCount(count) {
        const cartCountElement = document.getElementById('cart-count');
        if (cartCountElement) {
            cartCountElement.textContent = `${count}`;
        }
    }

    function updatePriceCount(price, discountPrice = null, discountPercent = null) {
        const generalPrice = document.getElementById('gen-price');
        if (!generalPrice) return;

        // Очищаем содержимое контейнера
        generalPrice.innerHTML = '';

        if (discountPrice && discountPercent) {
            const container = document.createElement('div');
            container.classList.add('discounted');

            const oldPrice = document.createElement('span');
            oldPrice.classList.add('old-price');
            oldPrice.textContent = `${price} ₽`;

            const newPrice = document.createElement('span');
            newPrice.classList.add('new-price');
            newPrice.textContent = `${discountPrice} ₽`;

            const discountBadge = document.createElement('span');
            discountBadge.classList.add('discount-badge');
            discountBadge.textContent = `−${discountPercent}%`;

            container.appendChild(oldPrice);
            container.appendChild(newPrice);
            container.appendChild(discountBadge);

            generalPrice.appendChild(container);
        } else {
            const heading = document.createElement('h3');
            heading.textContent = 'К оплате: ';

            const boldPrice = document.createElement('b');
            boldPrice.textContent = `${price} ₽`;

            heading.appendChild(boldPrice);
            generalPrice.appendChild(heading);
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        let isThrottled = false;
        const THROTTLE_DELAY = 500; // задержка 500 мс между запросами
        document.body.addEventListener('click', (e) => {
            if (isThrottled) return;
            isThrottled = true
            setTimeout(() => isThrottled = false, THROTTLE_DELAY)
            
            const button = e.target;
            const productId = button.dataset.id;
            if (!productId) return;

            const csrfToken = getCSRFToken();

            const endpoint = button.classList.contains('decrease') ? '/remove_from_cart/' : '/add_to_cart/';
            fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body: `product_id=${encodeURIComponent(productId)}`
            })
            .then(res => {
                if (!res.ok) throw new Error("Ошибка ответа сервера");
                return res.json();
            })
            .then(data => {
                updateCartItem(productId, data.new_quantity, data.cart_item_count);
                updateCartCount(data.cart_item_count);
                updatePriceCount(data.price, data.discount_price, data.discount_percent);
            })
            .catch(err => {
                alert('Ошибка при изменении количества товара');
                console.error(err);
            });
        });
    });

  document.addEventListener("DOMContentLoaded", function () {
    const button = document.querySelector(".checkout-btn");
    const storageKey = "checkoutLoadCount";

    // Получаем количество загрузок
    let loadCount = parseInt(localStorage.getItem(storageKey)) || 0;
    loadCount += 1;

    // Сохраняем новое значение
    localStorage.setItem(storageKey, loadCount);

    // Каждая пятая загрузка — свечение
    if ((loadCount % 3 === 0 || loadCount === 1) && button) {
      button.classList.add("glow");

      // Убираем класс после анимации (3 секунды)
      setTimeout(() => {
        button.classList.remove("glow");
      }, 3000);
    }
  });
