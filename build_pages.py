#!/usr/bin/env python3
"""
build_pages.py — генератор статичних сторінок товарів для via-accessories.com.ua

ЗАПУСКАТИ ПІСЛЯ КОЖНОГО ДОДАВАННЯ/ЗМІНИ ТОВАРІВ у assets/products.js, ПЕРЕД git push:

    python build_pages.py

Що робить:
  * читає assets/products.js (через Node.js — він найнадійніше розбирає JS-об'єкт);
  * створює products/<бренд>-<код>.html — по сторінці на кожен товар
    (шаблон: templates/product.tpl.html, дизайн той самий, що був у product.html);
  * робить легкі WebP-копії фото (content/optimized/) і обкладинки відео (poster) — лише для нових
    або змінених файлів; оригінали не чіпає. Для цього потрібні Pillow і ffmpeg;
  * стискає відео (H.264, ~720p, CRF 26) з content/watermarked у content/optimized/video/ — сайт бере їх звідти;
  * створює brands/<бренд>.html — сторінку кожного бренду, що має товари;
  * створює category/<відділ>.html — сторінку кожного відділу, що має товари (плитки брендів: логотип
    assets/brands/<slug бренду>.svg|.png або BRAND_LOGOS з products.js; логотипа немає — текстова плитка);
  * створює category/<відділ>/<бренд>.html — товари бренду в цьому відділі (лише пари з видимими товарами);
  * виставляє посилання на відділи/бренди в шапці, підвалах і на головній (атрибути data-dept /
    data-brand): є сторінка — веде на неї, ще немає — на catalog.html?...;
  * створює assets/product-urls.js — відповідність id товару -> адреса сторінки
    (її використовують каталог, головна, кошик і старий product.html?id=...);
  * вписує товари прямо в HTML каталогу (catalog.html) і «Хітів сезону» на головній (index.html) —
    між маркерами <!-- build:... -->, щоб пошуковик бачив посилання на товари без JavaScript;
  * додає на сторінку товару блок «Схожі товари» (той самий бренд / відділ);
  * сітки товарів (відділи, «відділ + бренд», бренди, каталог) — новинки першими (поле added) і з
    data-атрибутами (ціна, бренд, колір, дата, назва) для фільтрів і сортування (assets/filters.js);
    на сторінці відділу під плитками брендів — усі товари відділу;
  * створює assets/search-index.js (видимі товари для пошуку в шапці, assets/search.js) і search.html —
    сторінку результатів пошуку (noindex, не в sitemap);
  * створює sitemap.xml (з <lastmod>), robots.txt і feed.xml (фід товарів для Google Merchant Center).

Необов'язкові поля товару (їх ставить адмінка via-admin):
  * longDescription — довгий опис: блок «Опис» під товаром (лише якщо заповнений);
  * hit: true — «Новинка / Хіт»: товар першим потрапляє в «Хіти сезону» на головній;
  * added: "YYYY-MM-DD" — дата додавання (адмінка ставить при створенні): сортування «Новинки»;
  * hidden: true — немає в наявності: товару немає в каталозі, на сторінках бренду/відділу, у «Схожих»,
    «Хітах», sitemap.xml і feed.xml. Його сторінка лишається за тією самою адресою (без noindex) з
    позначкою «Немає в наявності», без кнопок кошика/замовлення і з availability OutOfStock у JSON-LD —
    так радить Google для тимчасово відсутніх товарів: сторінка не випадає з індексу і повертається
    з усією історією, щойно товар знову з'явиться.

Усі згенеровані файли можна безпечно перегенерувати: папки products/, brands/, category/
перед генерацією очищуються від старих *.html (щоб не лишалось сторінок видалених товарів).

Переадресації (redirects.json у корені сайту): {"стара адреса": "нова адреса"}, напр. після
перейменування бренду {"products/van-cleef-jw0104.html": "products/van-cleef-arpels-jw0104.html"}.
За старою адресою створюється сторінка-переадресація (meta refresh + canonical на нову адресу);
у sitemap.xml і feed.xml старої адреси немає.
"""
import html
import json
import shutil
import os
import re
import subprocess
import sys
import unicodedata
import urllib.parse

# ----------------------------- НАЛАШТУВАННЯ -----------------------------
SITE_URL = "https://via-accessories.com.ua"      # без слеша в кінці
AVAILABILITY = "https://schema.org/InStock"      # наявність для schema.org Offer
OUT_OF_STOCK = "https://schema.org/OutOfStock"   # для прихованих товарів (hidden: true)
                                                  # (інші варіанти: https://schema.org/PreOrder,
                                                  #  https://schema.org/OutOfStock)
CURRENCY = "UAH"
# Умови повернення (hasMerchantReturnPolicy у JSON-LD товару; назви полів — за документацією Google
# https://developers.google.com/search/docs/appearance/structured-data/return-policy).
# Має збігатися з текстом на сторінці returns.html.
RETURN_POLICY = {
    "@type": "MerchantReturnPolicy",
    "applicableCountry": "UA",
    "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
    "merchantReturnDays": 14,
    "returnMethod": "https://schema.org/ReturnByMail",
    "returnFees": "https://schema.org/ReturnFeesCustomerResponsibility",  # пересилання оплачує покупець
}
# --- фід для Google Merchant Center (feed.xml) ---
FEED_NS = "http://base.google.com/ns/1.0"
FEED_TITLE = "via.accessories"
FEED_DESCRIPTION = "Каталог товарів via.accessories: сумки та аксесуари. Доставка по Україні та Європі."
FEED_AVAILABILITY = "in_stock"       # in_stock / out_of_stock / preorder (для всіх товарів фіду)
# Окремі заголовки й атрибути для Google (feed_meta.py): g:title «Жіноча сумка Бренд Модель матеріал колір»,
# категорія за типом товару, g:color, g:material, g:gender, g:age_group. На сайт (сторінки) не впливає.
# Список заголовків погоджено (via-admin/docs/feed_titles.csv). Вимкнути — False (тоді фід як раніше).
FEED_GOOGLE_META = True
# Категорії Google Product Taxonomy за відділами сайту (https://www.google.com/basepages/producttype/taxonomy.en-US.txt)
GOOGLE_CATEGORY = {
    "bags": "Apparel & Accessories > Handbags, Wallets & Cases > Handbags",     # id 6551
    "shoes": "Apparel & Accessories > Shoes",
    "watches": "Apparel & Accessories > Jewelry > Watches",
    "jewelry": "Apparel & Accessories > Jewelry",
    "accessories": "Apparel & Accessories > Clothing Accessories",
    "eyewear": "Apparel & Accessories > Clothing Accessories > Sunglasses",
}

# Адреси сторінок відділів (латиницею): ключ відділу з products.js -> ім'я файлу в category/
DEPT_SLUGS = {
    "bags": "sumky",
    "shoes": "vzuttia",
    "watches": "hodynnyky",
    "jewelry": "prykrasy",
    "accessories": "aksesuary",
    "eyewear": "okuliary",
}
# Порядок «головних» брендів: так вони йдуть у заголовку та рядку брендів відділу.
# Бренди, яких тут немає, ставляться після них — за кількістю товарів.
BRAND_PRIORITY = ["Louis Vuitton", "Chanel", "Dior", "Hermès"]
DELIVERY_LINE = "Доставка по Україні та Європі"

# --- оптимізація зображень ---
OPT_REL = "content/optimized"        # куди кладуться WebP-копії та обкладинки відео
IMG_WIDTHS = [240, 480, 800, 1200]   # ширини копій (ширші за оригінал не створюються; оригінал — найбільший розмір)
WEBP_QUALITY = 85
POSTER_WIDTH = 720                   # ширина обкладинки відео
POSTER_AT = "1.0"                    # секунда відео, з якої береться кадр
SLIDES = ["slide1.jpg", "slide2.jpg", "slide3.jpg"]   # слайди головної (у корені)
IMG_META = {}                        # шлях до оригіналу -> {"w", "h", "s": [ширини]}
POSTER_META = {}                     # шлях до відео -> {"p": шлях до обкладинки, "w", "h"}

# --- стиснення відео (оригінали з content/watermarked лишаються на диску; сайт бере копії звідси) ---
VIDEO_REL = "content/optimized/video"
VIDEO_CRF = 26                       # менше число — краща якість і більший файл
VIDEO_PRESET = "slow"
VIDEO_AUDIO_KBPS = 96                # звук (якщо він є у відео) — AAC
VIDEO_MAX_SHORT_SIDE = 720           # коротша сторона кадру не більша за 720 px (вертикальне — до 720x1280)
VIDEO_WORKERS = 3                    # скільки відео стискається одночасно
VIDEO_OUT = {}                       # шлях до оригіналу -> шлях до стисненого відео
# sizes для <picture>: скільки місця займає картинка на екрані (щоб браузер обрав потрібну ширину)
MAIN_SIZES = "(max-width:1000px) calc(100vw - 50px), 650px"      # головне фото товару
THUMB_SIZES = "(max-width:1000px) 22vw, 150px"                     # мініатюри галереї
CARD_SIZES = "(max-width:500px) 100vw, (max-width:900px) 50vw, 25vw"   # картки в сітці 4/2/1
TILE_SIZES = "(max-width:900px) 50vw, 20vw"                        # плитки брендів на сторінці відділу
SIMILAR_COUNT = 4                    # скільки «Схожих товарів» на сторінці товару (ряд із 4 карток)
HITS_COUNT = 4                       # скільки карток у «Хітах сезону» на головній
TG_NICK = "via_manager"                                    # як у product.html / cart.js
# Сторінки сайту для sitemap (товари додаються автоматично)
STATIC_PAGES = ["", "catalog.html", "contacts.html", "delivery.html", "returns.html", "terms.html", "privacy.html"]  # "" = головна
# -------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "products")
BRANDS_DIR = os.path.join(ROOT, "brands")
CATEGORY_DIR = os.path.join(ROOT, "category")

CYR = {
    "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e", "є": "ie", "ж": "zh",
    "з": "z", "и": "y", "і": "i", "ї": "i", "й": "i", "к": "k", "л": "l", "м": "m", "н": "n",
    "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "shch", "ь": "", "ю": "iu", "я": "ia", "ы": "y", "э": "e", "ъ": "",
}


