/* ============================================================
   ОФОРМЛЕННЯ ЗАМОВЛЕННЯ — модальна форма (ім'я + телефон).
   Заявка йде на Cloudflare Worker (ORDER_ENDPOINT з assets/config.js),
   який пересилає її в Telegram-групу. Токена бота тут немає.
   Підключається на cart.html та сторінках товарів.
   ============================================================ */
(function () {
    var SITE = 'https://via-accessories.com.ua';
    var TG_LINK = 'https://t.me/via_manager';

    var overlay, form, nameInput, phoneInput, trapInput, errEl, submitBtn, bodyEl, successEl, formWrap;
    var currentItems = [], onSuccess = null, lastFocus = null, sending = false;

    function build() {
        overlay = document.createElement('div');
        overlay.className = 'order-overlay';
        overlay.hidden = true;
        overlay.innerHTML =
            '<div class="order-modal" role="dialog" aria-modal="true" aria-labelledby="orderTitle" tabindex="-1">' +
                '<button type="button" class="order-close" aria-label="Закрити">✕</button>' +
                '<div class="order-form-wrap">' +
                    '<h2 class="order-title" id="orderTitle">Оформлення замовлення</h2>' +
                    '<form class="order-form" novalidate>' +
                        '<label class="order-label" for="orderName">Ваше ім’я</label>' +
                        '<input class="order-input" id="orderName" name="name" type="text" autocomplete="name" maxlength="60" required>' +
                        '<label class="order-label" for="orderPhone">Номер телефону</label>' +
                        '<input class="order-input" id="orderPhone" name="phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="+380..." maxlength="24" required>' +
                        '<input type="text" name="website" style="display:none" tabindex="-1" autocomplete="off" aria-hidden="true">' +
                        '<div class="order-error" role="alert" aria-live="assertive"></div>' +
                        '<button type="submit" class="order-submit">Оформити</button>' +
                        '<p class="order-note">Ми зв’яжемося з вами для підтвердження замовлення</p>' +
                    '</form>' +
                '</div>' +
                '<div class="order-success" hidden>' +
                    '<p class="order-success-text" role="status">Дякуємо! Замовлення прийнято, ми зв’яжемося з вами найближчим часом</p>' +
                    '<button type="button" class="order-submit order-done">Закрити</button>' +
                '</div>' +
            '</div>';
        document.body.appendChild(overlay);

        form = overlay.querySelector('form');
        nameInput = form.elements.name;
        phoneInput = form.elements.phone;
        trapInput = form.elements.website;
        errEl = overlay.querySelector('.order-error');
        submitBtn = overlay.querySelector('.order-form .order-submit');
        successEl = overlay.querySelector('.order-success');
        formWrap = overlay.querySelector('.order-form-wrap');
        bodyEl = overlay.querySelector('.order-modal');

        overlay.addEventListener('mousedown', function (e) { if (e.target === overlay) close(); });
        overlay.querySelector('.order-close').addEventListener('click', close);
        overlay.querySelector('.order-done').addEventListener('click', close);
        form.addEventListener('submit', submit);
        phoneInput.addEventListener('input', function () { phoneInput.value = formatPhone(phoneInput.value); });
        document.addEventListener('keydown', onKey);
    }

    /* ---- Телефон ---- */
    function phoneDigits(v) { return String(v || '').replace(/\D/g, ''); }

    /* Повертає +380XXXXXXXXX, міжнародний +XXXXXXXXXX або '' якщо номер некоректний */
    function normalizePhone(v) {
        var d = phoneDigits(v);
        if (/^380\d{9}$/.test(d)) return '+' + d;
        if (/^0\d{9}$/.test(d)) return '+38' + d;
        if (/^\d{10,15}$/.test(d)) return '+' + d;
        return '';
    }

    /* Маска для вводу: 0XX XXX XX XX / +380 XX XXX XX XX / +XXXXXXXX... */
    function formatPhone(v) {
        var d = phoneDigits(v);
        if (!d) return /^\s*\+/.test(v) ? '+' : '';
        function group(s, sizes) {
            var out = [], pos = 0;
            for (var i = 0; i < sizes.length && pos < s.length; i++) {
                out.push(s.substr(pos, sizes[i]));
                pos += sizes[i];
            }
            if (pos < s.length) out.push(s.substr(pos));
            return out.join(' ');
        }
        if (d.indexOf('380') === 0) return '+380' + (d.length > 3 ? ' ' + group(d.slice(3, 12), [2, 3, 2, 2]) : '');
        if (d.charAt(0) === '0' && !/^\s*\+/.test(v)) return group(d.slice(0, 10), [3, 3, 2, 2]);
        return '+' + d.slice(0, 15);
    }

    /* ---- Відкриття / закриття ---- */
    function open(items, opts) {
        if (!items || !items.length) return;
        if (!overlay) build();
        currentItems = items;
        onSuccess = (opts && opts.onSuccess) || null;
        lastFocus = document.activeElement;
        form.reset();
        setError('');
        setSending(false);
        successEl.hidden = true;
        formWrap.hidden = false;
        overlay.hidden = false;
        document.documentElement.classList.add('order-open');
        nameInput.focus();
    }

    function close() {
        if (!overlay || overlay.hidden) return;
        overlay.hidden = true;
        document.documentElement.classList.remove('order-open');
        if (lastFocus && lastFocus.focus) lastFocus.focus();
    }

    function onKey(e) {
        if (!overlay || overlay.hidden) return;
        if (e.key === 'Escape') { e.preventDefault(); close(); return; }
        if (e.key !== 'Tab') return;
        /* Фокус не виходить за межі модалки */
        var els = Array.prototype.filter.call(
            bodyEl.querySelectorAll('button, input:not([tabindex="-1"]), a[href]'),
            function (el) { return !el.disabled && el.offsetParent !== null; });
        if (!els.length) return;
        var first = els[0], last = els[els.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
        else if (!bodyEl.contains(document.activeElement)) { e.preventDefault(); first.focus(); }
    }

    function setError(html) {
        errEl.innerHTML = html;
        errEl.style.display = html ? 'block' : 'none';
    }

    function setSending(on) {
        sending = on;
        submitBtn.disabled = on;
        submitBtn.classList.toggle('loading', on);
        submitBtn.textContent = on ? 'Відправляємо…' : 'Оформити';
    }

    /* ---- Відправка ---- */
    function submit(e) {
        e.preventDefault();
        if (sending) return;
        var name = nameInput.value.replace(/\s+/g, ' ').trim();
        var phone = normalizePhone(phoneInput.value);
        if (name.length < 2) { setError('Вкажіть ім’я (щонайменше 2 символи)'); nameInput.focus(); return; }
        if (name.length > 60) { setError('Ім’я занадто довге (до 60 символів)'); nameInput.focus(); return; }
        if (!phone) { setError('Вкажіть коректний номер телефону, наприклад +380 50 123 45 67'); phoneInput.focus(); return; }
        setError('');
        setSending(true);

        var total = 0;
        currentItems.forEach(function (it) { total += (it.price || 0) * (it.qty || 1); });
        var payload = {
            name: name,
            phone: phone,
            items: currentItems,
            total: total,
            page: location.href,
            website: trapInput.value
        };

        var ctrl = (typeof AbortController === 'function') ? new AbortController() : null;
        var timer = setTimeout(function () { if (ctrl) ctrl.abort(); }, 15000);
        /* text/plain — «проста» CORS-заявка без preflight; Worker все одно читає JSON */
        fetch(ORDER_ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
            body: JSON.stringify(payload),
            signal: ctrl ? ctrl.signal : undefined
        }).then(function (r) {
            return r.json().catch(function () { return { ok: false }; }).then(function (j) { return { status: r.status, body: j }; });
        }).then(function (res) {
            clearTimeout(timer);
            if (res.body && res.body.ok) { done(); return; }
            if (res.status === 429) { fail('Забагато спроб. Спробуйте трохи пізніше або напишіть нам у Telegram: <a href="' + TG_LINK + '" target="_blank" rel="noopener">@via_manager</a>'); return; }
            if (res.status === 400 && res.body && res.body.error) { fail(res.body.error); return; }
            fail();
        }).catch(function () { clearTimeout(timer); fail(); });
    }

    function fail(msg) {
        setSending(false);
        setError(msg || 'Не вдалося відправити. Спробуйте ще раз або напишіть нам у Telegram: <a href="' + TG_LINK + '" target="_blank" rel="noopener">@via_manager</a>');
    }

    function done() {
        setSending(false);
        formWrap.hidden = true;
        successEl.hidden = false;
        if (onSuccess) { try { onSuccess(); } catch (e) {} }
        successEl.querySelector('.order-done').focus();
    }

    /* ---- Збір позицій ---- */
    function absUrl(rel) {
        if (!rel) return '';
        if (/^https?:/.test(rel)) return rel;
        return SITE + '/' + rel.replace(/^\.?\//, '');
    }

    function cartItems() {
        return getCart().map(function (it) {
            var rel = (it.id && typeof PRODUCT_URLS !== 'undefined' && PRODUCT_URLS[it.id]) ? PRODUCT_URLS[it.id] : '';
            return { name: it.name, code: it.code || '', price: it.priceNum || 0, qty: it.qty || 1, url: absUrl(rel) };
        });
    }

    function productItems() {
        if (typeof PRODUCT === 'undefined') return [];
        var canon = document.querySelector('link[rel="canonical"]');
        return [{
            name: PRODUCT.name,
            code: PRODUCT.code || '',
            price: PRODUCT.priceNum || 0,
            qty: 1,
            url: canon ? canon.href : location.href
        }];
    }

    function init() {
        var cartBtn = document.getElementById('cartOrder');
        if (cartBtn) cartBtn.addEventListener('click', function () {
            open(cartItems(), { onSuccess: function () { clearCart(); } });
        });
        var prodBtn = document.getElementById('orderProductBtn');
        if (prodBtn) prodBtn.addEventListener('click', function () { open(productItems()); });
    }

    window.ViaOrder = { open: open, normalizePhone: normalizePhone };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
