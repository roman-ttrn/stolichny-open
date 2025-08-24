  // --- При загрузке: если страница сбросила active на "Все", подправляем URL под первый слаг ---
document.addEventListener('DOMContentLoaded', () => {
  const firstBtn = document.querySelector('.subcategory-btn'); // первая кнопка гарантированно "Все"
  if (!firstBtn) return;

  const slug = firstBtn.dataset.slug;
  if (!slug) return; // если data-slug нет — ничего не делаем

  // простая нормализация: гарантируем ровно один слеш в конце
  function norm(path) {
    if (!path) return '/';
    return path.replace(/\/+$/, '') + '/';
  }

  const desiredPath = norm(`/catalog/${encodeURIComponent(slug)}/`);
  const currentPath = norm(window.location.pathname);

  // Если текущий путь отличается — заменим URL (без перезагрузки)
  if (currentPath !== desiredPath) {
    const newUrl = desiredPath + window.location.search + window.location.hash;
    history.replaceState(null, '', newUrl);
  }

  // Установим currentCatalogPath и active на первой кнопке, чтобы остальной код работал корректно
  currentCatalogPath = desiredPath;
  document.querySelectorAll('.subcategory-btn').forEach(b => b.classList.remove('active'));
  firstBtn.classList.add('active');
});

  let currentCatalogPath = window.location.pathname.replace(/\/+$/, '') + '/';
  const THROTTLE_DELAY = 500; // задержка 500 мс между запросами
  // 1) Получаем CSRF‑токен из куки
  function getCSRFToken() {
    const name = 'csrftoken';
    return document.cookie.split(';')
      .map(c => c.trim())
      .find(c => c.startsWith(name + '='))
      ?.split('=')[1] || '';
  }

  // 2) Обновляем число в иконке корзины
  function updateCartCount(count) {
    const el = document.getElementById('cart-count');
    if (el) el.textContent = `${count}`;
  }

  // 3) Обновляем конкретную карточку товара
    function updateUI(productId, quantity) {
    const card = document.querySelector(`.product-card[data-id="${CSS.escape(productId)}"]`);
    if (!card) return;

    const wrapper = card.querySelector('.action-wrapper');
    if (!wrapper) return;

    // Очищаем старое содержимое
    wrapper.innerHTML = '';

    if (quantity > 0) {
      const controls = document.createElement('div');
      controls.classList.add('cart-controls');

      const decreaseBtn = document.createElement('button');
      decreaseBtn.classList.add('decrease');
      decreaseBtn.setAttribute('data-id', productId);
      decreaseBtn.textContent = '−';

      const quantitySpan = document.createElement('span');
      quantitySpan.classList.add('quantity');
      quantitySpan.textContent = quantity;

      const increaseBtn = document.createElement('button');
      increaseBtn.classList.add('increase');
      increaseBtn.setAttribute('data-id', productId);
      increaseBtn.textContent = '+';

      controls.appendChild(decreaseBtn);
      controls.appendChild(quantitySpan);
      controls.appendChild(increaseBtn);

      wrapper.appendChild(controls);
    } else {
      const addBtn = document.createElement('button');
      addBtn.classList.add('add-to-cart');
      addBtn.setAttribute('data-id', productId);
      addBtn.textContent = '+';

      wrapper.appendChild(addBtn);
    }
  }


  // 4) Получаем состояние корзины с сервера и обновляем всё
  function checkCartUpdates() {
    fetch('/get_cart_count/', {
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin'
    })
      .then(res => res.json())
      .then(data => {
        // отладка: console.log('cart data:', data);
        updateCartCount(data.count);
        document.querySelectorAll('.product-card').forEach(card => {
          const id = card.dataset.id;
          const qty = data.cart_items[id]?.quantity || 0;
          updateUI(id, qty);
        });
      })
      .catch(err => console.error('Ошибка при checkCartUpdates:', err));
  }

  // 5) Отправляем add/remove запрос на сервер
  function sendCartUpdate(endpoint, productId) {
    if (isThrottled) return;
    isThrottled = true;
    setTimeout(() => isThrottled = false, THROTTLE_DELAY);

    const body = `product_id=${encodeURIComponent(productId)}`;
    fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': getCSRFToken()
      },
      credentials: 'same-origin',
      body: body
    })
      .then(res => res.json())
      .then(data => {
        updateCartCount(data.cart_item_count);
        updateUI(productId, data.new_quantity);
      })
      .catch(err => console.error('Ошибка при sendCartUpdate:', err));
  }

  // 6) Глобальный слушатель кликов по + / − / добавить
  document.body.addEventListener('click', e => {
    const btn = e.target.closest('button[data-id]');
    if (!btn) return;
    const pid = btn.dataset.id;

    if (btn.classList.contains('decrease')) {
      sendCartUpdate('/remove_from_cart/', pid);
    } else if (btn.classList.contains('increase')) {
      sendCartUpdate('/add_to_cart/', pid);
    } else if (btn.classList.contains('add-to-cart')) {
      // здесь можно вставить логику для весозависимых продуктов:
      // if (card.dataset.weightDependence === 'true') { openWeightModal(...) }
      sendCartUpdate('/add_to_cart/', pid);
    }
  });

  // 7) Вызываем при загрузке, возврате на страницу и при фокусе вкладки
  document.addEventListener('DOMContentLoaded', checkCartUpdates);
  window.addEventListener('pageshow', checkCartUpdates);
  window.addEventListener('focus', checkCartUpdates);


  document.querySelectorAll('.story-card').forEach(card => {
    card.addEventListener('click', () => {
      const modal = document.getElementById('instaStoryModal');
      const img = modal.querySelector('img');
      const categoryBtn = modal.querySelector('a')

      const imageSrc = card.querySelector('img').src;
      const storyName = card.querySelector('span').textContent
      img.src = imageSrc;

      const storyLink = card.dataset.link; // Получаем ссылку из data-атрибута

      if (storyLink){
        categoryBtn.href = storyLink
        categoryBtn.classList.remove('hidden');
      } else {
        categoryBtn.classList.add('hidden');
      }
      modal.classList.remove('hidden');

      // УСТАНАВЛИВАЕМ УНИКАЛЬНЫЙ ТЕКСТ
      const caption = card.dataset.caption || '';
      const captionContainer = modal.querySelector('.insta-caption');
      captionContainer.textContent = caption;

      // Запрашиваем сохранённую реакцию
      fetch(`/get_story_reaction/?image_src=${encodeURIComponent(imageSrc)}`)
        .then(res => res.json())
        .then(data => {
          const saved = document.getElementById('saved-reaction');
          if (data.reaction) {
            saved.textContent = data.reaction;
          } else {
            saved.textContent = '';
          }
        });
    });
  });


  document.querySelector('.insta-close').addEventListener('click', () => {
    document.getElementById('instaStoryModal').classList.add('hidden');
  });

  const input = document.getElementById('insta-reply-input');
  const reactions = document.getElementById('emoji-reactions');
  const flash = document.getElementById('emoji-flash');

  // Показываем реакции при фокусе
  input.addEventListener('focus', () => {
    reactions.classList.remove('hidden');
  });

  // Скрываем при потере фокуса 
  input.addEventListener('blur', () => {
    setTimeout(() => reactions.classList.add('hidden'), 200);
  });

  // Клик по эмодзи
  reactions.querySelectorAll('.emoji').forEach(emoji => {
    emoji.addEventListener('click', () => {
      const symbol = emoji.textContent;
      flash.textContent = symbol;

      // Запуск анимации появления
      flash.classList.add('enter');

      // Сохраняем реакцию на сервере
      const imageSrc = document.getElementById('insta-story-bg').src;
      fetch('/save_story_reaction/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCSRFToken()
        },
        body: `image_src=${encodeURIComponent(imageSrc)}&reaction=${encodeURIComponent(symbol)}`
      });

      // Показываем реакцию в UI
      const saved = document.getElementById('saved-reaction');
      saved.textContent = symbol;

      // Через 1 секунду запускаем анимацию исчезания
      setTimeout(() => {
        flash.classList.remove('enter');
        flash.classList.add('exit');
      }, 1000);

      // Через 1.4 секунды убираем классы (чтобы элемент можно было использовать снова)
      setTimeout(() => {
        flash.classList.remove('exit');
      }, 1400);
    });
  });


 
  let loading = false;