def slugify(text):
    text = text.lower()
    text = "".join(CYR.get(ch, ch) for ch in text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("&", " ")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def esc(s):
    return html.escape(str(s), quote=True)


# Контакти в тексті опису -> посилання (лише на сторінці товару; у products.js, feed.xml і JSON-LD текст не змінюється).
# @username Telegram (5-32 символи, не частина e-mail) і українські номери: +38 073 862 41 36, +380738624136,
# 380738624136, 073 862 41 36, (073) 862-41-36, 073-862-41-36, 0738624136.
_CONTACT_RX = re.compile(
    r"(?P<tg>(?<![\w@./])@[A-Za-z][A-Za-z0-9_]{4,31}(?![\w@]))"
    r"|(?P<tel>(?<![\w+])(?:\+?38[\s\-]?)?\(?0\d{2}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}(?![\w]))")


def _tel_href(raw):
    d = re.sub(r"\D", "", raw)
    if d.startswith("0") and len(d) == 10:
        d = "38" + d
    return "tel:+" + d if d.startswith("380") and len(d) == 12 else ""


def linkify(text):
    """Екранований текст опису, у якому @username і телефони - посилання (t.me / tel:)."""
    text = str(text or "")
    out, pos = [], 0
    for m in _CONTACT_RX.finditer(text):
        if m.group("tg"):
            href = "https://t.me/" + m.group("tg")[1:]
            link = '<a class="contact-link" href="%s" target="_blank" rel="noopener">%s</a>' % (esc(href), esc(m.group("tg")))
        else:
            href = _tel_href(m.group("tel"))
            if not href:
                continue
            link = '<a class="contact-link" href="%s">%s</a>' % (esc(href), esc(m.group("tel")))
        out.append(esc(text[pos:m.start()]))
        out.append(link)
        pos = m.end()
    out.append(esc(text[pos:]))
    return "".join(out)


def url_path(rel):
    """Шлях до файлу з кирилицею/пробілами -> безпечний для URL (/ лишається)."""
    return urllib.parse.quote(rel, safe="/")


def load_products():
    js = (
        "const fs=require('fs'),vm=require('vm');"
        "const c={};vm.createContext(c);"
        "vm.runInContext(fs.readFileSync(process.argv[1],'utf8')"
        "+';this.__P=PRODUCTS;this.__D=DEPARTMENTS_META;this.__L=(typeof BRAND_LOGOS===\"undefined\")?{}:BRAND_LOGOS;',c);"
        "process.stdout.write(JSON.stringify({products:c.__P,depts:c.__D,logos:c.__L}));"
    )
    try:
        out = subprocess.check_output(
            ["node", "-e", js, os.path.join(ROOT, "assets", "products.js")]
        )
    except FileNotFoundError:
        sys.exit("Помилка: не знайдено Node.js (команда 'node'). Встановіть його з https://nodejs.org")
    data = json.loads(out.decode("utf8"))
    return data["products"], data["depts"], data["logos"]


def price_number(p):
    """Число-ціна. Якщо в товарі є поле priceNum — беремо його; інакше розбираємо
    рядок виду '4200 грн'. Прочерк/порожньо/незрозуміло -> None (ціну не показуємо)."""
    if isinstance(p.get("priceNum"), (int, float)) and p["priceNum"] > 0:
        return p["priceNum"]
    s = str(p.get("price") or "").strip()
    m = re.fullmatch(r"(\d[\d\s]*)(?:[.,](\d{1,2}))?\s*(?:грн\.?|₴|uah)?", s, re.I)
    if not m:
        return None
    whole = int(re.sub(r"\s", "", m.group(1)))
    if m.group(2):
        return float("%d.%s" % (whole, m.group(2)))
    return whole if whole > 0 else None


def trim(text, limit):
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",.;:—- ")
    return cut + "…"


def make_slugs(products):
    slugs, used = {}, {}
    for pid, p in products.items():
        brand = p.get("brand") or ""
        base = slugify(brand if brand and brand != "Інше" else "tovar")
        code = slugify(str(p.get("code") or "")) or slugify(pid)
        slug = "%s-%s" % (base, code) if base else code
        if slug in used:                       # раптом збігся код — додаємо id
            slug = "%s-%s" % (slug, slugify(pid))
        used[slug] = pid
        slugs[pid] = slug
    return slugs


def opt_path(src, suffix):
    """content/watermarked/Лв 1-1.jpg + 480 -> content/optimized/Лв 1-1-480.webp"""
    stem = os.path.splitext(os.path.basename(src))[0]
    return "%s/%s-%s.webp" % (OPT_REL, stem, suffix)


def _fresh(dst, src):
    return os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src)


def optimize_images(sources):
    """WebP у кількох ширинах для кожного фото; створює лише відсутні або застарілі файли."""
    from PIL import Image, ImageOps
    os.makedirs(os.path.join(ROOT, OPT_REL), exist_ok=True)
    made = 0
    stems = {}
    for src in sources:
        stem = os.path.splitext(os.path.basename(src))[0]
        if stems.setdefault(stem, src) != src:
            sys.exit("Помилка: однакові імена файлів у різних папках: %s і %s" % (stems[stem], src))
        path = os.path.join(ROOT, src)
        with Image.open(path) as im:
            orient = im.getexif().get(0x0112, 1)
            w, h = (im.height, im.width) if orient in (5, 6, 7, 8) else (im.width, im.height)
        widths = [x for x in IMG_WIDTHS if x < w] + [w]
        IMG_META[src] = {"w": w, "h": h, "s": widths}
        todo = [x for x in widths if not _fresh(os.path.join(ROOT, opt_path(src, x)), path)]
        if not todo:
            continue
        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            for x in todo:
                out = im if x == w else im.resize((x, round(h * x / w)), Image.LANCZOS)
                out.save(os.path.join(ROOT, opt_path(src, x)), "WEBP", quality=WEBP_QUALITY, method=4)
                made += 1
    return made


def make_posters(videos):
    """Обкладинка (кадр відео) у WebP через ffmpeg; створює лише відсутні або застарілі."""
    from PIL import Image
    ffmpeg = shutil.which("ffmpeg")
    made = 0
    for v in videos:
        path = os.path.join(ROOT, v)
        rel = opt_path(v, "poster")
        dst = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            # оригіналу відео немає (напр. його прибрано з git) — лишаємо вже готову обкладинку
            if not os.path.exists(dst):
                print("Увага: немає ні відео %s, ні його обкладинки" % v)
                continue
        elif not _fresh(dst, path):
            if not ffmpeg:
                print("Увага: ffmpeg не знайдено — обкладинку для %s не створено" % v)
                continue
            cmd = [ffmpeg, "-y", "-v", "error", "-ss", POSTER_AT, "-i", path, "-frames:v", "1",
                   "-vf", "scale='min(%d,iw)':-2" % POSTER_WIDTH, "-c:v", "libwebp", "-quality", str(WEBP_QUALITY), dst]
            res = subprocess.run(cmd, capture_output=True)
            if res.returncode != 0 or not os.path.exists(dst):
                # відео коротше за POSTER_AT — беремо перший кадр
                cmd[cmd.index("-ss") + 1] = "0"
                res = subprocess.run(cmd, capture_output=True)
            if res.returncode != 0 or not os.path.exists(dst):
                print("Увага: не вдалося зробити обкладинку для %s" % v)
                continue
            made += 1
        with Image.open(dst) as im:
            POSTER_META[v] = {"p": rel, "w": im.width, "h": im.height}
    return made


def video_out_path(src):
    """content/watermarked/Лв 1-4.mp4 -> content/optimized/video/Лв 1-4.mp4 (те саме ім'я, завжди .mp4)"""
    return "%s/%s.mp4" % (VIDEO_REL, os.path.splitext(os.path.basename(src))[0])


def _compress_one(ffmpeg, ffprobe, src, dst):
    probe = subprocess.run([ffprobe, "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                            "-of", "csv=p=0", src], capture_output=True, text=True)
    has_audio = bool(probe.stdout.strip())
    short = VIDEO_MAX_SHORT_SIDE
    # коротша сторона не більша за VIDEO_MAX_SHORT_SIDE, пропорції зберігаються, збільшення немає, розміри парні
    scale = ("scale=w='if(lt(iw,ih),min(%d,iw),-2)':h='if(lt(iw,ih),-2,min(%d,ih))'" % (short, short))
    cmd = [ffmpeg, "-y", "-v", "error", "-i", src, "-map", "0:v:0"]
    if has_audio:
        cmd += ["-map", "0:a:0"]
    cmd += ["-vf", scale, "-c:v", "libx264", "-preset", VIDEO_PRESET, "-crf", str(VIDEO_CRF), "-pix_fmt", "yuv420p"]
    cmd += ["-c:a", "aac", "-b:a", "%dk" % VIDEO_AUDIO_KBPS] if has_audio else ["-an"]
    tmp = dst + ".part"
    cmd += ["-movflags", "+faststart", "-f", "mp4", tmp]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 or not os.path.exists(tmp):
        if os.path.exists(tmp):
            os.remove(tmp)
        return False, res.stderr.strip()[-300:]
    os.replace(tmp, dst)          # файл з'являється лише повністю готовим
    return True, ""


def compress_videos(videos):
    """Стискає відео (H.264/AAC) у content/optimized/video/ — лише нові або змінені.
    Повертає (скільки створено, {шлях оригіналу: шлях стисненого})."""
    from concurrent.futures import ThreadPoolExecutor
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    os.makedirs(os.path.join(ROOT, VIDEO_REL), exist_ok=True)
    out, todo, stems = {}, [], {}
    for v in videos:
        stem = os.path.splitext(os.path.basename(v))[0]
        if stems.setdefault(stem, v) != v:
            sys.exit("Помилка: однакові імена відео у різних папках: %s і %s" % (stems[stem], v))
        rel = video_out_path(v)
        src, dst = os.path.join(ROOT, v), os.path.join(ROOT, rel)
        if not os.path.exists(src):
            if os.path.exists(dst):       # оригіналу немає (прибраний з git) — лишаємо готовий стиснений
                out[v] = rel
            else:
                print("Увага: немає ні відео %s, ні його стисненої копії" % v)
            continue
        if _fresh(dst, src):
            out[v] = rel
        else:
            todo.append((v, src, dst, rel))
    if todo and not (ffmpeg and ffprobe):
        sys.exit("Помилка: не знайдено ffmpeg/ffprobe — потрібні для стиснення відео")
    made = 0
    if todo:
        print("Стискаю відео: %d шт. (може тривати кілька хвилин)..." % len(todo))
        with ThreadPoolExecutor(max_workers=VIDEO_WORKERS) as pool:
            results = list(pool.map(lambda t: _compress_one(ffmpeg, ffprobe, t[1], t[2]), todo))
        for (v, src, dst, rel), (ok, err) in zip(todo, results):
            if ok:
                out[v] = rel
                made += 1
            else:
                print("Увага: не вдалося стиснути %s: %s" % (v, err))
    return made, out


def cleanup_videos(keep_rel):
    """Видаляє зі content/optimized/video/ стиснені відео, яких більше немає в товарах."""
    keep = {os.path.basename(r) for r in keep_rel}
    removed = 0
    d = os.path.join(ROOT, VIDEO_REL)
    for fn in os.listdir(d):
        if (fn.endswith(".mp4") or fn.endswith(".part")) and fn not in keep:
            os.remove(os.path.join(d, fn))
            removed += 1
    return removed


def cleanup_optimized():
    """Видаляє зі content/optimized файли, які більше не потрібні (фото/відео видалили з товарів)."""
    keep = set()
    for src, m in IMG_META.items():
        keep.update(os.path.basename(opt_path(src, x)) for x in m["s"])
    keep.update(os.path.basename(m["p"]) for m in POSTER_META.values())
    removed = 0
    for fn in os.listdir(os.path.join(ROOT, OPT_REL)):
        if fn.endswith(".webp") and fn not in keep:
            os.remove(os.path.join(ROOT, OPT_REL, fn))
            removed += 1
    return removed


def srcset_for(src, prefix):
    m = IMG_META[src]
    return ", ".join("%s%s %dw" % (prefix, url_path(opt_path(src, x)), x) for x in m["s"])


def picture_html(src, alt, sizes, prefix, loading="lazy"):
    """<picture> з WebP (srcset) і запасним оригіналом JPG; width/height задані.
    loading: "lazy" (нижче першого екрана), "eager" (звичайна), "high" (найважливіше — LCP)."""
    attrs = {"lazy": ' loading="lazy"', "eager": "", "high": ' fetchpriority="high"'}[loading]
    decoding = "" if loading == "high" else ' decoding="async"'
    m = IMG_META.get(src)
    if not m:
        return '<img src="%s%s" alt="%s"%s>' % (prefix, url_path(src), esc(alt), attrs)
    return (
        '<picture><source type="image/webp" srcset="%s" sizes="%s">'
        '<img src="%s%s" width="%d" height="%d" alt="%s"%s%s></picture>'
        % (srcset_for(src, prefix), esc(sizes), prefix, url_path(src), m["w"], m["h"], esc(alt), attrs, decoding)
    )


def breadcrumb_jsonld(items):
    """<script> з JSON-LD BreadcrumbList; items — [(назва, повна адреса), ...]."""
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": u}
            for i, (n, u) in enumerate(items)
        ],
    }
    body = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return '<script type="application/ld+json">\n%s\n</script>' % body


