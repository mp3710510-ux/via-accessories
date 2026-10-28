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
  * створює category/<відділ>.html — сторінку кожного відділу, що має товари;
  * виставляє посилання на відділи/бренди в шапці, підвалах і на головній (атрибути data-dept /
    data-brand): є сторінка — веде на неї, ще немає — на catalog.html?...;
  * створює assets/product-urls.js — відповідність id товару -> адреса сторінки
    (її використовують каталог, головна, кошик і старий product.html?id=...);
  * створює sitemap.xml, robots.txt і feed.xml (фід товарів для Google Merchant Center).

Усі згенеровані файли можна безпечно перегенерувати: папки products/, brands/, category/
перед генерацією очищуються від старих *.html (щоб не лишалось сторінок видалених товарів).
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


def build_page(tpl, pid, p, slug, depts, brand_pages, dept_pages):
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
    video = p.get("video") or None
    specs = p.get("specs") or {}

    full_name = ("%s %s" % (brand, name)) if has_brand and brand.lower() not in name.lower() else name
    title = "%s — %s | via.accessories" % (full_name, p.get("category") or dept_title)
    og_title = "%s — via.accessories" % full_name

    desc = (p.get("description") or "").strip()
    tail = []
    if code:
        tail.append("Код: %s." % code)
    if num is not None:
        tail.append("Ціна: %s." % price_text)
    meta_desc = trim(desc, 160 - len(" ".join(tail)) - 1) if desc else full_name
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
            "availability": AVAILABILITY,
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

    # --- хлібні крихти: Головна › Бренд › Назва (бренд — посилання на його сторінку) ---
    crumbs = ['<a href="../index.html">Головна</a>', '<span class="sep">›</span>']
    ld_crumbs = [("Головна", SITE_URL + "/")]
    if has_brand and brand in brand_pages:
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
    if video:
        pm = POSTER_META.get(video)
        gallery.append({
            "type": "video", "src": "../" + url_path(VIDEO_OUT.get(video, video)),
            "poster": ("../" + url_path(pm["p"])) if pm else "",
            "w": pm["w"] if pm else 0, "h": pm["h"] if pm else 0,
        })
        cover = picture_html(images[0], full_name, THUMB_SIZES, "../", "lazy") if images else ""
        thumbs.append('<div class="thumb video-thumb" data-index="%d">%s</div>' % (len(images), cover))

    price_block = '<div class="price" id="productPrice">%s</div>\n' % esc(price_text) if num is not None else ""
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
        "DESCRIPTION_TEXT": esc(desc),
        "SPECS": spec_items,
        "TG_HREF": esc(tg_href),
        "PRODUCT_JSON": product_json,
    }
    out = tpl
    for k, v in repl.items():
        out = out.replace("%%" + k + "%%", v)
    leftover = re.findall(r"%%[A-Z_]+%%", out)
    if leftover:
        raise RuntimeError("Не підставлено плейсхолдери %s у %s" % (leftover, pid))
    return out, page_url, num


NAV_LINK_RE = re.compile(r'<a href="([^"]*)" data-(dept|brand)="([^"]*)"')


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
        prefix = "../" if href.startswith("../") else ""
        if kind == "dept":
            target = dept_pages.get(value) or "catalog.html?dept=%s" % urllib.parse.quote(value)
        else:
            target = brand_pages.get(value) or "catalog.html?brand=%s" % urllib.parse.quote(value)
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


def card_html(pid, p, slug, full_name, loading="lazy"):
    """Картка товару, як у каталозі; посилання прямо в HTML."""
    href = "../products/%s.html" % slug
    img = picture_html(p["images"][0], full_name, CARD_SIZES, "../", loading) if p.get("images") else ""
    code = str(p.get("code") or "")
    num = price_number(p)
    price = '<div class="price">%s</div>' % esc((p.get("price") or "").strip()) if num is not None else ""
    code_html = '<div class="code">%s</div>' % esc(code) if code else ""
    return (
        '<div class="card">'
        '<a href="%s" style="display:block;text-decoration:none;color:inherit;">'
        '<div class="card-image">%s</div></a>'
        '<div class="card-caption"><a href="%s" style="text-decoration:none;color:inherit;">'
        '<div class="name">%s</div>%s%s</a>'
        '<button class="add-to-cart" type="button" data-id="%s">У кошик</button></div></div>'
        % (href, img, href, esc(p["name"]), price, code_html, esc(pid))
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


def build_listing(tpl, rel, h1, subtitle, brands_line, title, description, crumbs, ld_crumbs, items, slugs, full_names, brand_tiles=""):
    url = "%s/%s" % (SITE_URL, rel)
    first = items[0][1] if items else {}
    og_image = ("%s/%s" % (SITE_URL, url_path(first["images"][0]))) if first.get("images") else ""
    # найперша картка (LCP) — з високим пріоритетом і без lazy; решта — lazy (ті, що вже на екрані, браузер все одно вантажить одразу)
    cards = "\n".join(
        card_html(pid, p, slugs[pid], full_names[pid], "high" if i == 0 else "lazy")
        for i, (pid, p) in enumerate(items)
    )
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
        # на сторінці відділу — лише плитки брендів (товари — на сторінках брендів); інакше сітка товарів
        "GRID": "" if brand_tiles else '<div class="grid">\n%s\n</div>\n' % cards,
        "ITEMS_JSON": listing_items_json(items),
    }
    out = tpl
    for k, v in repl.items():
        out = out.replace("%%" + k + "%%", v)
    leftover = re.findall(r"%%[A-Z_]+%%", out)
    if leftover:
        raise RuntimeError("Не підставлено плейсхолдери %s у %s" % (leftover, rel))
    return out, url


