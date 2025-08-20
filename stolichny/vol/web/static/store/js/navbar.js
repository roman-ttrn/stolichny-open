const searchInput = document.querySelector(".search-input");
const suggestionBox = document.getElementById("product-suggestions");
let debounceTimeout = null;

searchInput.addEventListener("input", function() {
    clearTimeout(debounceTimeout);
    const query = searchInput.value.trim();
    
    if (query.length === 0) {
    suggestionBox.classList.remove("active");
    suggestionBox.innerHTML = "";
    return;
    }

    debounceTimeout = setTimeout(() => {
    fetch(`/api/search-products?q=${encodeURIComponent(query)}`)
        .then(res => res.json())
        .then(data => {
            suggestionBox.innerHTML = "";

            if (data.result.length === 0) {
            const li = document.createElement("li");
            const bold = document.createElement("b");
            bold.textContent = "Ничего не найдено";
            li.appendChild(bold);
            suggestionBox.appendChild(li);
            } else {
            data.result.forEach(product => {
                const li = document.createElement("li");

                const span = document.createElement("span");
                span.classList.add("suggestion-text");

                const bold = document.createElement("b");
                bold.textContent = product.name;
                span.appendChild(bold);

                const link = document.createElement("a");
                link.href = `/product_page/${encodeURIComponent(product.id)}/`;
                link.textContent = "→ К товару";

                li.appendChild(span);
                li.appendChild(link);
                suggestionBox.appendChild(li);
            });
            }

            suggestionBox.classList.add("active");
        });
    }, 300);
});

const toggleBtn = document.querySelector('.menu-toggle');
const sidebar   = document.querySelector('.sidebar');

toggleBtn.addEventListener('click', () => {
    const open = sidebar.classList.toggle('open');
    sidebar.setAttribute('aria-hidden', !open);
    document.body.style.overflow = open ? 'hidden' : '';
});

// Закрытие по клику вне панели
document.addEventListener('click', e => {
    if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
    sidebar.classList.remove('open');
    sidebar.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    }
});