def ordered_brands(brand_counts, first_seen):
    """Бренди: спочатку з BRAND_PRIORITY, далі за кількістю товарів, потім за порядком у products.js."""
    pr = {b: i for i, b in enumerate(BRAND_PRIORITY)}
    return sorted(brand_counts, key=lambda b: (pr.get(b, len(pr)), -brand_counts[b], first_seen[b]))


def join_list(items):
    """['а','б','в'] -> 'а, б та в'"""
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " та " + items[-1]


def brand_dept_phrase(dept_titles, lower):
    """Відділи бренду для підзаголовка: «Сумки та аксесуари», «Сумки, взуття та аксесуари».
    Слово «аксесуари» додається завжди, якщо окремого відділу «Аксесуари» ще немає в переліку."""
    names = [t.lower() for t in dept_titles]
    if "аксесуари" in names:
        names.remove("аксесуари")
    names.append("аксесуари")
    phrase = join_list(names)
    return phrase if lower else phrase[:1].upper() + phrase[1:]


def videos_of(p):
    """Усі відео товару: videos (нові товари), а для старих — [video]."""
    if p.get("videos"):
        return list(p["videos"])
    return [p["video"]] if p.get("video") else []


# Галерея з багатьма медіа (більше за «3 фото + 1 відео»): мініатюри переносяться (ПК) або гортаються стрічкою
# (телефон), лічильник «3 / 8», стрілки, свайп по головному фото і в лайтбоксі. Лише на таких сторінках.
MANY_MEDIA_CSS = (
    ".gallery{min-width:0}.gallery-thumbs{position:relative;max-width:100%}\n"
    ".gallery-count{position:absolute;right:12px;bottom:12px;background:rgba(28,26,23,0.62);color:#f5f1ea;font-size:11px;"
    "letter-spacing:2px;padding:5px 9px;border-radius:2px;pointer-events:none}\n"
    ".gallery-arrow{position:absolute;top:50%;transform:translateY(-50%);width:40px;height:40px;border:0;border-radius:50%;"
    "background:rgba(245,241,234,0.85);color:#1c1a17;font-size:20px;line-height:40px;cursor:pointer;opacity:0;"
    "transition:opacity 0.3s;z-index:2}\n"
    ".gallery-arrow.prev{left:12px}.gallery-arrow.next{right:12px}\n"
    ".gallery-main:hover .gallery-arrow{opacity:1}\n"
    "@media (hover:none){.gallery-arrow{display:none}}\n"
    "@media (max-width:500px){.gallery-thumbs{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;"
    "-webkit-overflow-scrolling:touch;scrollbar-width:none;gap:10px;padding-bottom:2px}"
    ".gallery-thumbs::-webkit-scrollbar{display:none}"
    ".gallery-thumbs .thumb{flex:0 0 calc((100% - 30px) / 3.4);scroll-snap-align:start}}\n"
)
MANY_MEDIA_JS = """<script>
(function () {
    var items = galleryItems, strip = galleryThumbs, th = strip.querySelectorAll('.thumb');
    if (items.length < 2) return;
    var count = document.createElement('div'); count.className = 'gallery-count';
    var prev = document.createElement('button'); prev.type = 'button'; prev.className = 'gallery-arrow prev'; prev.setAttribute('aria-label', 'Попереднє'); prev.textContent = '‹';
    var next = document.createElement('button'); next.type = 'button'; next.className = 'gallery-arrow next'; next.setAttribute('aria-label', 'Наступне'); next.textContent = '›';
    function decorate() {
        count.textContent = (currentIndex + 1) + ' / ' + items.length;
        galleryMain.appendChild(count); galleryMain.appendChild(prev); galleryMain.appendChild(next);
        var t = th[currentIndex];
        if (t && strip.scrollWidth > strip.clientWidth) strip.scrollTo({ left: t.offsetLeft - (strip.clientWidth - t.offsetWidth) / 2, behavior: 'smooth' });
    }
    var baseShow = showMain;
    showMain = function (i) { baseShow(i); decorate(); };
    function go(i) {
        i = (i + items.length) % items.length;
        for (var j = 0; j < th.length; j++) th[j].classList.toggle('active', j === i);
        currentIndex = i;
        showMain(i);
    }
    prev.addEventListener('click', function (e) { e.stopPropagation(); go(currentIndex - 1); });
    next.addEventListener('click', function (e) { e.stopPropagation(); go(currentIndex + 1); });
    function swipe(el, step) {
        var x0 = null, y0 = 0, moved = false;
        el.addEventListener('touchstart', function (e) { var t = e.touches[0]; x0 = t.clientX; y0 = t.clientY; moved = false; }, { passive: true });
        el.addEventListener('touchend', function (e) {
            if (x0 === null) return;
            var t = e.changedTouches[0], dx = t.clientX - x0, dy = t.clientY - y0;
            x0 = null;
            if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy) * 1.5) { moved = true; step(dx < 0 ? 1 : -1); }
        });
        el.addEventListener('click', function (e) { if (moved) { moved = false; e.stopImmediatePropagation(); e.preventDefault(); } }, true);
    }
    swipe(galleryMain, function (d) { go(currentIndex + d); });
    swipe(lightboxContent, function (d) { lightboxStep(d); });
    decorate();
})();
</script>
"""


# Стилі додаються на сторінку лише тоді, коли потрібні (інші сторінки лишаються без змін)
STOCK_OUT_CSS = (
    ".stock-out{display:inline-block;font-size:12px;letter-spacing:3px;text-transform:uppercase;color:#1c1a17;"
    "border:1px solid var(--color-gold);padding:10px 18px;border-radius:2px;margin:-12px 0 26px}\n"
    ".btn-cart,.btn-order{display:none}\n"
)
LONG_DESC_CSS = (
    ".long-desc{max-width:1500px;margin:0 auto;padding:0 60px 90px}\n"
    ".long-desc-inner{max-width:860px;margin:0 auto;padding-top:60px;border-top:1px solid rgba(0,0,0,0.08)}\n"
    ".long-desc h2{font-family:'Cormorant Garamond',serif;font-size:30px;font-weight:400;letter-spacing:6px;"
    "text-transform:uppercase;color:#1c1a17;text-align:center;margin-bottom:34px}\n"
    ".long-desc p{font-size:15px;font-weight:300;line-height:1.9;letter-spacing:0.5px;color:#4a443c;margin-bottom:18px}\n"
    "@media (max-width:1000px){.long-desc{padding:0 25px 60px}.long-desc-inner{padding-top:44px}}\n"
    "@media (max-width:900px){.long-desc h2{font-size:24px;letter-spacing:4px;margin-bottom:24px}}\n"
)


def long_desc_html(text):
    """Довгий опис -> <section>; абзаци — через порожній рядок, перенос рядка всередині абзацу — <br>."""
    text = (text or "").replace("\r\n", "\n").strip()
    if not text:
        return ""
    paras = [x.strip() for x in re.split(r"\n\s*\n", text) if x.strip()]
    body = "\n".join("<p>%s</p>" % "<br>".join(linkify(l.strip()) for l in para.split("\n")) for para in paras)
    return '<section class="long-desc"><div class="long-desc-inner">\n<h2>Опис</h2>\n%s\n</div></section>\n\n' % body


def dept_brand_pages_of(products):
    """(відділ, бренд) -> category/<відділ>/<бренд>.html — лише для пар, де є хоча б один видимий товар."""
    out = {}
    for p in products.values():
        b, d = p.get("brand") or "", p.get("dept") or ""
        if p.get("hidden") or not b or b == "Інше" or d not in DEPT_SLUGS:
            continue
        out[(d, b)] = "category/%s/%s.html" % (DEPT_SLUGS[d], slugify(b))
    return out


def plural_items(n):
    """1 товар, 2 товари, 5 товарів"""
    if n % 10 == 1 and n % 100 != 11:
        return "%d товар" % n
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return "%d товари" % n
    return "%d товарів" % n


