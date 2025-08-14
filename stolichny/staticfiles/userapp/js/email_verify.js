  const inputs = document.querySelectorAll('.code-input');
  const hiddenInput = document.getElementById('finalCode');
  const form = document.getElementById('codeForm');
  const resendButton = document.getElementById('resendButton');

  // Автоматический переход по инпутам и сбор финального кода
  inputs.forEach((input, idx) => {
    input.addEventListener('input', () => {
      input.value = input.value.replace(/[^0-9]/g, '');
      if (input.value && idx < inputs.length - 1) {
        inputs[idx + 1].focus();
      }
      hiddenInput.value = Array.from(inputs).map(i => i.value).join('');
    });

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Backspace' && !input.value && idx > 0) {
        inputs[idx - 1].focus();
      }
    });
  });

  // Таймер на 30 секунд
  let seconds = 30;
  let timer = setInterval(() => {
    seconds--;
    resendButton.textContent = `Отправить код ещё раз (${seconds})`;
    if (seconds <= 0) {
      clearInterval(timer);
      resendButton.disabled = false;
      resendButton.textContent = 'Отправить код ещё раз';
    }
  }, 1000);

  // Повторная отправка кода
  resendButton.addEventListener('click', () => {
    resendButton.disabled = true;
    resendButton.textContent = 'Отправка...';

    fetch("{% url 'resend_code' %}", {
      method: "POST",
      headers: {
        "X-CSRFToken": "{{ csrf_token }}",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({})
    })
    .then(response => {
      if (response.ok) {
        seconds = 30;
        resendButton.textContent = `Отправить код ещё раз (${seconds})`;
        timer = setInterval(() => {
          seconds--;
          resendButton.textContent = `Отправить код ещё раз (${seconds})`;
          if (seconds <= 0) {
            clearInterval(timer);
            resendButton.disabled = false;
            resendButton.textContent = 'Отправить код ещё раз';
          }
        }, 1000);
      } else {
        resendButton.textContent = 'Ошибка. Попробуйте снова через 5 минут.';
      }
    });
  });