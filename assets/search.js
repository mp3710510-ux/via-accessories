/* ============================================================
   SEARCH.JS — пошук у шапці (усі сторінки) і сторінка результатів search.html.
   Дані — assets/search-index.js (генерує build_pages.py з products.js; лише видимі товари).
   Індекс підвантажується при першому відкритті пошуку. Сервера немає — усе в браузері.
   ============================================================ */
/* ---------- ЯДРО ПОШУКУ (без браузера: його ж перевіряють тести via-admin/tests/test_search.py) ----------
   1) нормалізація: регістр, діакритика (Hermès = hermes), фонетика латиниці/кирилиці (shanel = chanel,
      гуччі = гучі, кроссовки ≈ кросовкі);
   2) словник брендів і типів товарів (укр/рос/англ, типові помилки) -> як у даних;
   3) нечіткий пошук, лише коли точного збігу немає: відстань Дамерау–Левенштейна до 1 помилки для слів
      з 4–6 літер і до 2 — для довших (коротші слова й коди — лише точно). Точні збіги — вище. */
var SearchCore = (function () {
    'use strict';

    function base(s) {
        return String(s || '').toLowerCase()
            .normalize('NFD').replace(/[̀-ͯ]/g, '')      // é -> e, ї -> і, й -> и
            .replace(/[’'`ʼ]/g, '')
            .replace(/[^a-z0-9а-яієґё]+/g, ' ')
            .trim();
    }
    /* фонетика одного слова: різні написання одного звучання -> одна форма */
    function phon(w) {
        if (/[a-z]/.test(w)) {
            w = w.replace(/sch/g, 'ch').replace(/sh/g, 'ch').replace(/ph/g, 'f')
                .replace(/ck/g, 'k').replace(/q/g, 'k').replace(/w/g, 'v').replace(/y/g, 'i');
        }
        if (/[а-яієґё]/.test(w)) {
            w = w.replace(/[єэё]/g, 'е').replace(/[иыї]/g, 'і');
        }
        return w.replace(/([a-zа-яієґё])\1+/g, '$1');   // подвоєні літери -> одна (цифри кодів не чіпаємо: 7322 ≠ 732)
    }
    function words(s) { return base(s).split(' ').filter(Boolean).map(phon); }

    /* бренди: назва як у даних -> усі відомі написання (укр/рос/англ, помилки) */
    var BRANDS = {
        'Chanel': ['shanel', 'chanell', 'chanal', 'шанэль', 'шанел', 'шанель', 'шанель'],
        'Louis Vuitton': ['louis vitton', 'luis vuiton', 'louis vuiton', 'louie vuitton', 'luis vuitton', 'louis viton',
            'луи виттон', 'луи витон', 'луї вітон', 'луї віттон', 'луі вітон', 'луі віттон', 'лв', 'lv'],
        'Gucci': ['gucchi', 'guchi', 'гуччи', 'гучи', 'гучі', 'гуччі'],
        'Hermès': ['ermes', 'hermess', 'гермес', 'эрмес', 'ермес', 'гермєс'],
        'Dior': ['диор', 'діор'],
        'Balenciaga': ['balensiaga', 'balenciga', 'баленсиага', 'баленсіага'],
        'Bottega Veneta': ['bottega', 'botega', 'botega veneta', 'боттега венета', 'ботега венета', 'боттега', 'ботега'],
        'Prada': ['прада'],
        'Coach': ['couch', 'коуч', 'коач'],
        'Van Cleef & Arpels': ['van cleef', 'van clif', 'van clef', 'vancleef', 'van cleef arpels', 'ван клиф', 'ван кліф',
            'ван кліф арпельс', 'ван клиф арпельс', 'vca'],
        'Chrome Hearts': ['chrom harts', 'chrome harts', 'chrom hearts', 'хром хартс', 'хром хартз'],
        'Golden Goose': ['goldengoose', 'голден гус', 'голден гуз', 'ggdb'],
        'Dolce & Gabbana': ['dolce gabbana', 'dolce gabana', 'dolce', 'd g', 'dg', 'дольче габбана', 'дольче габана', 'дольче', 'дг'],
        'Loro Piana': ['лоро пиана', 'лоро піана'],
        'Miu Miu': ['миу миу', 'міу міу'],
        'Tom Ford': ['том форд'],
        'Bvlgari': ['bulgari', 'булгари', 'булгарі', 'бвлгарі'],
        'Rolex': ['ролекс'],
        'Cartier': ['картье', 'картьє']
    };
    /* типи товарів: будь-яке написання -> «хоча б одне з цих слів» у товарі (як у search-index.js) */
    var TYPES = [
        [['сумка', 'bag'], ['сумка', 'сумки', 'сумочка', 'бег', 'беги', 'bag', 'bags', 'torba', 'торба']],
        [['кросівки', 'sneakers'], ['кроссовки', 'кросовки', 'кросівки', 'sneakers', 'sneaker', 'snikers', 'сникерс']],
        [['окуляри', 'glasses', 'sunglasses'], ['очки', 'окуляри', 'glasses', 'sunglasses']],
        [['браслет', 'bracelet'], ['браслет', 'браслети', 'bracelet', 'braslet']],
        [['гаманець', 'wallet'], ['кошелек', 'кошельок', 'гаманець', 'wallet']],
        [['ремінь', 'belt'], ['ремень', 'ремінь', 'belt']],
        [['годинник', 'watch'], ['часы', 'годинник', 'watch']],
        [['сережки', 'earrings'], ['серьги', 'сережки', 'earrings']],
        [['каблучка', 'ring'], ['кольцо', 'каблучка', 'ring']],
        [['шарф', 'scarf', 'палантин'], ['шарф', 'scarf']],
        [['хустка', 'scarf'], ['платок', 'хустка']]
    ];

    /* фраза (фонетичні слова через пробіл) -> {q: слова, any: групи, show: як показати, brand: так/ні} */
    var ALIAS = {}, MAXLEN = 1;
    function addAlias(key, val) {
        var k = words(key).join(' ');
        if (!k || ALIAS[k]) return;
        ALIAS[k] = val;
        MAXLEN = Math.max(MAXLEN, k.split(' ').length);
    }
    Object.keys(BRANDS).forEach(function (b) {
        var val = { q: words(b), show: b, brand: true };
        addAlias(b, val);
        BRANDS[b].forEach(function (k) { addAlias(k, val); });
    });
    TYPES.forEach(function (t) {
        var val = { any: t[0].map(function (w) { return words(w).join(' '); }), show: t[0][0] };
        t[1].forEach(function (k) { addAlias(k, val); });
    });

    /* Дамерау–Левенштейн (перестановка сусідніх літер = 1 помилка); max — далі не рахуємо */
    function dl(a, b, max) {
        if (Math.abs(a.length - b.length) > max) return max + 1;
        var d = [], i, j;
        for (i = 0; i <= a.length; i++) { d[i] = [i]; }
        for (j = 0; j <= b.length; j++) { d[0][j] = j; }
        for (i = 1; i <= a.length; i++) {
            var rowMin = Infinity;
            for (j = 1; j <= b.length; j++) {
                var c = a[i - 1] === b[j - 1] ? 0 : 1;
                var v = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + c);
                if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) v = Math.min(v, d[i - 2][j - 2] + 1);
                d[i][j] = v;
                if (v < rowMin) rowMin = v;
            }
            if (rowMin > max) return max + 1;
        }
        return d[a.length][b.length];
    }
    function allowed(tok) {
        if (/\d/.test(tok) || tok.length < 4) return 0;     // коди і короткі слова — лише точно
        return tok.length <= 6 ? 1 : 2;
    }

    var CYR = /[а-яієґ]/;
    /* «сумки» знаходить «сумка», «браслети» — «браслет»: для кирилиці відкидаємо закінчення */
    function variants(tok) {
        var out = [tok];
        if (CYR.test(tok)) {
            if (tok.length >= 5) out.push(tok.slice(0, -1));
            if (tok.length >= 7) out.push(tok.slice(0, -2));
        }
        return out;
    }

    var ITEMS = [], VOCAB = [], SHOW = {};
    function setIndex(rows) {
        var vocab = {};
        SHOW = {};
        ITEMS = (rows || []).map(function (it, i) {
            var e = {
                it: it, i: i,
                brand: words(it.b), name: words(it.n), code: base(it.c).replace(/ /g, ''),
                rest: words([it.c, it.t, it.co].join(' '))
            };
            /* як показати слово у «Показано результати для»: оригінальне написання з бренду/назви */
            [[it.b, e.brand], [it.n, e.name]].forEach(function (pair) {
                var orig = base(pair[0]).split(' ');
                var src = String(pair[0] || '').split(/[\s\/&,]+/).filter(function (x) { return base(x); });
                pair[1].forEach(function (w, k) {
                    if (!SHOW[w]) SHOW[w] = src[k] || orig[k] || w;
                });
            });
            e.brand.concat(e.name, e.rest).forEach(function (w) { vocab[w] = 1; });
            return e;
        });
        VOCAB = Object.keys(vocab);
    }

    function hasPrefix(list, t) {
        for (var i = 0; i < list.length; i++) if (list[i].indexOf(t) === 0) return true;
        return false;
    }

    /* запит -> слова з урахуванням словника; кожне слово: {q, any?, show, changed, fuzzy?} */
    function parse(q) {
        var raw = base(q).split(' ').filter(Boolean);
        var toks = raw.map(function (w) { return { q: phon(w), show: w, changed: false }; });
        var out = [];
        for (var i = 0; i < toks.length;) {
            var hit = null, len = 0;
            for (var L = Math.min(MAXLEN, toks.length - i); L >= 1 && !hit; L--) {
                var key = toks.slice(i, i + L).map(function (t) { return t.q; }).join(' ');
                if (ALIAS[key]) { hit = ALIAS[key]; len = L; }
            }
            if (!hit) { out.push(toks[i]); i++; continue; }
            var typed = raw.slice(i, i + len).join(' ');
            if (hit.any) {
                out.push({ any: hit.any, show: hit.show, changed: false });
            } else {
                var same = typed === base(hit.show);
                hit.q.forEach(function (w, k) {
                    out.push({ q: w, show: k === 0 ? hit.show : '', changed: !same, brand: true });
                });
            }
            i += len;
        }
        /* слово, що після нормалізації стало однією літерою («qq» -> «k»), знаходило б усе підряд — пропускаємо
           (цифри лишаються; «d&g», «лв» уже замінені словником) */
        return out.filter(function (t) { return t.any || t.brand || t.q.length > 1 || /\d/.test(t.q); });
    }

    function matchWord(e, t) {
        /* вага збігу слова t у товарі e (0 — немає) */
        if (e.code && e.code === t) return 50;
        if (e.code && /\d/.test(t) && e.code.indexOf(t) === 0) return 20;
        if (hasPrefix(e.brand, t)) return 8;
        if (hasPrefix(e.name, t)) return 5;
        if (hasPrefix(e.rest, t)) return 2;
        return 0;
    }

    function search(q) {
        var toks = parse(q);
        var res = { items: [], corrected: false, label: '' };
        if (!toks.length) return res;
        /* слова без жодного точного збігу у словнику сайту — шукаємо схожі (нечіткий пошук) */
        toks.forEach(function (t) {
            if (t.any || t.brand) return;
            var exact = variants(t.q).some(function (v) { return VOCAB.some(function (w) { return w.indexOf(v) === 0; }); });
            if (exact) return;
            var k = allowed(t.q);
            if (!k) return;
            var best = k + 1, cands = [];
            VOCAB.forEach(function (w) {
                var dist = dl(t.q, w, k);
                if (t.q.length >= 5 && w.length > t.q.length) dist = Math.min(dist, dl(t.q, w.slice(0, t.q.length), k));
                if (dist < best) { best = dist; cands = [w]; }
                else if (dist === best && dist <= k) cands.push(w);
            });
            if (cands.length) {
                t.fuzzy = cands;
                t.changed = true;
                t.show = SHOW[cands[0]] || cands[0];
            }
        });
        var scored = [];
        ITEMS.forEach(function (e) {
            var score = 0;
            for (var k = 0; k < toks.length; k++) {
                var t = toks[k], hit = 0, j;
                if (t.any) {
                    for (j = 0; j < t.any.length && !hit; j++) {
                        var ws = t.any[j].split(' '), all = 1, sum = 0;
                        ws.forEach(function (w) { var m = matchWord(e, w); if (!m) all = 0; sum += m; });
                        if (all) hit = sum;
                    }
                } else if (t.fuzzy) {
                    for (j = 0; j < t.fuzzy.length && !hit; j++) hit = matchWord(e, t.fuzzy[j]) ? 1 : 0;   // нечіткі — нижче
                } else {
                    var vs = variants(t.q);
                    for (j = 0; j < vs.length && !hit; j++) hit = matchWord(e, vs[j]);
                }
                if (!hit) return;
                score += hit;
            }
            scored.push({ e: e, s: score });
        });
        scored.sort(function (a, b) { return b.s - a.s || a.e.i - b.e.i; });   // однакова вага — новинки першими
        res.items = scored.map(function (r) { return r.e.it; });
        res.corrected = res.items.length > 0 && toks.some(function (t) { return t.changed; });
        res.label = toks.map(function (t) { return t.show; }).filter(Boolean).join(' ');
        return res;
    }

    return { setIndex: setIndex, search: search, parse: parse, phon: phon, base: base, dl: dl };
})();
if (typeof module === 'object' && module && module.exports) module.exports = SearchCore;