def build_page(tpl, pid, p, slug, depts, brand_pages, dept_pages, similar_html="", similar_json="{}",
               dept_brand_pages=None):
    page_rel = "products/%s.html" % slug
    page_url = "%s/%s" % (SITE_URL, page_rel)
    name = p["name"]
    brand = p.get("brand") or ""
    has_brand = bool(brand) and brand != "Інше"
    dept = p.get("dept", "")
    dept_title = depts.get(dept, {}).get("title") or p.get("category") or "Каталог"
    num = price_number(p)
    price_text = (p.get("price") or "").strip() if num is not None else ""
    code = str(p.get("code") or "")
    images = p.get("images") or []
    videos = videos_of(p)
    video = videos[0] if videos else None
    # більше медіа, ніж старі «3 фото + 1 відео» — галерея з гортанням/свайпом (старі сторінки не змінюються)
    many = len(images) > 3 or len(videos) > 1
    specs = p.get("specs") or {}
    hidden = bool(p.get("hidden"))

    full_name = ("%s %s" % (brand, name)) if has_brand and brand.lower() not in name.lower() else name
    # «<Назва> | <Бренд> | via.accessories», не довше 60 символів. Задовго — без « | via.accessories»;
    # і так задовго — вкорочуємо назву й додаємо код (щоб title схожих товарів не збігались)
    brand_part = (" | %s" % brand) if has_brand else ""
    title = name + brand_part + " | via.accessories"
    if len(title) > 60:
        title = name + (brand_part or " | via.accessories")
    if len(title) > 60:
        tail = (" (код %s)" % code) if code else ""
        title = trim(name, 60 - len(brand_part or " | via.accessories") - len(tail) - 1) + tail + (brand_part or " | via.accessories")
    og_title = "%s — via.accessories" % full_name

    desc = (p.get("description") or "").strip()
    tail = []
    if code:
        tail.append("Код: %s." % code)
    if num is not None:
        tail.append("Ціна: %s." % price_text)
    meta_desc = trim(desc, 155 - len(" ".join(tail)) - 2) if desc else full_name
    meta_desc = (meta_desc + " " + " ".join(tail)).strip()

    abs_images = ["%s/%s" % (SITE_URL, url_path(i)) for i in images]
    og_image = abs_images[0] if abs_images else ""

    # --- JSON-LD ---
    ld = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": full_name,
        "description": desc or full_name,
        "sku": code or pid,
        "url": page_url,
    }
    if abs_images:
        ld["image"] = abs_images
    if has_brand:
        ld["brand"] = {"@type": "Brand", "name": brand}
    if num is not None:
        ld["offers"] = {
            "@type": "Offer",
            "price": num,
            "priceCurrency": CURRENCY,
            "availability": OUT_OF_STOCK if hidden else AVAILABILITY,
            "url": page_url,
            "hasMerchantReturnPolicy": RETURN_POLICY,
        }
    jsonld = json.dumps(ld, ensure_ascii=False, indent=2).replace("</", "<\\/")

    og_price = ""
    if num is not None:
        og_price = (
            '<meta property="product:price:amount" content="%s">\n'
            '<meta property="product:price:currency" content="%s">\n' % (num, CURRENCY)
        )

    # --- хлібні крихти: Головна › Відділ › Бренд › Назва (бренд — сторінка «відділ + бренд»);
    #     немає такої сторінки (напр. прихований товар) — Головна › Бренд › Назва ---
    crumbs = ['<a href="/">Головна</a>', '<span class="sep">›</span>']
    ld_crumbs = [("Головна", SITE_URL + "/")]
    db_page = (dept_brand_pages or {}).get((dept, brand)) if has_brand else None
    if db_page and dept in dept_pages:
        crumbs += ['<a href="../%s">%s</a>' % (dept_pages[dept], esc(dept_title)), '<span class="sep">›</span>',
                   '<a href="../%s">%s</a>' % (db_page, esc(brand)), '<span class="sep">›</span>']
        ld_crumbs += [(dept_title, "%s/%s" % (SITE_URL, dept_pages[dept])), (brand, "%s/%s" % (SITE_URL, db_page))]
    elif has_brand and brand in brand_pages:
        crumbs += ['<a href="../%s">%s</a>' % (brand_pages[brand], esc(brand)), '<span class="sep">›</span>']
        ld_crumbs.append((brand, "%s/%s" % (SITE_URL, brand_pages[brand])))
    elif dept in dept_pages:
        crumbs += ['<a href="../%s">%s</a>' % (dept_pages[dept], esc(dept_title)), '<span class="sep">›</span>']
        ld_crumbs.append((dept_title, "%s/%s" % (SITE_URL, dept_pages[dept])))
    crumbs.append('<span class="current">%s</span>' % esc(name))
    ld_crumbs.append((name, page_url))
    breadcrumb_ld = breadcrumb_jsonld(ld_crumbs)

    # --- галерея: головне фото — перше, вантажиться першим; мініатюри — маленькі WebP, lazy ---
    gallery = []
    for src in images:
        m = IMG_META.get(src)
        gallery.append({
            "type": "image", "src": "../" + url_path(src),
            "set": srcset_for(src, "../") if m else "",
            "w": m["w"] if m else 0, "h": m["h"] if m else 0,
        })
    main_media = ""
    preload = ""
    if images:
        main_media = picture_html(images[0], full_name, MAIN_SIZES, "../", "high")
        if images[0] in IMG_META:
            m = IMG_META[images[0]]
            mid = min(m["s"], key=lambda x: abs(x - 800))
            preload = (
                '<link rel="preload" as="image" type="image/webp" href="../%s" imagesrcset="%s" imagesizes="%s" fetchpriority="high">\n'
                % (url_path(opt_path(images[0], mid)), esc(srcset_for(images[0], "../")), esc(MAIN_SIZES))
            )
    thumbs = []
    for idx, src in enumerate(images):
        thumbs.append(
            '<div class="thumb%s" data-index="%d">%s</div>'
            % (" active" if idx == 0 else "", idx, picture_html(src, full_name, THUMB_SIZES, "../", "lazy"))
        )
    for v in videos:
        pm = POSTER_META.get(v)
        gallery.append({
            "type": "video", "src": "../" + url_path(VIDEO_OUT.get(v, v)),
            "poster": ("../" + url_path(pm["p"])) if pm else "",
            "w": pm["w"] if pm else 0, "h": pm["h"] if pm else 0,
        })
        if many and pm:                               # кілька відео — кожне зі своєю обкладинкою
            cover = '<img src="../%s" alt="%s" loading="lazy" decoding="async">' % (url_path(pm["p"]), esc(full_name))
        else:
            cover = picture_html(images[0], full_name, THUMB_SIZES, "../", "lazy") if images else ""
        thumbs.append('<div class="thumb video-thumb" data-index="%d">%s</div>' % (len(gallery) - 1, cover))

    price_block = '<div class="price" id="productPrice">%s</div>\n' % esc(price_text) if num is not None else ""
    extra_css = ""
    if hidden:
        price_block += '<div class="stock-out">Немає в наявності</div>\n'
        extra_css += STOCK_OUT_CSS
    if many:
        extra_css += MANY_MEDIA_CSS
    long_html = long_desc_html(p.get("longDescription") or "")
    if long_html:
        extra_css += LONG_DESC_CSS
    spec_items = "".join("<li><span>%s</span><span>%s</span></li>" % (esc(k), esc(v)) for k, v in specs.items())

    tg_code = ("(код:%s)" % code) if code else ""
    if num is not None:
        tg_price = " (%s%s)" % (price_text, (", " + tg_code) if tg_code else "")
    else:
        tg_price = (" " + tg_code) if tg_code else ""
    tg_text = "Доброго дня! Цікавить товар: %s%s" % (name, tg_price)
    tg_href = "https://t.me/%s?text=%s" % (TG_NICK, urllib.parse.quote(tg_text, safe=""))

    product_js = {
        "id": pid,
        "name": name,
        "alt": full_name,
        "code": code,
        "priceText": price_text if num is not None else "ціну уточнюйте",
        "priceNum": num if num is not None else 0,
        "images": images,
        "video": VIDEO_OUT.get(video, video),
        "gallery": gallery,
    }
    if many:
        product_js["videos"] = [VIDEO_OUT.get(v, v) for v in videos]
    product_json = json.dumps(product_js, ensure_ascii=False).replace("</", "<\\/")

    repl = {
        "TITLE": esc(title),
        "DESCRIPTION": esc(meta_desc),
        "URL": esc(page_url),
        "OG_TITLE": esc(og_title),
        "OG_IMAGE": esc(og_image),
        "OG_PRICE": og_price,
        "JSONLD": jsonld,
        "PRELOAD": preload,
        "BREADCRUMB_LD": breadcrumb_ld,
        "BREADCRUMBS": "\n".join(crumbs),
        "MAIN_MEDIA": main_media,
        "THUMBS": "".join(thumbs),
        "CATEGORY": esc(p.get("category") or dept_title),
        "NAME": esc(name),
        "PRICE_BLOCK": price_block,
        "CODE": esc(code),
        "DESCRIPTION_TEXT": linkify(desc),
        "SPECS": spec_items,
        "TG_HREF": esc(tg_href),
        "PRODUCT_JSON": product_json,
        "SIMILAR": similar_html,
        "SIMILAR_JSON": similar_json,
        "EXTRA_CSS": ('<style>\n%s</style>\n' % extra_css) if extra_css else "",
        "LONG_DESC": long_html,
        "EXTRA_JS": MANY_MEDIA_JS if many else "",
    }
    out = tpl
    for k, v in repl.items():
        out = out.replace("%%" + k + "%%", v)
    leftover = re.findall(r"%%[A-Z_]+%%", out)
    if leftover:
        raise RuntimeError("Не підставлено плейсхолдери %s у %s" % (leftover, pid))
    return out, page_url, num


NAV_LINK_RE = re.compile(r'<a href="([^"]*)" data-(dept|brand)="([^"]*)"')


FOOTER_BRANDS = 8                    # скільки брендів у підвалі (найбільше видимих товарів; далі «Всі бренди»)
ALL_BRANDS_PAGE = "brands.html"      # сторінка «Всі бренди»: плитки всіх брендів з товарами
# Навігаційні блоки ручних сторінок і шаблонів, які збірка перебудовує з видимих товарів:
# (назва, регулярний вираз «відкриття блоку», закриття, вигляд рядка)
NAV_BLOCKS = [
    ("menu-depts", r'<div class="dropdown">\r?\n', r'\r?\n[ \t]*</div>', 'a'),
    ("home-depts", r'<div class="departments-list">\r?\n', r'\r?\n[ \t]*</div>', 'a'),
    ("footer-depts", r'<h4>Відділи</h4>\s*<ul>\r?\n', r'\r?\n[ \t]*</ul>', 'li'),
    ("footer-brands", r'<h4>Бренди</h4>\s*<ul>\r?\n', r'\r?\n[ \t]*</ul>', 'li'),
]


def nav_files():
    files = [os.path.join(ROOT, f) for f in os.listdir(ROOT) if f.endswith(".html") and f != "product.html"]
    files += [os.path.join(ROOT, "templates", f) for f in os.listdir(os.path.join(ROOT, "templates")) if f.endswith(".tpl.html")]
    return files


def render_nav(nav_depts, footer_brands, depts, dept_pages, brand_pages):
    """Меню «Каталог» у шапці, відділи на головній, колонки «Відділи» і «Бренди» в підвалі — лише те, що є:
    відділи з хоча б одним видимим товаром (порядок меню), у підвалі — до FOOTER_BRANDS брендів з найбільшою
    кількістю видимих товарів (при рівності — за алфавітом) + «Всі бренди». Префікс шляху (../, /) і відступи
    кожного файлу зберігаються. Повертає кількість змінених файлів."""
    changed = 0
    for path in nav_files():
        with open(path, "rb") as f:
            raw = f.read().decode("utf8")
        new = raw
        for name, open_rx, close_rx, kind in NAV_BLOCKS:
            m = re.search("(%s)(.*?)(%s)" % (open_rx, close_rx), new, re.S)
            if not m:
                continue
            body = m.group(2)
            indent = re.match(r"[ \t]*", body).group(0)
            pm = re.search(r'href="((?:\.\./)*|/)(?:category|brands|catalog)', body)
            prefix = pm.group(1) if pm else ""
            if name == "footer-brands":
                links = [(brand_pages[b], esc(b), ' data-brand="%s"' % esc(b)) for b in footer_brands]
                links.append((ALL_BRANDS_PAGE, "Всі бренди", ""))
            else:
                links = [(dept_pages[d], esc(depts.get(d, {}).get("title", d)), ' data-dept="%s"' % d) for d in nav_depts]
            lines = []
            for href, text, data in links:
                a = '<a href="%s%s"%s>%s</a>' % (prefix, href, data, text)
                lines.append(indent + ("<li>%s</li>" % a if kind == "li" else a))
            nl = "\r\n" if "\r\n" in m.group(0) else "\n"     # стиль переносів рядків файлу (шаблони бувають з CRLF)
            new = new[:m.start(2)] + nl.join(lines) + new[m.end(2):]
        if new != raw:
            with open(path, "wb") as f:          # у бінарному режимі — щоб не змінювати переноси рядків
                f.write(new.encode("utf8"))
            changed += 1
    return changed


def sync_nav_links(brand_pages, dept_pages):
    """Ручні сторінки (шапка, підвали, головна) та шаблони містять посилання з атрибутами
    data-dept="ключ" / data-brand="Назва". Тут їх href виставляється за наявністю сторінки:
      є сторінка відділу/бренду -> category/<відділ>.html або brands/<бренд>.html;
      сторінки ще немає         -> старий фільтр catalog.html?dept=... / catalog.html?brand=...
    Префікс "../" (для сторінок у підпапках і шаблонів товарів) зберігається."""
    files = [os.path.join(ROOT, f) for f in os.listdir(ROOT) if f.endswith(".html") and f != "product.html"]
    files += [os.path.join(ROOT, "templates", f) for f in os.listdir(os.path.join(ROOT, "templates")) if f.endswith(".tpl.html")]
    changed = 0

    def fix(m):
        href, kind, value = m.group(1), m.group(2), m.group(3)
        prefix = "../" if href.startswith("../") else "/" if href.startswith("/") else ""
        name = html.unescape(value)                 # «Dolce &amp; Gabbana» в атрибуті -> «Dolce & Gabbana»
        if kind == "dept":
            target = dept_pages.get(name) or "catalog.html?dept=%s" % urllib.parse.quote(name)
        else:
            target = brand_pages.get(name) or "catalog.html?brand=%s" % urllib.parse.quote(name)
        return '<a href="%s%s" data-%s="%s"' % (prefix, target, kind, value)

    for path in files:
        with open(path, "rb") as f:
            raw = f.read().decode("utf8")
        new = NAV_LINK_RE.sub(fix, raw)
        if new != raw:
            with open(path, "wb") as f:      # у бінарному режимі — щоб не змінювати переноси рядків
                f.write(new.encode("utf8"))
            changed += 1
    return changed