def brand_tiles_html(brands, brand_pages, logos, items):
    """Плитки брендів (логотип або фото першого товару), як у каталозі — для сторінки відділу."""
    tiles = []
    for i, b in enumerate(brands):
        logo = logos.get(b)
        cover = logo or next((p["images"][0] for _, p in items if p.get("brand") == b and p.get("images")), "")
        tiles.append(
            '<a class="brand-tile" href="../%s"><div class="brand-tile-image%s">%s</div>'
            '<div class="brand-tile-name">%s</div></a>'
            % (brand_pages[b], " is-logo" if logo else "",
               picture_html(cover, b, TILE_SIZES, "../", "eager" if i < 5 else "lazy"), esc(b))
        )
    if not tiles:
        return ""
    return '<div class="brand-grid brand-tiles">\n%s\n</div>\n' % "\n".join(tiles)


def clean_dir(path):
    os.makedirs(path, exist_ok=True)
    for fn in os.listdir(path):
        if fn.endswith(".html"):
            os.remove(os.path.join(path, fn))


def full_name_of(p):
    brand = p.get("brand") or ""
    has_brand = bool(brand) and brand != "Інше"
    return ("%s %s" % (brand, p["name"])) if has_brand and brand.lower() not in p["name"].lower() else p["name"]


def write(path, text):
    with open(path, "w", encoding="utf8", newline="\n") as f:
        f.write(text)


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
        it = ET.SubElement(ch, "item")
        ET.SubElement(it, g("id")).text = slugs[pid]
        ET.SubElement(it, g("title")).text = trim(full_name_of(p), 150)
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
        cat = GOOGLE_CATEGORY.get(dept)
        if cat:
            ET.SubElement(it, g("google_product_category")).text = cat
        ET.SubElement(it, g("product_type")).text = ("%s > %s" % (dept_title, brand)) if has_brand else dept_title
        count += 1
    ET.indent(rss, space="  ")
    data = ET.tostring(rss, encoding="utf-8", xml_declaration=True)     # байти, переноси рядків завжди LF
    with open(os.path.join(ROOT, "feed.xml"), "wb") as f:
        f.write(data + b"\n")
    return count, skipped


