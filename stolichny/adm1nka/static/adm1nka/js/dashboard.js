function updateShowInactiveButton() {
        const button = document.querySelector('.show-inactive-btn');
        if (button) {
            currentShowInactive = button.getAttribute('data-show-inactive') === 'true';
        }
    }

    let loading = false;
 

    function loadNextPage(){
        if (loading || !hasNextPage) return;
        console.log('ajax')
        loading = true;
        page += 1
        updateShowInactiveButton();

        fetch(`${window.location.pathname}?page=${page}&show_inactive=${currentShowInactive}`,{
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
            .then(res => res.json())
            .then(data => {
                document.getElementById('order-container').insertAdjacentHTML('beforeend', data.html)
                hasNextPage = data.has_next
                loading = false
            })
            .catch(err => {
            console.error('Ошибка подгрузки:', err);
            loading = false;
        });
    }


    window.addEventListener('scroll', () => {
        const scrollBottom = window.innerHeight + window.scrollY >= document.body.offsetHeight - 300;
        if (scrollBottom) {
            loadNextPage()
        }
    })