PIC_HELPER_JS = r"""/* <picture> з WebP (srcset) і запасним JPG — для сторінок, де картки малює JS (каталог, головна, кошик) */
function picHtml(src, alt, sizes, eager, cls) {
    var m = IMG_META[src];
    var a = String(alt || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
    if (!m) return '<img src="' + src + '" alt="' + a + '">';
    var base = src.split('/').pop().replace(/\.[^.]+$/, '');
    var set = m[2].map(function (w) {
        return encodeURI('content/optimized/' + base + '-' + w + '.webp') + ' ' + w + 'w';
    }).join(', ');
    return '<picture><source type="image/webp" srcset="' + set + '" sizes="' + sizes + '">' +
        '<img' + (cls ? ' class="' + cls + '"' : '') + ' src="' + encodeURI(src) + '" width="' + m[0] + '" height="' + m[1] + '" alt="' + a + '"' +
        (eager ? ' fetchpriority="high"' : ' loading="lazy"') + ' decoding="async"></picture>';
}
"""


CARD_META = {}                      # id -> дані для фільтрів/сортування (data-атрибути картки), див. card_meta()
FILTER_FACETS_ALL = "brand,price,color"      # відділи, каталог, пошук
FILTER_FACETS_BRAND = "price,color"          # сторінка бренду / «відділ + бренд»: бренд уже обрано


def card_meta(products, depts):
    """Дані картки для фільтрів і сортування: ціна, бренд, колір (з характеристики «Колір» або з назви —
    той самий розбір, що й у feed_meta.py), дата додавання, назва."""
    fm = load_feed_meta()
    out = {}
    for pid, p in products.items():
        brand = p.get("brand") or ""
        if brand == "Інше":
            brand = ""
        num = price_number(p)
        color = fm.final(p, depts.get(p.get("dept"), {}).get("title", "")).get("color") or ""
        out[pid] = {
            "price": ("%g" % num) if num is not None else "",
            "brand": slugify(brand) if brand else "", "brand-name": brand,
            "color": slugify(color) if color else "", "color-name": color,
            "added": p.get("added") or "", "name": p.get("name") or "",
        }
    return out


def kept_pages(brand_pages, dept_pages):
    """Сторінки брендів і відділів, що вже лежать на диску, хоча товарів для них не стало зовсім (усі видалено).
    Адреси не зникають: збірка пише за ними «Скоро в наявності». Повертає ({бренд: адреса}, [ключ відділу]).
    Сторінки-переадресації (redirects.json) не чіпаємо."""
    redirects = set(load_redirects())
    brands = {}
    if os.path.isdir(BRANDS_DIR):
        known = set(brand_pages.values())
        for fn in sorted(os.listdir(BRANDS_DIR)):
            rel = "brands/" + fn
            if not fn.endswith(".html") or rel in known or rel in redirects:
                continue
            with open(os.path.join(BRANDS_DIR, fn), encoding="utf8") as f:
                m = re.search(r"<h1>(.*?)</h1>", f.read(), re.S)
            if m:
                brands[html.unescape(m.group(1)).strip()] = rel
    by_slug = {v: k for k, v in DEPT_SLUGS.items()}
    kept = []
    if os.path.isdir(CATEGORY_DIR):
        for fn in sorted(os.listdir(CATEGORY_DIR)):
            d = by_slug.get(fn[:-5]) if fn.endswith(".html") else None
            if d and d not in dept_pages and "category/" + fn not in redirects:
                kept.append(d)
    return brands, kept


COMING_SOON_HTML = (
    '<div class="coming-soon">\n<p class="coming-soon-title">Скоро в наявності</p>\n'
    '<p>Зараз тут немає товарів. Напишіть нам — підкажемо, коли з’являться, або підберемо схоже.</p>\n'
    '<div class="search-empty-links"><a href="%scatalog.html">Перейти в каталог</a>'
    '<a href="https://t.me/%s" target="_blank" rel="noopener">Telegram @%s</a></div>\n</div>\n'
)


def coming_soon_page(ltpl, rel, h1, crumbs, ld_crumbs, slugs, full_names):
    """Бренд / відділ без видимих товарів: «Скоро в наявності» + каталог і Telegram; noindex, не в sitemap.
    Щойно товар з'явиться, наступна збірка зробить звичайну сторінку за тією самою адресою."""
    prefix = "../" * rel.count("/")
    page, _ = build_listing(
        ltpl, rel, h1, "", "", "%s — скоро в наявності | via.accessories" % h1,
        "%s: товари скоро з’являться. Каталог via.accessories і консультація в Telegram." % h1,
        crumbs, ld_crumbs, [], slugs, full_names,
        grid=COMING_SOON_HTML % (prefix, TG_NICK, TG_NICK),
    )
    return page.replace('<link rel="canonical"', '<meta name="robots" content="noindex, follow">\n<link rel="canonical"', 1)


def search_index_js(visible, slugs, depts):
    """assets/search-index.js — компактні дані видимих товарів для пошуку в шапці (assets/search.js).
    Тип товару — українською і англійською зі словника feed_meta.py (сумка/bag/handbag…), щоб «браслет»
    і «bracelet» знаходили те саме. Приховані товари сюди не потрапляють."""
    fm = load_feed_meta()
    en_by_uk = {}
    for word, (uk, _, _) in fm._T.items():
        if " " in word or word in getattr(fm, "KEEP_IN_MODEL", ()):   # «wallet on chain», «woc» — не загальний тип
            continue
        en_by_uk.setdefault(uk, []).append(word)
    rows = []
    for pid, p in newest_first(visible.items()):
        dept_title = depts.get(p.get("dept"), {}).get("title", "")
        info = fm.final(p, dept_title)
        types = [info["type"]] + en_by_uk.get(info["type"], []) + [dept_title]
        num = price_number(p)
        img = (p.get("images") or [""])[0]
        m = CARD_META.get(pid, {})
        row = {
            "u": "products/%s.html" % slugs[pid], "id": pid, "n": p.get("name") or "",
            "b": "" if (p.get("brand") or "") == "Інше" else (p.get("brand") or ""),
            "c": str(p.get("code") or ""), "t": " ".join(dict.fromkeys(t for t in types if t)),
            "p": (p.get("price") or "").strip() if num is not None else "", "pn": num if num is not None else 0,
            "i": img, "a": p.get("added") or "", "co": m.get("color-name", ""),
            "bs": m.get("brand", ""), "cs": m.get("color", ""),     # ті самі ключі, що в data-атрибутах карток
        }
        if img in IMG_META:
            row["wh"] = [IMG_META[img]["w"], IMG_META[img]["h"]]
            row["ws"] = IMG_META[img]["s"]
        rows.append(row)
    return ("/* Згенеровано build_pages.py — індекс пошуку (видимі товари, новинки першими). Не редагувати. */\n"
            "var SEARCH_INDEX = %s;\n" % json.dumps(rows, ensure_ascii=False, separators=(",", ":")))


def newest_first(items):
    """Новинки першими (поле added; однакові дати — у порядку products.js). Так статична сітка вже
    відсортована «Новинки» — JS нічого не переставляє при завантаженні."""
    return sorted(items, key=lambda it: it[1].get("added") or "", reverse=True)


def filter_root(inner, facets):
    """Обгортка, яку знаходить assets/filters.js: картки з data-атрибутами всередині; без JS — просто сітка."""
    return '<div class="filter-root" data-filter-root data-facets="%s">\n%s</div>\n' % (facets, inner)


def card_html(pid, p, slug, full_name, loading="lazy", prefix="../", data=False):
    """Картка товару, як у каталозі; посилання прямо в HTML. prefix — шлях до кореня сайту.
    data=True — з data-атрибутами для фільтрів і сортування (сітки сторінок списків і каталогу)."""
    attrs = ""
    if data and pid in CARD_META:
        attrs = "".join(' data-%s="%s"' % (k, esc(v)) for k, v in CARD_META[pid].items())
    href = "%sproducts/%s.html" % (prefix, slug)
    img = picture_html(p["images"][0], full_name, CARD_SIZES, prefix, loading) if p.get("images") else ""
    code = str(p.get("code") or "")
    num = price_number(p)
    price = '<div class="price">%s</div>' % esc((p.get("price") or "").strip()) if num is not None else ""
    code_html = '<div class="code">%s</div>' % esc(code) if code else ""
    return (
        '<div class="card"%s>'
        '<a href="%s" style="display:block;text-decoration:none;color:inherit;">'
        '<div class="card-image">%s</div></a>'
        '<div class="card-caption"><a href="%s" style="text-decoration:none;color:inherit;">'
        '<div class="name">%s</div>%s%s</a>'
        '<button class="add-to-cart" type="button" data-id="%s">У кошик</button></div></div>'
        % (attrs, href, img, href, esc(p["name"]), price, code_html, esc(pid))
    )


def listing_items_json(items):
    data = {}
    for pid, p in items:
        num = price_number(p)
        data[pid] = {
            "id": pid,
            "name": p["name"],
            "price": (p.get("price") or "").strip() if num is not None else "ціну уточнюйте",
            "code": str(p.get("code") or ""),
            "priceNum": num if num is not None else 0,
            "img": (p.get("images") or [""])[0],
        }
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def build_listing(tpl, rel, h1, subtitle, brands_line, title, description, crumbs, ld_crumbs, items, slugs, full_names,
                  brand_tiles="", grid=None, facets=FILTER_FACETS_ALL, tiles_heading=""):
    """grid — готовий HTML замість звичайної сітки (сторінка бренду з групами за відділами).
    Відносні шляхи шаблону (../) переписуються під глибину сторінки: корінь (search.html) — без ../,
    підпапка другого рівня (category/<відділ>/<бренд>.html) — ../../
    Сітка товарів обгорнута в filter-root (фільтри і сортування, assets/filters.js); facets — які фільтри.
    brand_tiles (сторінка відділу) — плитки брендів, під ними заголовок tiles_heading і всі товари відділу."""
    url = "%s/%s" % (SITE_URL, rel)
    depth = rel.count("/")
    prefix = "../" * depth
    if depth != 1:
        tpl = re.sub(r'(href|src)="\.\./', lambda m: '%s="%s' % (m.group(1), prefix), tpl)
    first = items[0][1] if items else {}
    og_image = ("%s/%s" % (SITE_URL, url_path(first["images"][0]))) if first.get("images") else ""
    items = newest_first(items)
    # найперша картка (LCP) — з високим пріоритетом і без lazy; решта — lazy (ті, що вже на екрані, браузер все одно вантажить одразу)
    cards = "\n".join(
        card_html(pid, p, slugs[pid], full_names[pid], "high" if i == 0 and not brand_tiles else "lazy", prefix, True)
        for i, (pid, p) in enumerate(items)
    )
    if grid is None and items:
        grid = '<div class="grid">\n%s\n</div>\n' % cards
    if brand_tiles and tiles_heading and grid:
        brand_tiles += '<h2 class="listing-h2">%s</h2>\n' % esc(tiles_heading)
    ld = breadcrumb_jsonld(ld_crumbs)
    ld_body = ld.split("\n", 1)[1].rsplit("\n", 1)[0]
    repl = {
        "TITLE": esc(title),
        "DESCRIPTION": esc(description),
        "URL": esc(url),
        "OG_TITLE": esc(title),
        "OG_IMAGE": esc(og_image),
        "JSONLD": ld_body,
        "BREADCRUMBS": "\n".join(crumbs),
        "H1": esc(h1),
        "SUBTITLE_BLOCK": ('<div class="subtitle">%s</div>\n' % esc(subtitle)) if subtitle else "",
        "BRANDS_LINE": brands_line,
        "BRAND_TILES": brand_tiles,
        "GRID": filter_root(grid, facets) if grid else "",
        "ITEMS_JSON": listing_items_json(items),
    }
    out = tpl
    for k, v in repl.items():
        out = out.replace("%%" + k + "%%", v)
    leftover = re.findall(r"%%[A-Z_]+%%", out)
    if leftover:
        raise RuntimeError("Не підставлено плейсхолдери %s у %s" % (leftover, rel))
    return out, url


