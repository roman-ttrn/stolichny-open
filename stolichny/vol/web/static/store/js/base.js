document.addEventListener('DOMContentLoaded', function() {
        // Закрытие уведомлений по клику
        document.querySelectorAll('.notification-close').forEach(closeBtn => {
            closeBtn.addEventListener('click', function() {
                const notification = this.closest('.notification');
                notification.style.animation = 'fadeOut 0.4s forwards';
                setTimeout(() => notification.remove(), 400);
            });
        });
        
        // Автоматическое закрытие через 5 секунд
        document.querySelectorAll('.notification').forEach(notification => {
            setTimeout(() => {
                notification.style.animation = 'fadeOut 0.4s forwards';
                setTimeout(() => notification.remove(), 400);
            }, 5000);
        });
    });


    function checkCartUpdates() {
        fetch('/get_cart_count/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            updateCartCount(data.count);
        })

        .catch(error => console.error('Ошибка при проверке корзины:', error));
        }

        // Проверяем корзину при загрузке страницы
        document.addEventListener('DOMContentLoaded', function() {
            checkCartUpdates();
        });

        // Также проверяем корзину при возвращении на страницу
        window.addEventListener('pageshow', function(event) {
            if (event.persisted) {
                checkCartUpdates();
            }
        });

        function getCSRFToken() {
        const name = 'csrftoken';
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const c = cookies[i].trim();
            if (c.startsWith(name + '=')) {
                return decodeURIComponent(c.substring(name.length + 1));
            }
        }
        return null;
        }

        function updateCartCount(count) {
            const cartCountElement = document.getElementById('cart-count');
            if (cartCountElement) {
                cartCountElement.textContent = `${count}`;
            }
        }