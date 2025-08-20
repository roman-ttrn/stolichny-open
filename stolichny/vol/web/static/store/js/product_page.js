document.addEventListener('DOMContentLoaded', () => {
  const container = document.querySelector('.product-detail-container');
  if (!container) return;

  const pid = container.dataset.pid;
  const actionBox = container.querySelector('.action-wrapper');

  const getCSRF = () =>
    document.cookie.split(';')
      .map(c => c.trim())
      .find(c => c.startsWith('csrftoken='))
      ?.split('=')[1];

  // обновление количества в иконке корзины
  function updateCartCount(count) {
    const cartCountElement = document.getElementById('cart-count');
    if (cartCountElement) {
      cartCountElement.textContent = `${count}`;
    }
  }

  const renderControls = qty => {
    actionBox.innerHTML = '';
    if (qty > 0) {
      const dec = document.createElement('button');
      dec.className = 'btn-decrease';
      dec.dataset.pid = pid;
      dec.textContent = '−';

      const span = document.createElement('span');
      span.className = 'detail-quantity';
      span.textContent = qty;

      const inc = document.createElement('button');
      inc.className = 'btn-increase';
      inc.dataset.pid = pid;
      inc.textContent = '+';

      actionBox.append(dec, span, inc);
    } else {
      const add = document.createElement('button');
      add.className = 'btn-add';
      add.dataset.pid = pid;
      add.textContent = 'Добавить';
      actionBox.append(add);
    }
  };

  const updateCount = () => {
    fetch('/get_cart_count/')
      .then(r => r.json())
      .then(data => {
        renderControls(data.cart_items[pid]?.quantity || 0);
        updateCartCount(data.count); 
      })
      .catch(console.error);
  };

  let isThrottled = false;
  const THROTTLE_DELAY = 500; // задержка 500 мс между запросами
  
  actionBox.addEventListener('click', e => {
    if (isThrottled) return;
    isThrottled = true;
    setTimeout(() => isThrottled = false, THROTTLE_DELAY);

    const btn = e.target.closest('button[data-pid]');
    if (!btn) return;

    const id = btn.dataset.pid;
    const endpoint = btn.classList.contains('btn-decrease')
      ? '/remove_from_cart/'
      : '/add_to_cart/';

    fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': getCSRF()
      },
      body: `product_id=${encodeURIComponent(id)}`
    })
    .then(r => r.json())
    .then(updateCount)
    .catch(console.error);
  });


  updateCount();
  window.addEventListener('pageshow', updateCount);
  window.addEventListener('focus', updateCount);
});