(function () {
    'use strict';
    if (typeof document === 'undefined') return;     // тести в Node — лише ядро

    /* корінь сайту — з адреси цього скрипта (сторінки лежать на різній глибині) */
    var me = document.currentScript && document.currentScript.src;
    var ROOT = me ? me.replace(/assets\/search\.js(\?.*)?$/, '') : '/';
    var TG = 'https://t.me/via_manager';
    var LIMIT = 8;

    var READY = false, loading = null;
    function prepIndex() { SearchCore.setIndex(window.SEARCH_INDEX || []); READY = true; }
    function loadIndex(cb) {
        if (READY) return cb();
        if (window.SEARCH_INDEX) { prepIndex(); return cb(); }
        if (!loading) {
            loading = [];
            var s = document.createElement('script');
            s.src = ROOT + 'assets/search-index.js';
            s.onload = function () { prepIndex(); loading.forEach(function (f) { f(); }); };
            s.onerror = function () { READY = true; loading.forEach(function (f) { f(); }); };
            document.head.appendChild(s);
        }
        loading.push(cb);
    }
    function search(q) { return SearchCore.search(q); }

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
    /* знайдено через виправлення написання — показуємо, що саме шукали */
    function didYouMean(r) {
        return r.corrected ? '<p class="search-fixed">Показано результати для: <b>' + esc(r.label) + '</b></p>' : '';
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
            var r = search(q);
            current = r.items;
            if (!current.length) { list.innerHTML = emptyHtml(); return; }
            var html = didYouMean(r) + '<ul class="search-list" role="listbox">';
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
        var r = search(q), found = r.items;
        if (r.corrected) status.innerHTML = '<p class="search-query">«' + esc(q) + '»</p>' + didYouMean(r);
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