def main():
    products, depts, logos = load_products()
    slugs = make_slugs(products)
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
            dept_brand_counts.setdefault(d, {})
            dept_brand_counts[d][b] = dept_brand_counts[d].get(b, 0) + 1
    brand_pages = {b: "brands/%s.html" % slugify(b) for b in brand_counts}
    used_depts = [d for d in DEPT_SLUGS if any(p.get("dept") == d for p in products.values())]
    dept_pages = {d: "category/%s.html" % DEPT_SLUGS[d] for d in used_depts}
    for d in {p.get("dept") for p in products.values()} - set(DEPT_SLUGS):
        print("Увага: відділ '%s' немає в DEPT_SLUGS — сторінку відділу не створено" % d)

    # --- WebP-копії фото та обкладинки відео (лише нові/змінені) ---
    photo_sources = []
    for p in products.values():
        photo_sources += [i for i in (p.get("images") or []) if i not in photo_sources]
    photo_sources += [l for l in logos.values() if l not in photo_sources]
    photo_sources += [sl for sl in SLIDES if os.path.exists(os.path.join(ROOT, sl))]
    videos = sorted({p["video"] for p in products.values() if p.get("video")})
    made_img = optimize_images(photo_sources)
    made_poster = make_posters(videos)
    made_video, video_out = compress_videos(videos)
    VIDEO_OUT.update(video_out)
    removed_opt = cleanup_optimized() + cleanup_videos(video_out.values())

    # посилання в шапці/підвалах/головній -> нові сторінки (або старий фільтр, якщо сторінки ще немає)
    nav_changed = sync_nav_links(brand_pages, dept_pages)
    with open(os.path.join(ROOT, "templates", "product.tpl.html"), encoding="utf8") as f:
        tpl = f.read()

    clean_dir(OUT_DIR)
    clean_dir(BRANDS_DIR)
    clean_dir(CATEGORY_DIR)
    full_names = {pid: full_name_of(p) for pid, p in products.items()}

    urls, priced = [], 0
    for pid, p in products.items():
        page, page_url, num = build_page(tpl, pid, p, slugs[pid], depts, brand_pages, dept_pages)
        write(os.path.join(OUT_DIR, slugs[pid] + ".html"), page)
        urls.append(page_url)
        priced += 1 if num is not None else 0

    with open(os.path.join(ROOT, "templates", "listing.tpl.html"), encoding="utf8") as f:
        ltpl = f.read()
    listing_urls = []
    home = ("Головна", SITE_URL + "/")
    home_link = '<a href="../index.html">Головна</a><span class="sep">›</span>'

    # --- сторінки брендів ---
    for brand in ordered_brands(brand_counts, first_seen):
        items = [(pid, p) for pid, p in products.items() if p.get("brand") == brand]
        dtitles = [depts.get(d, {}).get("title", d) for d in brand_depts[brand]]
        rel = brand_pages[brand]
        low = brand_dept_phrase(dtitles, lower=True)
        page, url = build_listing(
            ltpl, rel, brand, brand_dept_phrase(dtitles, lower=False), "",
            "%s — %s | via.accessories" % (brand, low),
            "%s — %s. %s." % (brand, low, DELIVERY_LINE),
            [home_link, '<span class="current">%s</span>' % esc(brand)],
            [home, (brand, "%s/%s" % (SITE_URL, rel))],
            items, slugs, full_names,
        )
        write(os.path.join(ROOT, rel), page)
        listing_urls.append(url)

    # --- сторінки відділів ---
    for d in used_depts:
        items = [(pid, p) for pid, p in products.items() if p.get("dept") == d]
        dtitle = depts.get(d, {}).get("title", d)
        rel = dept_pages[d]
        bs = ordered_brands(dept_brand_counts.get(d, {}), first_seen)
        tiles = brand_tiles_html(bs, brand_pages, logos, items)
        top = ", ".join(bs[:3])
        title = "%s — %s | via.accessories" % (dtitle, top) if top else "%s | via.accessories" % dtitle
        description = "%s — %s%s. %s." % (dtitle, top, " та інші бренди" if len(bs) > 3 else "", DELIVERY_LINE) if top else "%s. %s." % (dtitle, DELIVERY_LINE)
        page, url = build_listing(
            ltpl, rel, dtitle, "", "", title, description,
            [home_link, '<span class="current">%s</span>' % esc(dtitle)],
            [home, (dtitle, "%s/%s" % (SITE_URL, rel))],
            items, slugs, full_names, tiles,
        )
        write(os.path.join(ROOT, rel), page)
        listing_urls.append(url)

    # id -> адреса (для каталогу, головної, кошика, старого product.html)
    mapping = {pid: "products/%s.html" % slugs[pid] for pid in products}
    with open(os.path.join(ROOT, "assets", "product-urls.js"), "w", encoding="utf8", newline="\n") as f:
        f.write("/* Згенеровано build_pages.py — не редагувати вручну. */\n")
        f.write("var PRODUCT_URLS = %s;\n" % json.dumps(mapping, ensure_ascii=False, indent=2))
        f.write("var BRAND_URLS = %s;\n" % json.dumps(brand_pages, ensure_ascii=False, indent=2))
        f.write("var DEPT_URLS = %s;\n" % json.dumps(dept_pages, ensure_ascii=False, indent=2))
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

    # sitemap.xml
    locs = ["%s/%s" % (SITE_URL, pg) for pg in STATIC_PAGES] + listing_urls + urls
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for loc in locs:
            f.write("  <url><loc>%s</loc></url>\n" % esc(loc))
        f.write("</urlset>\n")

    # robots.txt
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf8", newline="\n") as f:
        f.write("User-agent: *\nAllow: /\nDisallow: /cart.html\n\nSitemap: %s/sitemap.xml\n" % SITE_URL)

    # feed.xml для Google Merchant Center
    feed_count, feed_skipped = build_feed(products, slugs, depts)
    if feed_skipped:
        print("Увага: у фід не потрапили товари без ціни або фото: %s" % ", ".join(feed_skipped))

    print("Створено сторінок товарів: %d (з ціною: %d, без ціни: %d)" % (len(products), priced, len(products) - priced))
    print("feed.xml (Google Merchant Center): %d товарів" % feed_count)
    print("Сторінок брендів: %d, відділів: %d" % (len(brand_pages), len(dept_pages)))
    print("Оновлено файлів із навігаційними посиланнями: %d" % nav_changed)
    print("Нових WebP-копій: %d, обкладинок відео: %d, стиснених відео: %d, видалено застарілих: %d" % (made_img, made_poster, made_video, removed_opt))
    print("Приклад товару: %s" % urls[0])
    print("Приклад бренду: %s/%s" % (SITE_URL, next(iter(brand_pages.values()))))
    if dept_pages:
        print("Приклад відділу: %s/%s" % (SITE_URL, next(iter(dept_pages.values()))))
    print("sitemap.xml: %d адрес; robots.txt; assets/product-urls.js" % len(locs))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf8")
    main()
