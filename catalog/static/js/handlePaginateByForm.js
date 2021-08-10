const form = document.querySelector('.paginate-by-form');
const select = document.querySelector('#id_paginate_by');

select.addEventListener('change', () => {
    form.submit();
})