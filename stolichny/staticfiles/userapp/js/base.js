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