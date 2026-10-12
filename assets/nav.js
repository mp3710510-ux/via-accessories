/* ============================================================
   NAV.JS — общий для всех страниц.
   На компьютере меню "Каталог" открывается по наведению мышкой
   (это уже было в CSS). На телефоне наводить нечем — там меню
   открывается и закрывается по тапу. Этот файл добавляет именно
   тап-поведение, не трогая работу на компьютере.
   ============================================================ */

(function () {
    var navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(function (item) {
        item.addEventListener('click', function (e) {
            // клик по самой ссылке внутри дропдауна — даём перейти по ссылке как обычно
            if (e.target.tagName === 'A') return;

            e.preventDefault();
            var isOpen = item.classList.contains('open');
            navItems.forEach(function (i) { i.classList.remove('open'); });
            if (!isOpen) item.classList.add('open');
        });
    });

    document.addEventListener('click', function (e) {
        navItems.forEach(function (item) {
            if (!item.contains(e.target)) item.classList.remove('open');
        });
    });
})();
