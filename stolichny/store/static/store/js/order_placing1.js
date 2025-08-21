// optimized-delivery.js — максимально оптимизированный скрипт для обновления стоимости доставки
(function () {
  'use strict';

  const DEBUG = false; // включи для логов

  function log(...args) { if (DEBUG) console.debug(...args); }

  // ==== КЭШ ОБЪЕКТОВ DOM (только один раз!) ====
  const deliverySelect = document.getElementById('delivery_area');
  const pickupCheckbox = document.getElementById('pickup');
  const doorDeliveryCheckbox = document.getElementById('door_delivery');
  const deliveryFeeBox = document.querySelector('.total-box p');
  const totalPriceBox = document.querySelector('.total-price');
  const discountedBlock = document.querySelector('.discounted');
  const oldPriceBox = document.querySelector('.old-price');
  const newPriceBox = document.querySelector('.new-price');
  const discountBadge = document.querySelector('.discount-badge');

  if (!deliverySelect || !pickupCheckbox || !doorDeliveryCheckbox) {
    log('Delivery UI missing — aborting optimized script.');
    return;
  }

  // ==== УТИЛИТЫ ====
  function updateTextIfChanged(el, text) {
    if (!el) return;
    text = String(text);
    if (el.textContent !== text) el.textContent = text;
  }

  function setDisplayIfNeeded(el, show, displayValue = 'block') {
    if (!el) return;
    const cur = window.getComputedStyle(el).display;
    const want = show ? displayValue : 'none';
    if (cur !== want) el.style.display = want;
  }

  // ==== BATCHED DOM UPDATES через requestAnimationFrame ====
  const pending = { deliveryFee: null, total: null, old: null, neu: null, discountBadge: null, discountedVisible: null, totalVisible: null, error: null };
  let rafScheduled = false;
  function scheduleFlush() {
    if (rafScheduled) return;
    rafScheduled = true;
    requestAnimationFrame(() => {
      rafScheduled = false;
      if (pending.error !== null) {
        // показываем текст ошибки там, где нужно
        updateTextIfChanged(deliveryFeeBox, pending.error.deliveryFee || 'Ошибка');
        if (totalPriceBox) updateTextIfChanged(totalPriceBox, pending.error.total || 'Ошибка');
      } else {
        if (pending.deliveryFee !== null) updateTextIfChanged(deliveryFeeBox, pending.deliveryFee);
        if (pending.total !== null && totalPriceBox) updateTextIfChanged(totalPriceBox, pending.total);
        if (pending.old !== null && oldPriceBox) updateTextIfChanged(oldPriceBox, pending.old);
        if (pending.neu !== null && newPriceBox) updateTextIfChanged(newPriceBox, pending.neu);
        if (pending.discountBadge !== null && discountBadge) updateTextIfChanged(discountBadge, pending.discountBadge);
        if (pending.discountedVisible !== null) setDisplayIfNeeded(discountedBlock, pending.discountedVisible, 'flex');
        if (pending.totalVisible !== null) setDisplayIfNeeded(totalPriceBox, pending.totalVisible, 'inline');
      }
      // сбрасываем
      for (const k of Object.keys(pending)) pending[k] = null;
    });
  }

  // ==== AbortController для отмены предыдущих запросов + таймаут ====
  let activeController = null;
  const FETCH_TIMEOUT = 8000; // ms

  // ==== Debounce: сглаживаем быстрые изменения (пользователь может быстро переключать) ====
  function debounce(fn, wait) {
    let t = null;
    return function (...args) {
      if (t) clearTimeout(t);
      t = setTimeout(() => {
        t = null;
        fn.apply(this, args);
      }, wait);
    };
  }

  // ==== Валидная сериализация параметров ====
  function booleanToString(b) { return b ? 'true' : 'false'; }

  // ==== Основная логика запроса + обработка ответа ====
  async function doFetchPrice() {
    // Снимаем лишние вызовы, если не видно нужных элементов
    const area = deliverySelect.value;
    const isPickup = pickupCheckbox.checked;
    const doorDelivery = doorDeliveryCheckbox.checked;

    log('doFetchPrice', { area, isPickup, doorDelivery });

    // показываем "загрузка" мгновенно (batch)
    pending.deliveryFee = 'Загрузка...';
    pending.total = 'Загрузка...';
    pending.old = '';
    pending.neu = '';
    pending.discountedVisible = false;
    pending.totalVisible = true;
    scheduleFlush();

    // abort previous
    if (activeController) {
      try { activeController.abort(); } catch (e) { /* ignore */ }
      activeController = null;
    }

    activeController = new AbortController();
    const signal = activeController.signal;
    // set timeout to auto-abort
    const timeoutId = setTimeout(() => {
      if (activeController) {
        try { activeController.abort(); } catch (e) {}
      }
    }, FETCH_TIMEOUT);

    // build query
    const params = new URLSearchParams({
      area: area || '',
      pickup: booleanToString(isPickup),
      door_delivery: booleanToString(doorDelivery),
      _ts: String(Date.now()) // anti-cache
    });

    try {
      const res = await fetch(`/api/get_delivery_price/?${params.toString()}`, {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        signal
      });

      clearTimeout(timeoutId);
      activeController = null;

      if (!res.ok) {
        // try to get text for debug in non-DEBUG mode
        let text = 'Ошибка при получении данных';
        try { text = await res.text(); } catch (e) { /* ignore */ }
        log('Fetch bad response:', res.status, text);
        pending.error = { deliveryFee: 'Ошибка', total: 'Ошибка' };
        scheduleFlush();
        return;
      }

      const data = await res.json();
      // Validate data:
      if (!('delivery_fee' in data) || !('final_total' in data) || !('old_total' in data)) {
        log('Invalid payload', data);
        pending.error = { deliveryFee: 'Ошибка', total: 'Ошибка' };
        scheduleFlush();
        return;
      }

      // Normalize numbers (server может присылать строки)
      const oldTotal = Number(data.old_total) || 0;
      const finalTotal = Number(data.final_total) || 0;
      const deliveryFee = (isPickup ? 'Самовывоз: бесплатно' : (`Доставка: ${data.delivery_fee} ₽`));

      // decide discount presence
      const hasDiscount = (oldTotal > 0 && finalTotal < oldTotal);

      if (hasDiscount) {
        pending.discountedVisible = true;
        pending.totalVisible = false;
        pending.old = `${oldTotal} ₽`;
        pending.neu = `${finalTotal} ₽`;
        // compute percent safely
        const discountPercent = Math.round(100 - (finalTotal / oldTotal) * 100);
        pending.discountBadge = `−${discountPercent}%`;
      } else {
        pending.discountedVisible = false;
        pending.totalVisible = true;
        pending.total = `${(finalTotal || oldTotal)} ₽`;
      }

      pending.deliveryFee = deliveryFee;
      scheduleFlush();

    } catch (err) {
      clearTimeout(timeoutId);
      activeController = null;
      if (err.name === 'AbortError') {
        log('Fetch aborted or timed out');
        return; // silent abort — new request likely already scheduled
      }
      console.error('Fetch error', err);
      pending.error = { deliveryFee: 'Ошибка', total: 'Ошибка' };
      scheduleFlush();
    }
  }

  // Debounced public function
  const fetchUpdatedPrice = debounce(doFetchPrice, 180);

  // ==== UI state logic (disable fields etc.) ====
  function updateDeliveryFieldsState() {
    const isPickup = pickupCheckbox.checked;
    const hasArea = deliverySelect.value !== '';

    deliverySelect.disabled = isPickup;
    const addressField = document.getElementById('address');
    if (addressField) addressField.disabled = isPickup;

    const shouldDisableDoorDelivery = !hasArea || isPickup;
    doorDeliveryCheckbox.disabled = shouldDisableDoorDelivery;
    if (shouldDisableDoorDelivery) doorDeliveryCheckbox.checked = false;
  }

  // ==== Event listeners (minimal and efficient) ====
  deliverySelect.addEventListener('change', () => {
    updateDeliveryFieldsState();
    fetchUpdatedPrice();
  });

  pickupCheckbox.addEventListener('change', () => {
    updateDeliveryFieldsState();
    fetchUpdatedPrice();
  });

  doorDeliveryCheckbox.addEventListener('change', fetchUpdatedPrice);

  // initial state on load
  updateDeliveryFieldsState();

  // run immediate initial calculation but debounced (so batching still works)
  fetchUpdatedPrice();

  // expose for debug/tests
  if (DEBUG) window.__delivery = { fetchUpdatedPrice, doFetchPrice };

})();
