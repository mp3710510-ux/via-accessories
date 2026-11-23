/* ============================================================
   SEARCH.JS — пошук у шапці (усі сторінки) і сторінка результатів search.html.
   Дані — assets/search-index.js (генерує build_pages.py з products.js; лише видимі товари).
   Індекс підвантажується при першому відкритті пошуку. Сервера немає — усе в браузері.
   ============================================================ */
(function () {
    'use strict';

    /* корінь сайту — з адреси цього скрипта (сторінки лежать на різній глибині) */
    var me = document.currentScript && document.currentScript.src;
    var ROOT = me ? me.replace(/assets\/search\.js(\?.*)?$/, '') : '/';
    var TG = 'https://t.me/via_manager';
    var LIMIT = 8;

    /* ---------- нормалізація: регістр, діакритика (Hermès = hermes), кирилиця -> латиниця для брендів ---------- */
    function norm(s) {
        return String(s || '').toLowerCase()
            .normalize('NFD').replace(/[̀-ͯ]/g, '')      // é -> e, ї -> і, й -> и
            .replace(/[’'`ʼ]/g, '')
            .replace(/ё/g, 'е').replace(/ы/g, 'и').replace(/э/g, 'е')
            .replace(/[^a-z0-9а-яієґ]+/g, ' ')
            .trim();
    }
    /* кириличні та скорочені назви брендів -> як у даних (після norm) */
    var ALIASES = {
        'chanel': ['шанель', 'шанел', 'шанэль'],
        'dior': ['діор', 'диор'],
        'gucci': ['гуччі', 'гучі', 'гуччи', 'гучи'],
        'louis vuitton': ['луї віттон', 'луі вітон', 'луї вітон', 'луі віттон', 'луи виттон', 'луи витон', 'луї', 'віттон', 'вітон', 'лв', 'lv'],
        'hermes': ['гермес', 'ермес', 'эрмес', 'гермєс'],
        'prada': ['прада'],
        'balenciaga': ['баленсіага', 'баленсиага', 'баленсіяга'],
        'bottega veneta': ['боттега венета', 'ботега венета', 'боттега', 'ботега'],
        'coach': ['коуч', 'коач'],
        'van cleef arpels': ['ван кліф і арпельс', 'ван кліф арпельс', 'ван кліф', 'ван клиф', 'ван кліфф', 'vca'],
        'chrome hearts': ['хром хартс', 'хром хартз', 'хромхартс'],
        'golden goose': ['голден гус', 'голден гуз', 'ggdb'],
        'dolce gabbana': ['дольче габбана', 'дольче габана', 'дольче', 'д г', 'дг', 'd g', 'dg'],
        'loro piana': ['лоро піана', 'лоро пиана', 'лоро'],
        'miu miu': ['міу міу', 'миу миу', 'міумію'],
        'tom ford': ['том форд'],
        'bvlgari': ['булгарі', 'бвлгарі', 'булгари', 'bulgari']
    };
    var ALIAS_LIST = [];
    Object.keys(ALIASES).forEach(function (to) {
        ALIASES[to].forEach(function (from) { ALIAS_LIST.push([norm(from), to]); });
    });
    ALIAS_LIST.sort(function (a, b) { return b[0].length - a[0].length; });   // довші фрази першими

    function prepareQuery(q) {
        var s = ' ' + norm(q) + ' ';
        ALIAS_LIST.forEach(function (a) {
            s = s.split(' ' + a[0] + ' ').join(' ' + a[1] + ' ');
        });
        return s.trim().split(' ').filter(Boolean);
    }

    var CYR = /[а-яієґ]/;
    /* «сумки» має знаходити «сумка», «браслети» — «браслет»: для кирилиці відкидаємо закінчення */
    function variants(tok) {
        var out = [tok];
        if (CYR.test(tok)) {
            if (tok.length >= 5) out.push(tok.slice(0, -1));
            if (tok.length >= 7) out.push(tok.slice(0, -2));
        }
        return out;
    }

    var INDEX = null, loading = null;
    function prepIndex() {
        INDEX = (window.SEARCH_INDEX || []).map(function (it, i) {
            return {
                it: it, i: i,
                brand: ' ' + norm(it.b),
                name: ' ' + norm(it.n),
                code: norm(it.c),
                all: ' ' + norm([it.b, it.n, it.c, it.t, it.co].join(' '))
            };
        });
    }
    function loadIndex(cb) {
        if (INDEX) return cb();
        if (window.SEARCH_INDEX) { prepIndex(); return cb(); }
        if (!loading) {
            loading = [];
            var s = document.createElement('script');
            s.src = ROOT + 'assets/search-index.js';
            s.onload = function () { prepIndex(); loading.forEach(function (f) { f(); }); };
            s.onerror = function () { INDEX = []; loading.forEach(function (f) { f(); }); };
            document.head.appendChild(s);
        }
        loading.push(cb);
    }

    /* кожне слово запиту має знайтись на початку якогось слова товару (бренд, назва, код, тип, колір) */
    function search(q) {
        var toks = prepareQuery(q);
        if (!toks.length || !INDEX) return [];
        var res = [];
        INDEX.forEach(function (e) {
            var score = 0;
            for (var k = 0; k < toks.length; k++) {
                var vs = variants(toks[k]), hit = 0;
                for (var v = 0; v < vs.length && !hit; v++) {
                    var t = vs[v];
                    if (e.code && e.code === t) hit = 50;
                    else if (e.code && e.code.indexOf(t) === 0 && /\d/.test(t)) hit = 20;
                    else if (e.brand.indexOf(' ' + t) >= 0) hit = 8;
                    else if (e.name.indexOf(' ' + t) >= 0) hit = 5;
                    else if (e.all.indexOf(' ' + t) >= 0) hit = 2;
                }
                if (!hit) return;
                score += hit;
            }
            res.push({ e: e, s: score });
        });
        res.sort(function (a, b) { return b.s - a.s || a.e.i - b.e.i; });   // однакова вага — новинки першими
        return res.map(function (r) { return r.e.it; });
    }

    /* ---------- спільне ---------- */
    function esc(s) {
        return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
    function webp(it, w) {
        var base = it.i.split('/').pop().replace(/\.[^.]+$/, '');
        return encodeURI(ROOT + 'content/optimized/' + base + '-' + w + '.webp');
    }
    function thumbSrc(it) {
        if (!it.i) return '';
        if (!it.ws) return encodeURI(ROOT + it.i);
        var best = it.ws.filter(function (w) { return w >= 240; })[0] || it.ws[it.ws.length - 1];
        return webp(it, best);
    }
    function plural(n) {
        var a = n % 10, b = n % 100;
        if (a === 1 && b !== 11) return n + ' товар';
        if (a >= 2 && a <= 4 && (b < 12 || b > 14)) return n + ' товари';
        return n + ' товарів';
    }
    function searchUrl(q) { return ROOT + 'search.html?q=' + encodeURIComponent(q); }
    function emptyHtml() {
        return '<div class="search-empty"><p>Нічого не знайдено</p><span>Спробуйте інше слово або напишіть нам — підберемо.</span>' +
            '<div class="search-empty-links"><a href="' + ROOT + 'catalog.html">Перейти в каталог</a>' +
            '<a href="' + TG + '" target="_blank" rel="noopener">Telegram @via_manager</a></div></div>';
    }

    /* ---------- оверлей пошуку в шапці ---------- */
    var ov, input, list, lastFocus, active = -1, current = [];
    var POPULAR = ['Chanel', 'Louis Vuitton', 'Dior', 'Hermès', 'Сумки', 'Окуляри'];

    function build() {
        ov = document.createElement('div');
        ov.className = 'search-overlay';
        ov.setAttribute('role', 'dialog');
        ov.setAttribute('aria-modal', 'true');
        ov.setAttribute('aria-label', 'Пошук');
        ov.innerHTML =
            '<div class="search-backdrop" data-search-close></div>' +
            '<div class="search-panel">' +
            '<form class="search-form" role="search" action="' + ROOT + 'search.html">' +
            '<svg class="search-form-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M15.6 15.6 21 21" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>' +
            '<input class="search-input" type="search" name="q" autocomplete="off" spellcheck="false" placeholder="Бренд, модель або код" aria-label="Пошук товарів" aria-controls="searchResults">' +
            '<button class="search-close" type="button" aria-label="Закрити пошук" data-search-close>&#x2715;</button>' +
            '</form>' +
            '<div class="search-results" id="searchResults"></div>' +
            '</div>';
        document.body.appendChild(ov);
        input = ov.querySelector('.search-input');
        list = ov.querySelector('.search-results');
        ov.addEventListener('click', function (e) {
            if (e.target.closest('[data-search-close]')) { e.preventDefault(); close(); }
            var chip = e.target.closest('[data-search-chip]');
            if (chip) { e.preventDefault(); input.value = chip.textContent; render(); input.focus(); }
        });
        input.addEventListener('input', render);
        input.addEventListener('keydown', onKey);
        ov.querySelector('.search-form').addEventListener('submit', function (e) {
            if (input.value.trim().length < 2) e.preventDefault();
        });
    }

    function hint() {
        list.innerHTML = '<div class="search-hint"><span>Популярне</span>' +
            POPULAR.map(function (p) { return '<button type="button" data-search-chip>' + esc(p) + '</button>'; }).join('') + '</div>';
    }

    function render() {
        var q = input.value.trim();
        active = -1;
        if (q.length < 2) { current = []; hint(); return; }
        loadIndex(function () {
            if (input.value.trim() !== q) return;          // поки вантажився індекс, запит змінився
            current = search(q);
            if (!current.length) { list.innerHTML = emptyHtml(); return; }
            var html = '<ul class="search-list" role="listbox">';
            current.slice(0, LIMIT).forEach(function (it, i) {
                html += '<li role="option" id="sr' + i + '"><a class="search-item" href="' + ROOT + it.u + '">' +
                    '<span class="search-thumb">' + (it.i ? '<img src="' + thumbSrc(it) + '" alt="" loading="lazy" decoding="async">' : '') + '</span>' +
                    '<span class="search-text">' + (it.b ? '<span class="search-brand">' + esc(it.b) + '</span>' : '') +
                    '<span class="search-name">' + esc(it.n) + '</span>' +
                    (it.p ? '<span class="search-price">' + esc(it.p) + '</span>' : '') + '</span></a></li>';
            });
            html += '</ul><a class="search-all" href="' + searchUrl(q) + '">Усі результати (' + current.length + ')<span aria-hidden="true">→</span></a>';
            list.innerHTML = html;
        });
    }

    function onKey(e) {
        var items = list.querySelectorAll('.search-item');
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
            if (!items.length) return;
            e.preventDefault();
            active = (active + (e.key === 'ArrowDown' ? 1 : -1) + items.length + 1) % (items.length + 1);
            if (active === items.length) active = -1;
            for (var i = 0; i < items.length; i++) items[i].classList.toggle('is-active', i === active);
            input.setAttribute('aria-activedescendant', active >= 0 ? 'sr' + active : '');
            if (active >= 0) items[active].scrollIntoView({ block: 'nearest' });
        } else if (e.key === 'Enter' && active >= 0 && items[active]) {
            e.preventDefault();
            location.href = items[active].href;
        }
    }

    function open() {
        if (!ov) build();
        lastFocus = document.activeElement;
        ov.classList.add('is-open');
        document.documentElement.classList.add('search-lock');
        if (!input.value) hint();
        input.focus();                       // одразу в обробнику кліку — інакше на iPhone не з'явиться клавіатура
        loadIndex(function () {});
    }
    function close() {
        if (!ov || !ov.classList.contains('is-open')) return;
        ov.classList.remove('is-open');
        document.documentElement.classList.remove('search-lock');
        if (lastFocus && lastFocus.focus) lastFocus.focus();
    }

    document.addEventListener('click', function (e) {
        var t = e.target.closest && e.target.closest('[data-search-open]');
        if (!t) return;
        e.preventDefault();
        open();
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') close();
    });

    /* ---------- сторінка search.html: сітка карток як у каталозі + фільтри ---------- */
    var grid = document.getElementById('searchGrid');
    if (!grid) return;
    var status = document.getElementById('searchStatus');
    var params = new URLSearchParams(location.search);
    var q = (params.get('q') || '').trim();
    var h1 = document.querySelector('.page-header h1');

    function cardHtml(it, i) {
        var href = ROOT + it.u, alt = esc((it.b ? it.b + ' ' : '') + it.n), img = '';
        if (it.i) {
            if (it.ws) {
                var set = it.ws.map(function (w) { return webp(it, w) + ' ' + w + 'w'; }).join(', ');
                img = '<picture><source type="image/webp" srcset="' + set + '" sizes="(max-width:500px) 100vw, (max-width:900px) 50vw, 25vw">' +
                    '<img src="' + encodeURI(ROOT + it.i) + '" width="' + it.wh[0] + '" height="' + it.wh[1] + '" alt="' + alt + '"' +
                    (i < 4 ? '' : ' loading="lazy"') + ' decoding="async"></picture>';
            } else {
                img = '<img src="' + encodeURI(ROOT + it.i) + '" alt="' + alt + '" loading="lazy">';
            }
        }
        return '<div class="card" data-price="' + (it.pn || '') + '" data-brand="' + esc(it.bs || '') +
            '" data-brand-name="' + esc(it.b) + '" data-color="' + esc(it.cs || '') + '" data-color-name="' + esc(it.co) +
            '" data-added="' + esc(it.a) + '" data-name="' + esc(it.n) + '">' +
            '<a href="' + href + '" style="display:block;text-decoration:none;color:inherit;"><div class="card-image">' + img + '</div></a>' +
            '<div class="card-caption"><a href="' + href + '" style="text-decoration:none;color:inherit;"><div class="name">' + esc(it.n) + '</div>' +
            (it.p ? '<div class="price">' + esc(it.p) + '</div>' : '') + (it.c ? '<div class="code">' + esc(it.c) + '</div>' : '') + '</a>' +
            '<button class="add-to-cart" type="button" data-id="' + esc(it.id) + '">У кошик</button></div></div>';
    }

    function bindCart(byId) {
        var btns = grid.querySelectorAll('.add-to-cart');
        Array.prototype.forEach.call(btns, function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                var it = byId[btn.getAttribute('data-id')];
                if (!it || typeof addToCart !== 'function') return;
                addToCart({ id: it.id, name: it.n, price: it.p || 'ціну уточнюйте', code: it.c, priceNum: it.pn || 0, img: it.i });
                btn.classList.add('added');
                btn.textContent = '✓ Додано';
                setTimeout(function () { btn.classList.remove('added'); btn.textContent = 'У кошик'; }, 1200);
            });
        });
    }

    if (q.length < 2) {
        status.innerHTML = '<p>Введіть щонайменше два символи.</p>';
        open();
        return;
    }
    if (h1) h1.textContent = 'Пошук';
    document.title = 'Пошук: ' + q + ' | via.accessories';
    status.innerHTML = '<p class="search-query">«' + esc(q) + '»</p>';
    loadIndex(function () {
        var found = search(q);
        if (!found.length) {
            status.innerHTML = '<p class="search-query">«' + esc(q) + '»</p>' + emptyHtml();
            return;
        }
        var byId = {};
        grid.innerHTML = found.map(function (it, i) { byId[it.id] = it; return cardHtml(it, i); }).join('');
        bindCart(byId);
        var root = grid.closest('[data-filter-root]');
        if (window.ViaFilters && root) window.ViaFilters.init(root);
    });
})();
