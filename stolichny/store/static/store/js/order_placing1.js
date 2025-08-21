document.addEventListener('DOMContentLoaded', function () {
    const discountedBlock = document.querySelector('.discounted');
    const deliverySelect = document.getElementById('delivery_area');
    const deliveryFeeBox = document.querySelector('.total-box p');
    const totalPriceBox = document.querySelector('.total-price');
    const oldPriceBox = document.querySelector('.old-price');
    const newPriceBox = document.querySelector('.new-price');
    const addressField = document.getElementById('address');
    const pickupCheckbox = document.getElementById('pickup');
    const doorDeliveryCheckbox = document.getElementById('door_delivery');

    const submitBtn = document.getElementById('submit-btn');
    
    submitBtn.addEventListener('click', function(e) {

    });

    function safeTextUpdate(element, text) {
        if (element) {
            element.textContent = String(text);
        }
    }

    function updateDeliveryFieldsState() {
        const isPickup = pickupCheckbox.checked;
        const hasArea = deliverySelect.value !== "";

        deliverySelect.disabled = isPickup;
        addressField.disabled = isPickup;

        const shouldDisableDoorDelivery = !hasArea || isPickup;
        doorDeliveryCheckbox.disabled = shouldDisableDoorDelivery;

        if (shouldDisableDoorDelivery) {
            doorDeliveryCheckbox.checked = false; // снимаем галочку, если чекбокс недоступен
        }
    }

    function fetchUpdatedPrice() {
        const area = deliverySelect.value;
        const isPickup = pickupCheckbox.checked;
        const doorDelivery = doorDeliveryCheckbox.checked;

        // Показываем "Загрузка..." перед отправкой запроса
        safeTextUpdate(deliveryFeeBox, 'Загрузка...');
        if (totalPriceBox) safeTextUpdate(totalPriceBox, 'Загрузка...');
        if (oldPriceBox) safeTextUpdate(oldPriceBox, '');
        if (newPriceBox) safeTextUpdate(newPriceBox, '');

        const params = new URLSearchParams({
            area: area,
            pickup: isPickup,
            door_delivery: doorDelivery
        });

        fetch(`/api/get_delivery_price/?${params.toString()}&_ts=${Date.now()}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) throw new Error('Ошибка при получении данных');
            return response.json();
        })
        .then(data => {
            if (!('delivery_fee' in data) || !('final_total' in data)) {
                throw new Error('Некорректные данные с сервера');
            }

            safeTextUpdate(deliveryFeeBox, isPickup ? 'Самовывоз: бесплатно' : `Доставка: ${data.delivery_fee} ₽`);

            const hasDiscount = 'final_total' in data && data.final_total !== null && 'old_total' in data && data.old_total !== null && data.old_total > data.final_total;

            if (hasDiscount) {
                if (discountedBlock) discountedBlock.style.display = 'block';
                if (totalPriceBox) totalPriceBox.style.display = 'none';

                safeTextUpdate(oldPriceBox, `${data.old_total} ₽`);
                safeTextUpdate(newPriceBox, `${data.final_total} ₽`);

                const discountPercent = Math.round(100 - (data.final_total / data.old_total) * 100);
                const badge = document.querySelector('.discount-badge');
                if (badge) badge.textContent = `−${discountPercent}%`;

            } else {
                if (discountedBlock) discountedBlock.style.display = 'none';
                if (totalPriceBox) totalPriceBox.style.display = 'inline';

                safeTextUpdate(totalPriceBox, `${data.final_total || data.old_total} ₽`);
            }

            const hasArea = deliverySelect.value !== "";
            doorDeliveryCheckbox.disabled = !hasArea || isPickup;
        })
        .catch(error => {
            console.error('Ошибка:', error);
            alert('Ошибка при обновлении стоимости. Попробуйте позже.');
            safeTextUpdate(deliveryFeeBox, 'Ошибка');
            if (totalPriceBox) safeTextUpdate(totalPriceBox, 'Ошибка');
        });
    }

    deliverySelect.addEventListener('change', () => {
        updateDeliveryFieldsState();
        fetchUpdatedPrice();
    });

    pickupCheckbox.addEventListener('change', () => {
        updateDeliveryFieldsState();
        fetchUpdatedPrice();
    });

    doorDeliveryCheckbox.addEventListener('change', fetchUpdatedPrice);

    updateDeliveryFieldsState(); // при загрузке
});