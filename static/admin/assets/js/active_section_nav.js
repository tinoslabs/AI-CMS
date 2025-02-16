document.addEventListener("DOMContentLoaded", function () {
    const headerText = document.querySelector('.page-header')?.innerText.trim();
    
    document.querySelectorAll('.menu-item a').forEach(item => {
        if (item.innerText.trim() === headerText) {
            item.parentElement.classList.add('active');
        }
    });
});
