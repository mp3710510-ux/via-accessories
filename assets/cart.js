/* ============================================================
   КОРЗИНА — общий файл для index.html, catalog.html, product.html, cart.html
   Корзина больше не всплывающая панель (плохо работала на телефоне) —
   теперь это отдельная страница cart.html. Иконка 🛒 в шапке — обычная
   ссылка на неё. Здесь остаётся вся логика: хранение в localStorage,
   счётчик на иконке, полный список на странице корзины, оформление
   заказа в Telegram.
   ============================================================ */

var CART_KEY = 'mystore_cart';
var TG_NICK = 'alinaandyyy';

function getCart() {
    try {
        var raw = localStorage.getItem(CART_KEY);
        return raw ? JSON.parse(raw) : [];
    } catch (e) { return []; }
}

function saveCart(cart) {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
}

function addToCart(item) {
    var cart = getCart();
    var found = false;
    for (var i = 0; i < cart.length; i++) {
        if (cart[i].name === item.name) {
            cart[i].qty = (cart[i].qty || 1) + 1;
            found = true;
            break;
        }
    }
    if (!found) {
        item.qty = 1;
        cart.push(item);
    }
    saveCart(cart);
    renderCartCount();
}

function removeFromCart(name) {
    var cart = getCart().filter(function (it) { return it.name !== name; });
    saveCart(cart);
    renderCartCount();
    renderCartPageIfPresent();
}

function clearCart() {
    saveCart([]);
    renderCartCount();
    renderCartPageIfPresent();
}

function cartTotals() {
    var cart = getCart();
    var totalQty = 0, totalSum = 0;
    for (var i = 0; i < cart.length; i++) {
        totalQty += cart[i].qty || 1;
        totalSum += (cart[i].priceNum || 0) * (cart[i].qty || 1);
    }
    return { qty: totalQty, sum: totalSum };
}

/* Счётчик на иконке корзины — есть на всех страницах */
function renderCartCount() {
    var countEl = document.getElementById('cartCount');
    if (!countEl) return;
    var totals = cartTotals();
    if (totals.qty > 0) {
        countEl.textContent = totals.qty;
        countEl.classList.add('show');
    } else {
        countEl.classList.remove('show');
    }
}

/* Полный список товаров — есть только на странице cart.html */
function renderCartPage() {
    var itemsEl = document.getElementById('cartPageItems');
    if (!itemsEl) return;

    var footerEl = document.getElementById('cartPageFooter');
    var totalEl = document.getElementById('cartPageTotal');
    var emptyEl = document.getElementById('cartPageEmpty');
    var cart = getCart();

    if (cart.length === 0) {
        itemsEl.innerHTML = '';
        if (footerEl) footerEl.style.display = 'none';
        if (emptyEl) emptyEl.style.display = 'block';
        return;
    }

    if (emptyEl) emptyEl.style.display = 'none';

    var html = '';
    for (var i = 0; i < cart.length; i++) {
        var it = cart[i];
        var link = it.id ? ('product.html?id=' + encodeURIComponent(it.id)) : '#';
        html += '<div class="cart-page-item">' +
            '<a href="' + link + '" class="cart-page-item-link">' +
                '<img class="cart-page-item-img" src="' + it.img + '" alt="">' +
                '<div class="cart-page-item-info">' +
                    '<div class="cart-page-item-name">' + it.name + '</div>' +
                    '<div class="cart-page-item-price">' + it.price + (it.code ? ', ' + it.code : '') + (it.qty > 1 ? ' × ' + it.qty : '') + '</div>' +
                '</div>' +
            '</a>' +
            '<button class="cart-page-item-remove" data-name="' + it.name + '" type="button">✕</button>' +
        '</div>';
    }
    itemsEl.innerHTML = html;

    if (footerEl) footerEl.style.display = 'block';
    var totals = cartTotals();
    if (totalEl) totalEl.textContent = totals.sum + ' грн';

    var removeBtns = itemsEl.querySelectorAll('.cart-page-item-remove');
    for (var i = 0; i < removeBtns.length; i++) {
        removeBtns[i].addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            removeFromCart(this.getAttribute('data-name'));
        });
    }
}

function renderCartPageIfPresent() {
    if (document.getElementById('cartPageItems')) renderCartPage();
}

function buildOrderText() {
    var cart = getCart();
    var text = 'Доброго дня! Хочу замовити:\n\n';
    var sum = 0;
    for (var i = 0; i < cart.length; i++) {
        var it = cart[i];
        text += '• ' + it.name + ' — ' + it.price;
        if (it.code) text += ', (код:' + it.code + ')';
        if (it.qty > 1) text += ' × ' + it.qty;
        text += '\n';
        sum += (it.priceNum || 0) * (it.qty || 1);
    }
    text += '\nРазом: ' + sum + ' грн';
    return text;
}

function initCartUI() {
    renderCartCount();
    renderCartPageIfPresent();

    var cartClearBtn = document.getElementById('cartClear');
    if (cartClearBtn) {
        cartClearBtn.addEventListener('click', function () { clearCart(); });
    }

    var cartCheckoutBtn = document.getElementById('cartCheckout');
    if (cartCheckoutBtn) {
        cartCheckoutBtn.addEventListener('click', function (e) {
            e.preventDefault();
            var cart = getCart();
            if (cart.length === 0) return;
            window.open('https://t.me/' + TG_NICK + '?text=' + encodeURIComponent(buildOrderText()), '_blank');
        });
    }
}

initCartUI();