function loadNextPage() {
  if (loading || !hasNextPage) return;
  loading = true;

  // увеличиваем страницу — дальше будет запрошена следующая страница
  page += 1;

  // Формируем URL: currentCatalogPath уже содержит корректный путь вида "/catalog/slug/".
  const url = `${currentCatalogPath}?page=${page}`;

  fetch(url, {
    headers: { 'X-Requested-With': 'XMLHttpRequest' }
  })
    .then(res => {
      if (!res.ok) throw new Error('Network response was not ok');
      return res.json();
    })
    .then(data => {
      document.getElementById('product-grid').insertAdjacentHTML('beforeend', data.html);
      hasNextPage = data.has_next;
      loading = false;
    })
    .catch(err => {
      console.error('Ошибка подгрузки:', err);
      loading = false;
    });
}

  let isThrottled = false;
  // Отслеживаем скролл
  window.addEventListener('scroll', () => {
    if (isThrottled) return;
    const scrollBottom = window.innerHeight + window.scrollY >= document.body.offsetHeight - 300;
    if (scrollBottom) {
      loadNextPage();
      isThrottled = true; // Блокируем новые вызовы
      setTimeout(() => isThrottled = false, THROTTLE_DELAY);
    }
  });

  document.querySelectorAll('.subcategory-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const slug = btn.dataset.slug;

    // UI: переключаем active
    document.querySelectorAll('.subcategory-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    // Формируем новый базовый путь для запросов.
    currentCatalogPath = `/catalog/${encodeURIComponent(slug)}/`;

    // AJAX-запрос на подкатегорию (возвращает HTML и has_next)
    fetch(`${currentCatalogPath}?page=1`, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(res => {
        if (!res.ok) throw new Error('Network response was not ok');
        return res.json();
      })
      .then(data => {
        document.getElementById('product-grid').innerHTML = data.html;
        page = 1; // мы сейчас показали страницу 1
        hasNextPage = data.has_next;

        // Обновим историю браузера — полезно для бэка/кармашков
        if (history && history.pushState) {
          history.pushState(null, '', currentCatalogPath);
        }
      })
      .catch(err => console.error('Ошибка подкатегории:', err));
  });
});