BRAND_FILTER_JS = """<script>
/* Перемикачі відділів на сторінці бренду. Без JS видно всі секції, а перемикачі — звичайні якорі. */
(function () {
    var bar = document.querySelector('.dept-filter');
    if (!bar) return;
    var links = bar.querySelectorAll('a'), secs = document.querySelectorAll('.dept-section');
    function apply(f) {
        for (var i = 0; i < links.length; i++) links[i].classList.toggle('active', links[i].getAttribute('data-filter') === f);
        for (var j = 0; j < secs.length; j++) secs[j].hidden = !!f && secs[j].id !== f;
    }
    bar.addEventListener('click', function (e) {
        var a = e.target.closest('a');
        if (!a) return;
        e.preventDefault();
        var f = a.getAttribute('data-filter');
        apply(f);
        history.replaceState(null, '', f ? '#' + f : location.pathname + location.search);
    });
    var h = location.hash.slice(1);
    if (h && document.getElementById(h) && bar.querySelector('[data-filter="' + h + '"]')) apply(h);
})();
</script>
"""


def brand_sections_html(brand, items, depts, dept_brand_pages, slugs, full_names):
    """Сторінка бренду: товари згруповані за відділами (порядок — як у меню сайту, DEPT_SLUGS).
    Над групами — перемикачі «Усі / Сумки / …» (якщо відділів більше одного)."""
    order = list(DEPT_SLUGS) + sorted({p.get("dept") or "" for _, p in items} - set(DEPT_SLUGS))
    groups = [(d, newest_first([it for it in items if (it[1].get("dept") or "") == d])) for d in order]
    groups = [(d, g) for d, g in groups if g]
    if not groups:
        return None
    out, n = [], 0
    if len(groups) > 1:
        links = ['<a href="#" class="active" data-filter="">Усі</a>']
        for d, _ in groups:
            sid = DEPT_SLUGS.get(d) or "dept-%s" % slugify(d or "inshe")
            links.append('<a href="#%s" data-filter="%s">%s</a>' % (sid, sid, esc(depts.get(d, {}).get("title", d))))
        out.append('<nav class="dept-filter" aria-label="Відділи">\n%s\n</nav>' % "\n".join(links))
    for d, g in groups:
        sid = DEPT_SLUGS.get(d) or "dept-%s" % slugify(d or "inshe")
        dtitle = depts.get(d, {}).get("title", d)
        cards = []
        for pid, p in g:
            cards.append(card_html(pid, p, slugs[pid], full_names[pid], "high" if n == 0 else "lazy", "../", True))
            n += 1
        more = ""
        page = dept_brand_pages.get((d, brand))
        if page:
            what = "усе взуття" if d == "shoes" else "усі %s" % dtitle.lower()
            more = '<div class="dept-more"><a href="../%s">Дивитись %s %s</a></div>\n' % (page, esc(what), esc(brand))
        out.append(
            '<section class="dept-section" id="%s">\n<h2>%s</h2>\n<div class="grid">\n%s\n</div>\n%s</section>'
            % (sid, esc(dtitle), "\n".join(cards), more)
        )
    return "\n".join(out) + "\n" + (BRAND_FILTER_JS if len(groups) > 1 else "")


LOGO_DIR = "assets/brands"     # логотипи брендів: assets/brands/<slug бренду>.svg або .png (напр. gucci.png)


def brand_logo(brand, logos):
    """Логотип бренду: файл assets/brands/<slug>.svg|.png, інакше BRAND_LOGOS з products.js; немає — None."""
    for ext in ("svg", "png"):
        rel = "%s/%s.%s" % (LOGO_DIR, slugify(brand), ext)
        if os.path.exists(os.path.join(ROOT, rel)):
            return rel
    return logos.get(brand) or None


def brand_tiles_html(brands, brand_pages, logos, items, prefix="../", counts=None):
    """Плитки брендів (сторінка відділу, «Всі бренди»): логотип, а якщо логотипа немає — текстова плитка
    з назвою бренду (фото товару на плитку не ставимо).
    brand_pages — куди веде плитка (на сторінці відділу — сторінки «відділ + бренд»);
    prefix — шлях до кореня сайту; counts — {бренд: кількість товарів} для підпису під назвою."""
    tiles = []
    for i, b in enumerate(brands):
        logo = brand_logo(b, logos)
        if logo:
            inner = '<div class="brand-tile-image is-logo">%s</div>' % picture_html(
                logo, b, TILE_SIZES, prefix, "eager" if i < 5 else "lazy")
        else:
            inner = '<div class="brand-tile-image is-text"><span class="brand-tile-word">%s</span></div>' % esc(b)
        count = ('<div class="brand-tile-count">%s</div>' % plural_items(counts[b])) if counts else ""
        tiles.append(
            '<a class="brand-tile" href="%s%s">%s<div class="brand-tile-name">%s</div>%s</a>'
            % (prefix, brand_pages[b], inner, esc(b), count)
        )
    if not tiles:
        return ""
    return '<div class="brand-grid brand-tiles">\n%s\n</div>\n' % "\n".join(tiles)


def similar_items(pid, products, limit=SIMILAR_COUNT):
    """Схожі товари: спершу того ж бренду, потім того ж відділу, потім будь-які.
    Беремо ті, що йдуть після поточного (по колу) — так посилання розподіляються по всьому каталогу."""
    ids = list(products)
    i = ids.index(pid)
    ring = [x for x in ids[i + 1:] + ids[:i] if not products[x].get("hidden")]
    p = products[pid]
    brand, dept = p.get("brand") or "", p.get("dept") or ""
    groups = [
        [x for x in ring if brand and brand != "Інше" and products[x].get("brand") == brand],
        [x for x in ring if products[x].get("dept") == dept],
        ring,
    ]
    out = []
    for g in groups:
        for x in g:
            if x not in out and len(out) < limit:
                out.append(x)
    return out


def similar_block(pid, products, slugs, full_names):
    ids = similar_items(pid, products)
    if not ids:
        return "", "{}"
    cards = "\n".join(card_html(x, products[x], slugs[x], full_names[x], "lazy") for x in ids)
    block = '<section class="similar">\n<h2>Схожі товари</h2>\n<div class="grid">\n%s\n</div>\n</section>\n\n' % cards
    return block, listing_items_json([(x, products[x]) for x in ids])


def pick_hits(products, limit=HITS_COUNT):
    """Хіти сезону — як було в JS на головній: по одному товару з різних брендів, далі доповнюємо будь-якими."""
    seen, picked = set(), []
    for pid, p in products.items():               # «Новинка / Хіт» з адмінки — першими
        if p.get("hit") and len(picked) < limit:
            seen.add(p.get("brand") or p.get("category"))
            picked.append(pid)
    for pid, p in products.items():
        if pid in picked:
            continue
        key = p.get("brand") or p.get("category")
        if key not in seen and len(picked) < limit:
            seen.add(key)
            picked.append(pid)
    for pid in products:
        if len(picked) >= limit:
            break
        if pid not in picked:
            picked.append(pid)
    return picked


def hit_card_html(pid, p, slug, full_name):
    img = picture_html(p["images"][0], full_name, CARD_SIZES, "", "lazy") if p.get("images") else ""
    return (
        '<a href="products/%s.html" class="hit-card">'
        '<div class="hit-card-image"><span class="hit-badge">Хіт</span>%s</div>'
        '<div class="hit-card-caption"><div class="name">%s</div><div class="price">%s</div></div></a>'
        % (slug, img, esc(p["name"]), esc((p.get("price") or "").strip()))
    )


def inject(rel, name, content):
    """Вставляє згенерований HTML між <!-- build:NAME ... --> і <!-- /build:NAME --> у ручній сторінці."""
    path = os.path.join(ROOT, rel)
    with open(path, "rb") as f:
        raw = f.read().decode("utf8")
    rx = re.compile(r"(<!-- build:%s(?: [^>]*)? -->\n).*?(<!-- /build:%s -->)" % (re.escape(name), re.escape(name)), re.S)
    if not rx.search(raw):
        sys.exit("Помилка: у %s немає маркерів <!-- build:%s -->" % (rel, name))
    new = rx.sub(lambda m: m.group(1) + content + m.group(2), raw, count=1)
    if new != raw:
        with open(path, "wb") as f:      # у бінарному режимі — щоб не змінювати переноси рядків
            f.write(new.encode("utf8"))


def lastmod_dates(rels):
    """Дата останньої зміни сторінки для sitemap: змінена/нова (ще не в коміті) — сьогодні,
    інакше дата останнього коміту файлу в git; без git — дата файлу."""
    import datetime
    today = datetime.date.today().isoformat()
    dirty = None
    try:
        st = subprocess.run(["git", "status", "--porcelain", "-z", "--untracked-files=all"], cwd=ROOT,
                            capture_output=True, check=True).stdout.decode("utf8")
        dirty = {e[3:] for e in st.split("\0") if len(e) > 3}
    except (OSError, subprocess.CalledProcessError):
        pass
    out = {}
    for rel in rels:
        d = None
        if dirty is not None and rel not in dirty:
            r = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel], cwd=ROOT, capture_output=True)
            d = r.stdout.decode("utf8").strip() or None
        if d is None:
            if dirty is not None:
                d = today
            else:
                d = datetime.date.fromtimestamp(os.path.getmtime(os.path.join(ROOT, rel))).isoformat()
        out[rel] = d
    return out


def clean_dir(path, subdirs=False):
    """Видаляє старі *.html; subdirs=True — і в підпапках (category/<відділ>/), порожні підпапки прибирає."""
    os.makedirs(path, exist_ok=True)
    for fn in os.listdir(path):
        full = os.path.join(path, fn)
        if fn.endswith(".html") and os.path.isfile(full):
            os.remove(full)
        elif subdirs and os.path.isdir(full):
            clean_dir(full)
            if not os.listdir(full):
                os.rmdir(full)


REDIRECTS_FILE = "redirects.json"


def load_redirects():
    path = os.path.join(ROOT, REDIRECTS_FILE)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf8") as f:
        return json.load(f)


