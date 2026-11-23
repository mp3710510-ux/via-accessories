/* ============================================================
   FILTERS.JS — фільтри і сортування на сторінках відділів, «відділ + бренд», брендів, каталогу
   і результатів пошуку. Працює поверх статичних карток (.card з data-атрибутами від build_pages.py):
   data-price, data-brand / data-brand-name, data-color / data-color-name, data-added, data-name.
   Без JS усі картки й посилання видно як є. Стан — в адресі (?sort=price_asc&brand=chanel&min=…),
   canonical сторінок лишається без параметрів.
   ============================================================ */
(function () {
    'use strict';

    var SORTS = [
        ['new', 'Новинки'],
        ['price_asc', 'Ціна: від нижчої'],
        ['price_desc', 'Ціна: від вищої'],
        ['name', 'Назва А–Я']
    ];
    var SWATCH = {
        'чорний': '#1c1a17', 'білий': '#ffffff', 'кремовий': '#f3ead8', 'бежевий': '#d8c3a5', 'коричневий': '#7a5236',
        'червоний': '#b3262e', 'вишневий': '#7b1e32', 'бордовий': '#5c2430', 'рожевий': '#e7b4c0', 'синій': '#24406e',
        'блакитний': '#9cc3e4', 'зелений': '#3f6b45', 'темно-зелений': '#23402b', "м'ятний": '#b8dfcc', 'бірюзовий': '#3fb0ac',
        'сірий': '#9a958e', 'жовтий': '#e9c64a', 'помаранчевий': '#e08a3c', 'фіолетовий': '#6b4b8a', 'бузковий': '#b9a3d0',
        'хакі': '#7d7a4f', 'золотистий': '#c9a45c', 'сріблистий': '#c8c8c8',
        'різнокольоровий': 'conic-gradient(#b3262e,#e9c64a,#3f6b45,#24406e,#b3262e)',
        'леопардовий': 'radial-gradient(circle at 30% 30%,#3a2a1a 18%,transparent 20%),radial-gradient(circle at 70% 65%,#3a2a1a 16%,transparent 18%),#c99a5b'
    };
    var FILTER_ICON = '<svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><path d="M4 7h10M18 7h2M4 17h4M12 17h8" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><circle cx="16" cy="7" r="2" fill="none" stroke="currentColor" stroke-width="1.4"/><circle cx="10" cy="17" r="2" fill="none" stroke="currentColor" stroke-width="1.4"/></svg>';

    function esc(s) {
        return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
    function plural(n) {
        var a = n % 10, b = n % 100;
        if (a === 1 && b !== 11) return n + ' товар';
        if (a >= 2 && a <= 4 && (b < 12 || b > 14)) return n + ' товари';
        return n + ' товарів';
    }
    function money(n) { return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ' '); }
    function list(v) { return v ? v.split(',').filter(Boolean) : []; }
    function num(v) { var n = parseInt(String(v || '').replace(/\D/g, ''), 10); return isNaN(n) ? null : n; }

    function init(root) {
        if (!root || root.__viaFilters) return;
        var cards = Array.prototype.slice.call(root.querySelectorAll('.card[data-added]'));
        if (cards.length < 2) return;
        root.__viaFilters = true;

        cards.forEach(function (c, i) {
            c.__i = i;
            c.__price = parseFloat(c.getAttribute('data-price')) || 0;
            c.__brand = c.getAttribute('data-brand') || '';
            c.__color = c.getAttribute('data-color') || '';
            c.__added = c.getAttribute('data-added') || '';
            c.__name = c.getAttribute('data-name') || '';
        });

        /* варіанти — лише ті, що є серед товарів сторінки */
        function options(key, nameAttr) {
            var seen = {}, out = [];
            cards.forEach(function (c) {
                var v = c['__' + key];
                if (!v || seen[v]) return;
                seen[v] = 1;
                out.push({ v: v, label: c.getAttribute(nameAttr) || v });
            });
            return out.sort(function (a, b) { return a.label.localeCompare(b.label, 'uk'); });
        }
        var allowed = (root.getAttribute('data-facets') || '').split(',');
        var brandOpts = options('brand', 'data-brand-name');
        var colorOpts = options('color', 'data-color-name');
        var prices = cards.map(function (c) { return c.__price; }).filter(Boolean);
        var pMin = prices.length ? Math.min.apply(null, prices) : 0;
        var pMax = prices.length ? Math.max.apply(null, prices) : 0;
        var has = {
            brand: allowed.indexOf('brand') >= 0 && brandOpts.length >= 2,
            color: allowed.indexOf('color') >= 0 && colorOpts.length >= 2,
            price: allowed.indexOf('price') >= 0 && pMax > pMin
        };
        var anyFacet = has.brand || has.color || has.price;

        /* стан з адреси */
        var params = new URLSearchParams(location.search);
        var state = {
            sort: SORTS.some(function (s) { return s[0] === params.get('sort'); }) ? params.get('sort') : 'new',
            brand: has.brand ? list(params.get('brand')).filter(function (v) { return brandOpts.some(function (o) { return o.v === v; }); }) : [],
            color: has.color ? list(params.get('color')).filter(function (v) { return colorOpts.some(function (o) { return o.v === v; }); }) : [],
            min: has.price ? num(params.get('min')) : null,
            max: has.price ? num(params.get('max')) : null
        };

        /* ---------- панель над сіткою ---------- */
        var bar = document.createElement('div');
        bar.className = 'filter-bar';
        bar.innerHTML =
            (anyFacet ? '<button type="button" class="filter-btn" aria-haspopup="dialog" aria-expanded="false">' + FILTER_ICON +
                '<span>Фільтри</span><span class="filter-badge" hidden></span></button>' : '') +
            '<div class="filter-total" aria-live="polite"></div>' +
            '<label class="filter-sort"><span>Сортування</span><select>' +
            SORTS.map(function (s) { return '<option value="' + s[0] + '">' + s[1] + '</option>'; }).join('') +
            '</select></label>';
        var chips = document.createElement('div');
        chips.className = 'filter-chips';
        var nothing = document.createElement('div');
        nothing.className = 'filter-nothing';
        nothing.hidden = true;
        nothing.innerHTML = '<p>За цими фільтрами нічого немає</p><button type="button" data-freset>Скинути фільтри</button>';
        var tabs = root.querySelector('.dept-filter');               // сторінка бренду: перемикачі відділів — вище
        var anchor = tabs ? tabs.nextSibling : root.firstChild;
        root.insertBefore(bar, anchor);
        root.insertBefore(chips, anchor);
        root.insertBefore(nothing, anchor);
        var select = bar.querySelector('select');
        select.value = state.sort;
        var total = bar.querySelector('.filter-total');
        var openBtn = bar.querySelector('.filter-btn');
        var badge = bar.querySelector('.filter-badge');

        /* ---------- шухляда фільтрів (на телефоні — знизу, на комп'ютері — справа) ---------- */
        var layer = null, panel, applyBtn;
        if (anyFacet) {
            layer = document.createElement('div');
            layer.className = 'filter-layer';
            layer.hidden = true;
            var body = '';
            if (has.brand) body += group('Бренд', 'brand', brandOpts, false);
            if (has.price) {
                body += '<fieldset class="filter-group"><legend>Ціна, грн</legend><div class="filter-price">' +
                    '<label><span>від</span><input type="number" inputmode="numeric" min="0" step="100" data-price="min" placeholder="' + money(pMin) + '"></label>' +
                    '<span class="filter-dash" aria-hidden="true">—</span>' +
                    '<label><span>до</span><input type="number" inputmode="numeric" min="0" step="100" data-price="max" placeholder="' + money(pMax) + '"></label>' +
                    '</div><p class="filter-range">На сторінці: ' + money(pMin) + ' – ' + money(pMax) + ' грн</p></fieldset>';
            }
            if (has.color) body += group('Колір', 'color', colorOpts, true);
            layer.innerHTML =
                '<div class="filter-backdrop" data-fclose></div>' +
                '<aside class="filter-panel" role="dialog" aria-modal="true" aria-label="Фільтри" tabindex="-1">' +
                '<div class="filter-head"><span>Фільтри</span><button type="button" class="filter-x" data-fclose aria-label="Закрити">&#x2715;</button></div>' +
                '<div class="filter-body">' + body + '</div>' +
                '<div class="filter-foot"><button type="button" class="filter-reset" data-freset>Скинути</button>' +
                '<button type="button" class="filter-apply" data-fclose></button></div></aside>';
            document.body.appendChild(layer);
            panel = layer.querySelector('.filter-panel');
            applyBtn = layer.querySelector('.filter-apply');
            var pin = layer.querySelectorAll('[data-price]');
            if (pin.length) {
                pin[0].value = state.min != null ? state.min : '';
                pin[1].value = state.max != null ? state.max : '';
            }
            layer.addEventListener('change', function (e) {
                var cb = e.target;
                if (cb.type === 'checkbox') {
                    var arr = state[cb.name];
                    var at = arr.indexOf(cb.value);
                    if (cb.checked && at < 0) arr.push(cb.value);
                    if (!cb.checked && at >= 0) arr.splice(at, 1);
                    apply();
                }
            });
            var timer;
            layer.addEventListener('input', function (e) {
                if (!e.target.hasAttribute('data-price')) return;
                clearTimeout(timer);
                timer = setTimeout(function () {
                    state.min = num(pin[0].value);
                    state.max = num(pin[1].value);
                    apply();
                }, 350);
            });
            layer.addEventListener('click', function (e) {
                if (e.target.closest('[data-fclose]')) close();
            });
            openBtn.addEventListener('click', open);
        }

        function group(title, key, opts, swatch) {
            return '<fieldset class="filter-group"><legend>' + title + '</legend><div class="filter-opts">' +
                opts.map(function (o) {
                    var sw = swatch ? '<span class="filter-swatch" style="background:' + (SWATCH[o.label] || '#e6dccb') + '"></span>' : '';
                    return '<label class="filter-opt"><input type="checkbox" name="' + key + '" value="' + esc(o.v) + '"' +
                        (state[key].indexOf(o.v) >= 0 ? ' checked' : '') + '><span class="filter-check" aria-hidden="true"></span>' +
                        sw + '<span class="filter-label">' + esc(o.label) + '</span><span class="filter-num" data-count="' + key + ':' + esc(o.v) + '"></span></label>';
                }).join('') + '</div></fieldset>';
        }

        function open() {
            layer.hidden = false;
            document.documentElement.classList.add('filter-lock');
            openBtn.setAttribute('aria-expanded', 'true');
            requestAnimationFrame(function () { layer.classList.add('is-open'); panel.focus(); });
        }
        function close() {
            if (!layer || layer.hidden) return;
            layer.classList.remove('is-open');
            document.documentElement.classList.remove('filter-lock');
            openBtn.setAttribute('aria-expanded', 'false');
            setTimeout(function () { layer.hidden = true; }, 260);
            openBtn.focus();
        }
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') close();
        });

        /* ---------- фільтрація, лічильники, сортування ---------- */
        function ok(c, skip) {
            if (skip !== 'brand' && state.brand.length && state.brand.indexOf(c.__brand) < 0) return false;
            if (skip !== 'color' && state.color.length && state.color.indexOf(c.__color) < 0) return false;
            if (state.min != null && (!c.__price || c.__price < state.min)) return false;
            if (state.max != null && (!c.__price || c.__price > state.max)) return false;
            return true;
        }
        function cmp(a, b) {
            switch (state.sort) {
                case 'price_asc': return (a.__price || Infinity) - (b.__price || Infinity) || a.__i - b.__i;
                case 'price_desc': return (b.__price || -1) - (a.__price || -1) || a.__i - b.__i;
                case 'name': return a.__name.localeCompare(b.__name, 'uk', { sensitivity: 'base' }) || a.__i - b.__i;
                default: return (a.__added < b.__added ? 1 : a.__added > b.__added ? -1 : 0) || a.__i - b.__i;
            }
        }

        function apply() {
            var shown = 0;
            cards.forEach(function (c) {
                var yes = ok(c);
                c.classList.toggle('is-filtered-out', !yes);
                if (yes) shown++;
            });
            /* сортування — усередині кожної сітки (на сторінці бренду їх кілька, по відділах) */
            Array.prototype.forEach.call(root.querySelectorAll('.grid'), function (g) {
                var own = Array.prototype.filter.call(g.children, function (c) { return c.__i !== undefined; });
                own.sort(cmp).forEach(function (c) { g.appendChild(c); });
            });
            Array.prototype.forEach.call(root.querySelectorAll('.dept-section'), function (s) {
                s.classList.toggle('filter-empty', !s.querySelector('.card:not(.is-filtered-out)'));
            });
            nothing.hidden = shown > 0;
            total.textContent = plural(shown);
            if (applyBtn) applyBtn.textContent = shown ? 'Показати ' + plural(shown) : 'Нічого не знайдено';
            if (layer) {
                Array.prototype.forEach.call(layer.querySelectorAll('[data-count]'), function (el) {
                    var kv = el.getAttribute('data-count').split(':'), key = kv[0], v = kv[1];
                    var n = cards.filter(function (c) { return c['__' + key] === v && ok(c, key); }).length;
                    el.textContent = n;
                    var input = el.parentNode.querySelector('input');
                    el.parentNode.classList.toggle('is-disabled', !n && !input.checked);
                    input.disabled = !n && !input.checked;
                });
            }
            var active = state.brand.length + state.color.length + (state.min != null ? 1 : 0) + (state.max != null ? 1 : 0);
            if (badge) { badge.hidden = !active; badge.textContent = active; }
            renderChips(active);
            saveUrl();
        }

        function renderChips(active) {
            if (!active) { chips.innerHTML = ''; chips.hidden = true; return; }
            chips.hidden = false;
            var html = '';
            state.brand.forEach(function (v) { html += chip('brand', v, label(brandOpts, v)); });
            state.color.forEach(function (v) { html += chip('color', v, label(colorOpts, v)); });
            if (state.min != null) html += chip('min', '', 'від ' + money(state.min) + ' грн');
            if (state.max != null) html += chip('max', '', 'до ' + money(state.max) + ' грн');
            chips.innerHTML = html + '<button type="button" class="filter-clear" data-freset>Скинути все</button>';
        }
        function label(opts, v) { for (var i = 0; i < opts.length; i++) if (opts[i].v === v) return opts[i].label; return v; }
        function chip(key, v, text) {
            return '<button type="button" class="filter-chip" data-chip="' + key + '" data-v="' + esc(v) + '">' + esc(text) +
                '<span aria-hidden="true">&#x2715;</span><span class="visually-hidden"> — прибрати</span></button>';
        }
        chips.addEventListener('click', function (e) {
            var c = e.target.closest('[data-chip]');
            if (!c) return;
            var key = c.getAttribute('data-chip'), v = c.getAttribute('data-v');
            if (key === 'min' || key === 'max') state[key] = null;
            else state[key].splice(state[key].indexOf(v), 1);
            syncInputs();
            apply();
        });
        function reset() {
            state.brand = []; state.color = []; state.min = null; state.max = null;
            syncInputs();
            apply();
        }
        function syncInputs() {
            if (!layer) return;
            Array.prototype.forEach.call(layer.querySelectorAll('input[type=checkbox]'), function (cb) {
                cb.checked = state[cb.name].indexOf(cb.value) >= 0;
            });
            var pin = layer.querySelectorAll('[data-price]');
            if (pin.length) {
                pin[0].value = state.min != null ? state.min : '';
                pin[1].value = state.max != null ? state.max : '';
            }
        }
        document.addEventListener('click', function (e) {
            if (e.target.closest('[data-freset]') && (root.contains(e.target) || (layer && layer.contains(e.target)))) reset();
        });
        select.addEventListener('change', function () { state.sort = select.value; apply(); });

        function saveUrl() {
            var p = new URLSearchParams(location.search);
            ['sort', 'brand', 'color', 'min', 'max'].forEach(function (k) { p.delete(k); });
            if (state.sort !== 'new') p.set('sort', state.sort);
            if (state.brand.length) p.set('brand', state.brand.join(','));
            if (state.color.length) p.set('color', state.color.join(','));
            if (state.min != null) p.set('min', state.min);
            if (state.max != null) p.set('max', state.max);
            var qs = p.toString().replace(/%2C/g, ',');
            history.replaceState(history.state, '', location.pathname + (qs ? '?' + qs : '') + location.hash);
        }

        apply();
    }

    window.ViaFilters = { init: init };
    var roots = document.querySelectorAll('[data-filter-root]:not([data-filter-defer])');
    Array.prototype.forEach.call(roots, init);
})();