def redirect_html(old_rel, new_rel):
    """Сторінка-переадресація: одразу веде на нову адресу; canonical — нова адреса."""
    href = os.path.relpath(new_rel, os.path.dirname(old_rel) or ".").replace(os.sep, "/")
    url = "%s/%s" % (SITE_URL, url_path(new_rel))
    return (
        '<!DOCTYPE html>\n<html lang="uk">\n<head>\n<meta charset="UTF-8">\n'
        '<title>Сторінку перенесено | via.accessories</title>\n'
        '<link rel="canonical" href="%s">\n'
        '<meta http-equiv="refresh" content="0; url=%s">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<script>location.replace(%s + location.search + location.hash);</script>\n'
        '</head>\n<body>\n<p>Сторінку перенесено: <a href="%s">%s</a></p>\n</body>\n</html>\n'
        % (esc(url), esc(url_path(href)), json.dumps(url_path(href)), esc(url_path(href)), esc(url))
    )


def write_redirects(generated):
    """Пише сторінки-переадресації; адресу, за якою вже є справжня сторінка, не чіпає."""
    made = []
    for old, new in load_redirects().items():
        if old in generated:
            print("Увага: переадресацію %s пропущено — за цією адресою вже є сторінка" % old)
            continue
        if new not in generated:
            print("Увага: переадресація %s -> %s: нової сторінки немає" % (old, new))
            continue
        os.makedirs(os.path.dirname(os.path.join(ROOT, old)) or ROOT, exist_ok=True)
        write(os.path.join(ROOT, old), redirect_html(old, new))
        made.append(old)
    return made


def full_name_of(p):
    brand = p.get("brand") or ""
    has_brand = bool(brand) and brand != "Інше"
    return ("%s %s" % (brand, p["name"])) if has_brand and brand.lower() not in p["name"].lower() else p["name"]


def write(path, text):
    with open(path, "w", encoding="utf8", newline="\n") as f:
        f.write(text)


def load_feed_meta():
    """feed_meta.py поруч із цим файлом (працює і коли build_pages.py імпортує адмінка)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("feed_meta", os.path.join(ROOT, "feed_meta.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_feed(products, slugs, depts):
    """feed.xml для Google Merchant Center (RSS 2.0 + g:). Один item на кожну сторінку товару;
    дані ті самі, що й на сторінках (products.js), тому фід і сайт не розходяться.
    Товар без ціни/фото у фід не потрапляє (Merchant такі відхиляє). Повертає (кількість item, пропущені)."""
    import xml.etree.ElementTree as ET
    ET.register_namespace("g", FEED_NS)
    g = lambda tag: "{%s}%s" % (FEED_NS, tag)
    rss = ET.Element("rss", {"version": "2.0"})
    ch = ET.SubElement(rss, "channel")
    ET.SubElement(ch, "title").text = FEED_TITLE
    ET.SubElement(ch, "link").text = SITE_URL
    ET.SubElement(ch, "description").text = FEED_DESCRIPTION
    count, skipped = 0, []
    fm = load_feed_meta() if FEED_GOOGLE_META else None
    for pid, p in products.items():
        num = price_number(p)
        images = p.get("images") or []
        if num is None or not images:
            skipped.append(pid)
            continue
        brand = p.get("brand") or ""
        has_brand = bool(brand) and brand != "Інше"
        dept = p.get("dept") or ""
        dept_title = depts.get(dept, {}).get("title") or p.get("category") or dept
        meta = fm.final(p, dept_title) if fm else None
        it = ET.SubElement(ch, "item")
        ET.SubElement(it, g("id")).text = slugs[pid]
        ET.SubElement(it, g("title")).text = meta["title"] if meta else trim(full_name_of(p), 150)
        ET.SubElement(it, g("description")).text = trim(re.sub(r"<[^>]+>", " ", p.get("description") or full_name_of(p)), 5000)
        ET.SubElement(it, g("link")).text = "%s/products/%s.html" % (SITE_URL, slugs[pid])
        ET.SubElement(it, g("image_link")).text = "%s/%s" % (SITE_URL, url_path(images[0]))
        for extra in images[1:11]:
            ET.SubElement(it, g("additional_image_link")).text = "%s/%s" % (SITE_URL, url_path(extra))
        ET.SubElement(it, g("availability")).text = FEED_AVAILABILITY
        ET.SubElement(it, g("price")).text = "%.2f %s" % (num, CURRENCY)
        if has_brand:
            ET.SubElement(it, g("brand")).text = brand
        ET.SubElement(it, g("condition")).text = "new"
        ET.SubElement(it, g("identifier_exists")).text = "no"
        cat = meta["category"] if meta else GOOGLE_CATEGORY.get(dept)
        if cat:
            ET.SubElement(it, g("google_product_category")).text = cat
        ET.SubElement(it, g("product_type")).text = ("%s > %s" % (dept_title, brand)) if has_brand else dept_title
        if meta:                                       # атрибути з feed_meta.py (невідомі — не вигадуємо)
            if meta["color"]:
                ET.SubElement(it, g("color")).text = meta["color"]
            if meta["material"]:
                ET.SubElement(it, g("material")).text = meta["material"]
            ET.SubElement(it, g("gender")).text = meta["gender"]
            ET.SubElement(it, g("age_group")).text = "adult"
        count += 1
    ET.indent(rss, space="  ")
    data = ET.tostring(rss, encoding="utf-8", xml_declaration=True)     # байти, переноси рядків завжди LF
    with open(os.path.join(ROOT, "feed.xml"), "wb") as f:
        f.write(data + b"\n")
    return count, skipped


def main():
    products, depts, logos = load_products()
    slugs = make_slugs(products)
    # приховані (немає в наявності): сторінка є, але в списках, sitemap і фіді їх немає
    visible = {pid: p for pid, p in products.items() if not p.get("hidden")}
    with open(os.path.join(ROOT, "templates", "product.tpl.html"), encoding="utf8") as f:
        tpl = f.read()

    # --- які бренди та відділи мають товари ---
    brand_counts, first_seen, brand_depts, dept_brand_counts = {}, {}, {}, {}
    for pid, p in products.items():
        b, d = p.get("brand") or "", p.get("dept") or ""
        if b and b != "Інше":
            brand_counts[b] = brand_counts.get(b, 0) + 1
            first_seen.setdefault(b, len(first_seen))
            if d not in brand_depts.setdefault(b, []):
                brand_depts[b].append(d)
            if pid in visible:
                dept_brand_counts.setdefault(d, {})
                dept_brand_counts[d][b] = dept_brand_counts[d].get(b, 0) + 1
    brand_pages = {b: "brands/%s.html" % slugify(b) for b in brand_counts}
    used_depts = [d for d in DEPT_SLUGS if any(p.get("dept") == d for p in products.values())]
    dept_pages = {d: "category/%s.html" % DEPT_SLUGS[d] for d in used_depts}
    dept_brand_pages = dept_brand_pages_of(products)
    for d in {p.get("dept") for p in products.values()} - set(DEPT_SLUGS):
        print("Увага: відділ '%s' немає в DEPT_SLUGS — сторінку відділу не створено" % d)

    # --- що реально є на сайті (видимі товари): відділи в меню, бренди в підвалі, «Всі бренди» ---
    vis_brand_counts = {}
    for p in visible.values():
        b = p.get("brand") or ""
        if b and b != "Інше":
            vis_brand_counts[b] = vis_brand_counts.get(b, 0) + 1
    nav_depts = [d for d in used_depts if any(p.get("dept") == d for p in visible.values())]
    brands_by_count = sorted(vis_brand_counts, key=lambda b: (-vis_brand_counts[b], b.casefold()))
    footer_brands = brands_by_count[:FOOTER_BRANDS]
    # сторінки бренду/відділу, які вже є на диску, але товарів для них не стало зовсім: адресу не видаляємо —
    # лишається сторінка «Скоро в наявності» (noindex, не в sitemap)
    kept_brands, kept_depts = kept_pages(brand_pages, dept_pages)
    brand_pages.update(kept_brands)

    # --- WebP-копії фото та обкладинки відео (лише нові/змінені) ---
    photo_sources = []
    for p in products.values():
        photo_sources += [i for i in (p.get("images") or []) if i not in photo_sources]
    photo_sources += [l for l in logos.values() if l not in photo_sources]
    photo_sources += [sl for sl in SLIDES if os.path.exists(os.path.join(ROOT, sl))]
    videos = sorted({v for p in products.values() for v in videos_of(p)})
    made_img = optimize_images(photo_sources)
    made_poster = make_posters(videos)
    made_video, video_out = compress_videos(videos)
    VIDEO_OUT.update(video_out)
    removed_opt = cleanup_optimized() + cleanup_videos(video_out.values())

    # меню, відділи на головній і підвал — лише те, що є; решта посилань data-dept/data-brand -> сторінки
    nav_changed = render_nav(nav_depts, footer_brands, depts, dept_pages, brand_pages)
    nav_changed += sync_nav_links(brand_pages, dept_pages)
    with open(os.path.join(ROOT, "templates", "product.tpl.html"), encoding="utf8") as f:
        tpl = f.read()

    clean_dir(OUT_DIR)
    clean_dir(BRANDS_DIR)
    clean_dir(CATEGORY_DIR, subdirs=True)
    full_names = {pid: full_name_of(p) for pid, p in products.items()}
    CARD_META.clear()
    CARD_META.update(card_meta(visible, depts))

    urls, priced = [], 0
    for pid, p in products.items():
        sim_html, sim_json = similar_block(pid, products, slugs, full_names)
        page, page_url, num = build_page(tpl, pid, p, slugs[pid], depts, brand_pages, dept_pages, sim_html, sim_json,
                                    dept_brand_pages)
        write(os.path.join(OUT_DIR, slugs[pid] + ".html"), page)
        if pid in visible:
            urls.append(page_url)
        priced += 1 if num is not None else 0

    with open(os.path.join(ROOT, "templates", "listing.tpl.html"), encoding="utf8") as f:
        ltpl = f.read()
    listing_urls = []
    home = ("Головна", SITE_URL + "/")
    home_link = '<a href="/">Головна</a><span class="sep">›</span>'

    # --- сторінки брендів (немає видимих товарів — «Скоро в наявності», noindex, не в sitemap) ---
    for brand in ordered_brands(brand_counts, first_seen) + sorted(kept_brands):
        items = [(pid, p) for pid, p in visible.items() if p.get("brand") == brand]
        rel = brand_pages[brand]
        if not items:
            write(os.path.join(ROOT, rel), coming_soon_page(
                ltpl, rel, brand, [home_link, '<span class="current">%s</span>' % esc(brand)],
                [home, (brand, "%s/%s" % (SITE_URL, rel))], slugs, full_names))
            continue
        dtitles = [depts.get(d, {}).get("title", d) for d in brand_depts[brand]]
        low = brand_dept_phrase(dtitles, lower=True)
        page, url = build_listing(
            ltpl, rel, brand, brand_dept_phrase(dtitles, lower=False), "",
            "%s — %s | via.accessories" % (brand, low),
            "%s — %s. %s." % (brand, low, DELIVERY_LINE),
            [home_link, '<span class="current">%s</span>' % esc(brand)],
            [home, (brand, "%s/%s" % (SITE_URL, rel))],
            items, slugs, full_names,
            grid=brand_sections_html(brand, items, depts, dept_brand_pages, slugs, full_names),
            facets=FILTER_FACETS_BRAND,
        )
        write(os.path.join(ROOT, rel), page)
        listing_urls.append(url)

    # --- сторінки відділів (плитки брендів ведуть на сторінки «відділ + бренд») ---
    for d in used_depts + kept_depts:
        items = [(pid, p) for pid, p in visible.items() if p.get("dept") == d]
        dtitle = depts.get(d, {}).get("title", d)
        rel = dept_pages.get(d) or "category/%s.html" % DEPT_SLUGS[d]
        if not items:                       # порожній відділ — «Скоро в наявності», noindex, не в sitemap
            write(os.path.join(ROOT, rel), coming_soon_page(
                ltpl, rel, dtitle, [home_link, '<span class="current">%s</span>' % esc(dtitle)],
                [home, (dtitle, "%s/%s" % (SITE_URL, rel))], slugs, full_names))
            continue
        bs = ordered_brands(dept_brand_counts.get(d, {}), first_seen)
        tiles = brand_tiles_html(bs, {b: dept_brand_pages[(d, b)] for b in bs}, logos, items)
        top = ", ".join(bs[:3])
        title = "%s — %s | via.accessories" % (dtitle, top) if top else "%s | via.accessories" % dtitle
        description = "%s — %s%s. %s." % (dtitle, top, " та інші бренди" if len(bs) > 3 else "", DELIVERY_LINE) if top else "%s. %s." % (dtitle, DELIVERY_LINE)
        page, url = build_listing(
            ltpl, rel, dtitle, "", "", title, description,
            [home_link, '<span class="current">%s</span>' % esc(dtitle)],
            [home, (dtitle, "%s/%s" % (SITE_URL, rel))],
            items, slugs, full_names, tiles,
            tiles_heading="Усе взуття" if d == "shoes" else "Усі %s" % dtitle.lower(),
        )
        write(os.path.join(ROOT, rel), page)
        listing_urls.append(url)
        # --- сторінки «відділ + бренд»: category/<відділ>/<бренд>.html — лише товари бренду в цьому відділі ---
        for b in bs:
            brel = dept_brand_pages[(d, b)]
            bitems = [(pid, p) for pid, p in items if p.get("brand") == b]
            h1 = "%s %s" % (dtitle, b)
            btitle = h1 + " | via.accessories"
            if len(btitle) > 60:
                btitle = h1
            os.makedirs(os.path.dirname(os.path.join(ROOT, brel)), exist_ok=True)
            page, url = build_listing(
                ltpl, brel, h1, "",
                '<div class="brands-line"><a href="../../%s">Усі товари %s</a></div>\n' % (brand_pages[b], esc(b)),
                btitle,
                "%s у via.accessories: %s у наявності. %s." % (h1, plural_items(len(bitems)), DELIVERY_LINE),
                [home_link, '<a href="../../%s">%s</a><span class="sep">›</span>' % (rel, esc(dtitle)),
                 '<span class="current">%s</span>' % esc(b)],
                [home, (dtitle, "%s/%s" % (SITE_URL, rel)), (b, "%s/%s" % (SITE_URL, brel))],
                bitems, slugs, full_names, facets=FILTER_FACETS_BRAND,
            )
            write(os.path.join(ROOT, brel), page)
            listing_urls.append(url)

    # --- «Всі бренди» (brands.html): плитки всіх брендів з видимими товарами, з кількістю товарів ---
    page, url = build_listing(
        ltpl, ALL_BRANDS_PAGE, "Бренди", "", "", "Усі бренди | via.accessories",
        "Бренди в via.accessories: %s. %s." % (", ".join(brands_by_count[:6]) + (" та інші" if len(brands_by_count) > 6 else ""), DELIVERY_LINE),
        [home_link, '<span class="current">Бренди</span>'],
        [home, ("Бренди", "%s/%s" % (SITE_URL, ALL_BRANDS_PAGE))],
        [], slugs, full_names,
        brand_tiles=brand_tiles_html(brands_by_count, brand_pages, logos, [], "", vis_brand_counts),
    )
    write(os.path.join(ROOT, ALL_BRANDS_PAGE), page)
    listing_urls.append(url)

    # --- каталог: уся сітка товарів у HTML, новинки першими (JS вмикає кнопки, фільтри й сортування;
    #     старі адреси ?dept=/?brand=<Назва> малює JS каталогу) ---
    cat_cards = "\n".join(
        card_html(pid, p, slugs[pid], full_names[pid], "high" if i < 4 else "lazy", "", True)
        for i, (pid, p) in enumerate(newest_first(visible.items()))
    )
    inject("catalog.html", "catalog-grid",
           filter_root('<div class="grid" id="catalogGrid">\n%s\n</div>\n' % cat_cards, FILTER_FACETS_ALL))
    # --- пошук: індекс товарів для assets/search.js і сторінка результатів search.html (noindex, не в sitemap) ---
    write(os.path.join(ROOT, "assets", "search-index.js"), search_index_js(visible, slugs, depts))
    page, _ = build_listing(
        ltpl, "search.html", "Пошук", "", "", "Пошук | via.accessories",
        "Пошук товарів via.accessories: бренд, модель, код.",
        [home_link, '<span class="current">Пошук</span>'],
        [home, ("Пошук", SITE_URL + "/search.html")],
        [], slugs, full_names,
        grid='<div class="search-status" id="searchStatus" aria-live="polite"></div>\n'
             '<div class="grid" id="searchGrid"></div>\n'
             '<noscript><p class="search-status">Пошук працює з увімкненим JavaScript. '
             '<a href="catalog.html">Перейти до каталогу</a></p></noscript>\n',
    )
    page = page.replace('<div class="filter-root" data-filter-root ', '<div class="filter-root" data-filter-root data-filter-defer ', 1)
    page = page.replace('<link rel="canonical"', '<meta name="robots" content="noindex, follow">\n<link rel="canonical"', 1)
    write(os.path.join(ROOT, "search.html"), page)
    inject("catalog.html", "catalog-ld", breadcrumb_jsonld([home, ("Каталог", SITE_URL + "/catalog.html")]) + "\n")
    # --- головна: «Хіти сезону» у HTML ---
    hits = "\n".join(hit_card_html(pid, products[pid], slugs[pid], full_names[pid]) for pid in pick_hits(visible))
    inject("index.html", "hits", hits + "\n")

    # старі адреси -> нові (після перейменувань); у sitemap і feed їх немає
    generated = {"products/%s.html" % slugs[pid] for pid in products} | set(brand_pages.values()) | set(dept_pages.values()) | set(dept_brand_pages.values()) \
        | {"category/%s.html" % DEPT_SLUGS[d] for d in kept_depts} | {ALL_BRANDS_PAGE}
    redirects = write_redirects(generated)

    # id -> адреса (для каталогу, головної, кошика, старого product.html)
    mapping = {pid: "products/%s.html" % slugs[pid] for pid in products}
    with open(os.path.join(ROOT, "assets", "product-urls.js"), "w", encoding="utf8", newline="\n") as f:
        f.write("/* Згенеровано build_pages.py — не редагувати вручну. */\n")
        f.write("var PRODUCT_URLS = %s;\n" % json.dumps(mapping, ensure_ascii=False, indent=2))
        f.write("var BRAND_URLS = %s;\n" % json.dumps(brand_pages, ensure_ascii=False, indent=2))
        f.write("var DEPT_URLS = %s;\n" % json.dumps(dept_pages, ensure_ascii=False, indent=2))
        tile_logos = {b: brand_logo(b, logos) for b in brand_pages if brand_logo(b, logos)}
        f.write("/* Логотипи для плиток брендів (assets/brands/<slug>.svg|png або BRAND_LOGOS); немає — текстова плитка */\n")
        f.write("var BRAND_TILE_LOGOS = %s;\n" % json.dumps(tile_logos, ensure_ascii=False, indent=2))
        compact = {k: [m["w"], m["h"], m["s"]] for k, m in IMG_META.items() if k.startswith("content/")}
        f.write("/* Оптимізовані копії фото: шлях -> [ширина, висота, [ширини WebP]] */\n")
        f.write("var IMG_META = %s;\n" % json.dumps(compact, ensure_ascii=False, separators=(",", ":")))
        f.write(PIC_HELPER_JS)
        f.write(
            "function productUrl(id) {\n"
            "    return PRODUCT_URLS[id] || ('product.html?id=' + encodeURIComponent(id));\n"
            "}\n"
            "/* Сторінка бренду / відділу; якщо її ще немає — старий фільтр каталогу */\n"
            "function brandUrl(name) {\n"
            "    return BRAND_URLS[name] || ('catalog.html?brand=' + encodeURIComponent(name));\n"
            "}\n"
            "function deptUrl(key) {\n"
            "    return DEPT_URLS[key] || ('catalog.html?dept=' + encodeURIComponent(key));\n"
            "}\n"
        )

    # sitemap.xml — усі публічні сторінки (без 404, кошика та старого product.html — у них noindex)
    locs = ["%s/%s" % (SITE_URL, pg) for pg in STATIC_PAGES] + listing_urls + urls
    rels = {loc: (loc[len(SITE_URL) + 1:] or "index.html") for loc in locs}
    dates = lastmod_dates(rels.values())
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for loc in locs:
            f.write("  <url><loc>%s</loc><lastmod>%s</lastmod></url>\n" % (esc(loc), dates[rels[loc]]))
        f.write("</urlset>\n")

    # robots.txt — дозволено все (кошик закритий від індексу метатегом noindex)
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf8", newline="\n") as f:
        f.write("User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE_URL)

    # feed.xml для Google Merchant Center
    feed_count, feed_skipped = build_feed(visible, slugs, depts)
    if feed_skipped:
        print("Увага: у фід не потрапили товари без ціни або фото: %s" % ", ".join(feed_skipped))

    print("Створено сторінок товарів: %d (з ціною: %d, без ціни: %d)" % (len(products), priced, len(products) - priced))
    if len(visible) != len(products):
        print("Приховано (немає в наявності): %d — %s" % (len(products) - len(visible), ", ".join(x for x in products if x not in visible)))
    print("feed.xml (Google Merchant Center): %d товарів" % feed_count)
    print("Сторінок брендів: %d, відділів: %d, «відділ + бренд»: %d" % (len(brand_pages), len(dept_pages), len(dept_brand_pages)))
    print("Меню/підвал: відділи — %s; бренди в підвалі — %s" % (", ".join(depts.get(d, {}).get("title", d) for d in nav_depts),
                                                             ", ".join(footer_brands)))
    soon = [b for b in brand_pages if b not in vis_brand_counts] + \
           [depts.get(d, {}).get("title", d) for d in used_depts + kept_depts if d not in nav_depts]
    if soon:
        print("«Скоро в наявності» (noindex, не в sitemap): %s" % ", ".join(soon))
    print("Оновлено файлів із навігаційними посиланнями: %d" % nav_changed)
    print("Нових WebP-копій: %d, обкладинок відео: %d, стиснених відео: %d, видалено застарілих: %d" % (made_img, made_poster, made_video, removed_opt))
    print("Приклад товару: %s" % urls[0])
    print("Приклад бренду: %s/%s" % (SITE_URL, next(iter(brand_pages.values()))))
    if dept_pages:
        print("Приклад відділу: %s/%s" % (SITE_URL, next(iter(dept_pages.values()))))
    print("sitemap.xml: %d адрес; robots.txt; assets/product-urls.js" % len(locs))
    if redirects:
        print("Переадресацій: %d (%s)" % (len(redirects), ", ".join(redirects)))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf8")
    main()
