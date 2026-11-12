"""Заголовки й атрибути товарів для Google Merchant Center (feed.xml).

На сайті (назви, title, h1, адреси) нічого не змінюється — це лише для фіду.
Заголовок: [Жіноча/Жіночий/Жіноче/Жіночі] [тип] [бренд] [модель] [матеріал] [колір], до 150 символів.
Не вгадує: невідомі матеріал чи колір пропускаються.

feed_info(product, dept_title="") -> dict(title, type, gender, gender_word, material, material_title, color,
    color_title, category, product_type, model). Ручні значення товару (feedTitle, feedGender) мають пріоритет.
Використовують build_pages.py (фід) і адмінка via-admin (форма, бот, список).
"""
import re

MAX_TITLE = 150

# ----------------------------------------------------------------- категорії Google (офіційна таксономія, англ.)
CAT_HANDBAGS = "Apparel & Accessories > Handbags, Wallets & Cases > Handbags"
CAT_WALLETS = "Apparel & Accessories > Handbags, Wallets & Cases > Wallets & Money Clips"
CAT_BACKPACKS = "Luggage & Bags > Backpacks"
CAT_FANNY = "Luggage & Bags > Fanny Packs"
CAT_BELTS = "Apparel & Accessories > Clothing Accessories > Belts"
CAT_SCARVES = "Apparel & Accessories > Clothing Accessories > Scarves & Shawls"
CAT_KEYCHAINS = "Apparel & Accessories > Handbag & Wallet Accessories > Keychains"
CAT_ACCESSORIES = "Apparel & Accessories > Clothing Accessories"
CAT_JEWELRY = "Apparel & Accessories > Jewelry"
CAT_BRACELETS = "Apparel & Accessories > Jewelry > Bracelets"
CAT_NECKLACES = "Apparel & Accessories > Jewelry > Necklaces"
CAT_PENDANTS = "Apparel & Accessories > Jewelry > Charms & Pendants"
CAT_EARRINGS = "Apparel & Accessories > Jewelry > Earrings"
CAT_RINGS = "Apparel & Accessories > Jewelry > Rings"
CAT_BROOCHES = "Apparel & Accessories > Jewelry > Brooches & Lapel Pins"
CAT_WATCHES = "Apparel & Accessories > Jewelry > Watches"
CAT_SUNGLASSES = "Apparel & Accessories > Clothing Accessories > Sunglasses"
CAT_EYEGLASSES = "Health & Beauty > Personal Care > Vision Care > Eyeglasses"
CAT_SHOES = "Apparel & Accessories > Shoes"

# ----------------------------------------------------------------- типи: слово -> (укр., рід ч/ж/с/мн, категорія)
_T = {}


def _type(words, uk, gender, cat):
    for w in words:
        _T[w] = (uk, gender, cat)


_type(["bag", "bags", "handbag", "shoulder bag", "crossbody bag", "tote bag", "tote", "сумка", "сумки"], "сумка", "ж", CAT_HANDBAGS)
_type(["belt bag", "waist bag", "поясна сумка"], "поясна сумка", "ж", CAT_FANNY)
_type(["backpack", "рюкзак"], "рюкзак", "ч", CAT_BACKPACKS)
_type(["clutch", "клатч"], "клатч", "ч", CAT_HANDBAGS)
_type(["wallet", "гаманець"], "гаманець", "ч", CAT_WALLETS)
_type(["card holder", "cardholder", "картхолдер"], "картхолдер", "ч", CAT_WALLETS)
_type(["belt", "ремінь"], "ремінь", "ч", CAT_BELTS)
_type(["scarf", "хустка"], "хустка", "ж", CAT_SCARVES)
_type(["shawl", "шаль"], "шаль", "ж", CAT_SCARVES)
_type(["keychain", "key ring", "bag charm", "брелок"], "брелок", "ч", CAT_KEYCHAINS)
_type(["bracelet", "браслет"], "браслет", "ч", CAT_BRACELETS)
_type(["necklace", "кольє"], "кольє", "с", CAT_NECKLACES)
_type(["pendant", "підвіска"], "підвіска", "ж", CAT_PENDANTS)
_type(["earrings", "earring", "сережки"], "сережки", "мн", CAT_EARRINGS)
_type(["ring", "каблучка"], "каблучка", "ж", CAT_RINGS)
_type(["brooch", "брошка", "брош"], "брошка", "ж", CAT_BROOCHES)
_type(["watch", "watches", "годинник"], "годинник", "ч", CAT_WATCHES)
_type(["sunglasses", "окуляри"], "окуляри", "мн", CAT_SUNGLASSES)
_type(["glasses", "optical", "optical frame", "frame", "frames", "оправа"], "окуляри", "мн", CAT_EYEGLASSES)
_type(["sneakers", "sneaker", "trainers", "кросівки"], "кросівки", "мн", CAT_SHOES)
_type(["loafers", "loafer", "лофери"], "лофери", "мн", CAT_SHOES)
_type(["pumps", "heels", "shoes", "туфлі"], "туфлі", "мн", CAT_SHOES)
_type(["boots", "черевики"], "черевики", "мн", CAT_SHOES)
_type(["ankle boots", "ботильйони"], "ботильйони", "мн", CAT_SHOES)
_type(["sandals", "босоніжки", "сандалі"], "босоніжки", "мн", CAT_SHOES)
_type(["mules", "мюлі"], "мюлі", "мн", CAT_SHOES)
_type(["slides", "шльопанці"], "шльопанці", "мн", CAT_SHOES)
_type(["ballerinas", "ballet flats", "балетки"], "балетки", "мн", CAT_SHOES)
_type(["espadrilles", "еспадрильї"], "еспадрильї", "мн", CAT_SHOES)
_type(["кеди"], "кеди", "мн", CAT_SHOES)

DEPT_DEFAULT = {
    "bags": ("сумка", "ж", CAT_HANDBAGS),
    "shoes": ("взуття", "с", CAT_SHOES),
    "jewelry": ("прикраса", "ж", CAT_JEWELRY),
    "watches": ("годинник", "ч", CAT_WATCHES),
    "eyewear": ("окуляри", "мн", CAT_SUNGLASSES),
    "accessories": ("аксесуар", "ч", CAT_ACCESSORIES),
}
DEPT_CATS = {                                   # які типи з назви допустимі у відділі
    "bags": {CAT_HANDBAGS, CAT_BACKPACKS, CAT_FANNY, CAT_WALLETS},
    "shoes": {CAT_SHOES},
    "jewelry": {CAT_JEWELRY, CAT_BRACELETS, CAT_NECKLACES, CAT_PENDANTS, CAT_EARRINGS, CAT_RINGS, CAT_BROOCHES},
    "watches": {CAT_WATCHES},
    "eyewear": {CAT_SUNGLASSES, CAT_EYEGLASSES},
    "accessories": {CAT_WALLETS, CAT_BELTS, CAT_SCARVES, CAT_KEYCHAINS, CAT_ACCESSORIES, CAT_FANNY},
}
FEMALE_BY_DEFAULT = {"bags", "jewelry"}         # решта відділів — жіноче/чоловіче лише зі слів у назві/описі

# ----------------------------------------------------------------- матеріали: слово -> (основа прикметника | фраза, іменник)
# основа без закінчення («шкірян» -> шкіряна/шкіряний/шкіряне/шкіряні); фраза з пробілом не змінюється
_M = {}


def _mat(words, title, noun):
    for w in words:
        _M[w] = (title, noun)


_mat(["leather", "smooth leather", "grained leather", "lambskin", "calfskin", "calf leather", "goatskin"],
     "шкірян", "шкіра")
_mat(["ostrich leather", "ostrich"], "зі страусиної шкіри", "шкіра страуса")
_mat(["patent leather", "patent", "lacquer"], "лакован", "лакована шкіра")
_mat(["suede"], "замшев", "замша")
_mat(["nubuck"], "нубуков", "нубук")
_mat(["canvas", "light canvas", "coated canvas"], "", "канва")      # канва: у заголовок не пишемо, у g:material — так
_mat(["denim"], "джинсов", "джинс")
_mat(["tweed"], "твідов", "твід")
_mat(["textile", "fabric"], "текстильн", "текстиль")
_mat(["nylon"], "нейлонов", "нейлон")
_mat(["silk"], "шовков", "шовк")
_mat(["velvet"], "оксамитов", "оксамит")
_mat(["satin"], "атласн", "атлас")
_mat(["straw", "raffia"], "солом'ян", "солома")
_mat(["wool"], "вовнян", "вовна")
_mat(["plastic", "acetate"], "пластиков", "пластик")
_mat(["metal"], "металев", "метал")
JEWELRY_METALS = {"yellow gold": ("золото", "золото"), "white gold": ("біле золото", "біле золото"),
                  "rose gold": ("рожеве золото", "рожеве золото"), "gold": ("золото", "золото"),
                  "sterling silver": ("срібло", "срібло"), "silver": ("срібло", "срібло")}
PURITY = {"k18", "18k", "k14", "14k", "750", "585", "925"}
# камені в прикрасах: «з малахітом»; колір після них у заголовок не ставимо
STONES = {"malachite": "з малахітом", "onyx": "з оніксом", "black onyx": "з оніксом",
          "mother of pearl": "з перламутром", "mother-of-pearl": "з перламутром", "white mother of pearl": "з перламутром",
          "carnelian": "з сердоліком", "lapis lazuli": "з лазуритом", "lapis": "з лазуритом",
          "turquoise": "з бірюзою", "chalcedony": "з халцедоном", "agate": "з агатом", "tiger eye": "з тигровим оком",
          "tiger's eye": "з тигровим оком"}
# рекламні слова — у заголовок не йдуть: Premium, Premium quality, Luxury, Lux («Soft Lux» у Prada — модель, лишається)
PROMO = {"premium", "luxury", "lux"}
# характеристика «Матеріал» українською -> основа прикметника
SPEC_MAT = [("лакован", "лакован"), ("шкір", "шкірян"), ("замш", "замшев"), ("нубук", "нубуков"),
            ("канв", ""),("джинс", "джинсов"), ("денім", "джинсов"), ("твід", "твідов"),
            ("текстиль", "текстильн"), ("тканин", "текстильн"), ("нейлон", "нейлонов"), ("шовк", "шовков"),
            ("оксамит", "оксамитов"), ("атлас", "атласн"), ("солом", "солом'ян"), ("вовн", "вовнян"),
            ("пластик", "пластиков"), ("метал", "металев")]

# ----------------------------------------------------------------- кольори: слово -> основа
_C = {}


def _col(words, stem):
    for w in words:
        _C[w] = stem


_col(["black"], "чорн")
_col(["white"], "біл")
_col(["cream", "ivory", "milk", "off white", "off-white"], "кремов")
_col(["beige", "nude", "sand"], "бежев")
_col(["brown", "chocolate", "chocolate brown", "dark brown", "cognac", "tan", "camel", "caramel"], "коричнев")
_col(["red"], "червон")
_col(["cherry"], "вишнев")
_col(["burgundy", "bordo", "bordeaux", "borodo", "wine"], "бордов")
_col(["pink", "rose", "light pink", "hot pink", "fuchsia"], "рожев")
_col(["blue", "navy", "dark blue", "navy blue"], "син")
_col(["light blue", "ice blue", "sky blue", "baby blue"], "блакитн")
_col(["green"], "зелен")
_col(["dark green"], "темно-зелен")
_col(["mint", "mint gray", "mint grey", "mint green"], "м'ятн")
_col(["teal", "turquoise"], "бірюзов")
_col(["grey", "gray"], "сір")
_col(["yellow"], "жовт")
_col(["orange"], "помаранчев")
_col(["purple", "violet"], "фіолетов")
_col(["lilac", "lavender"], "бузков")
_col(["khaki"], "хакі")
_col(["multicolor", "multicolour", "multi"], "різнокольоров")
_col(["leopard"], "леопардов")
_col(["gold", "golden"], "золотист")
_col(["silver"], "сріблист")
NOT_COLOR = {"clear", "transparent"}            # «Clear/Black» -> колір беремо з другої частини
SPEC_COL = [("чорн", "чорн"), ("біл", "біл"), ("кремов", "кремов"), ("молочн", "кремов"), ("бежев", "бежев"),
            ("коричнев", "коричнев"), ("шоколад", "коричнев"), ("червон", "червон"), ("вишнев", "вишнев"),
            ("бордов", "бордов"), ("рожев", "рожев"), ("блакитн", "блакитн"), ("син", "син"),
            ("темно-зелен", "темно-зелен"), ("зелен", "зелен"), ("м'ятн", "м'ятн"), ("бірюзов", "бірюзов"),
            ("сір", "сір"), ("жовт", "жовт"), ("помаранчев", "помаранчев"), ("фіолетов", "фіолетов"),
            ("бузков", "бузков"), ("хакі", "хакі"), ("золот", "золотист"), ("срібл", "сріблист")]
HARDWARE = ["light gold hardware", "gold-tone hardware", "gold tone hardware", "silver-tone hardware",
            "gold hardware", "silver hardware", "with gold", "with silver", "hardware"]
FILLER = {"in", "with", "women's", "womens", "women", "woman", "men's", "mens", "men", "for", "жіноча", "жіночий",
          "жіноче", "жіночі", "чоловіча", "чоловічий", "чоловіче", "чоловічі"}

GENDER_WORD = {
    "female": {"ч": "Жіночий", "ж": "Жіноча", "с": "Жіноче", "мн": "Жіночі"},
    "male": {"ч": "Чоловічий", "ж": "Чоловіча", "с": "Чоловіче", "мн": "Чоловічі"},
}
GENDER_UK = {"female": "жіноча", "male": "чоловіча", "unisex": "унісекс"}
EYEWEAR_SIZE = re.compile(r"^\d{2}/\d{2}/\d{3}$")


def decline(stem, g):
    """Прикметник у роді типу. Фрази з пробілом («з канви», «срібло в позолоті») і «хакі» — як є."""
    if not stem or " " in stem or stem == "хакі":
        return stem
    if stem == "син":
        return {"ч": "синій", "ж": "синя", "с": "синє", "мн": "сині"}[g]
    return stem + {"ч": "ий", "ж": "а", "с": "е", "мн": "і"}[g]


def _norm(tok):
    return tok.lower().strip(",.;:()[]«»\"'")


def _composite(value):
    return bool(re.search(r"[/,]| і | та ", value or ""))


def detect_gender(dept, text):
    """female / male / unisex."""
    t = (text or "").lower()
    if re.search(r"\bwom[ae]n'?s?\b|жіноч", t):
        return "female"
    if re.search(r"\bm[ae]n'?s?\b|чоловіч", t):
        return "male"
    return "female" if dept in FEMALE_BY_DEFAULT else "unisex"


def analyse_name(name, dept, code="", brand=""):
    """Розбирає назву: тип, матеріал і колір з англійських слів, решта — модель."""
    toks = name.split()
    # бренд на початку назви (як було у Вк-1) — прибираємо
    if brand:
        b = brand.lower().split()
        if [_norm(t) for t in toks[:len(b)]] == [_norm(x) for x in b]:
            toks = toks[len(b):]
    jewelry = dept in ("jewelry", "watches")
    keep, typ, mats, cols, metal_gold, stones = [], None, [], [], [], []
    i = 0
    low = [_norm(t) for t in toks]
    while i < len(toks):
        hit = None
        for n in (3, 2, 1):
            if i + n > len(toks):
                continue
            ph = " ".join(low[i:i + n])
            if not jewelry and ph in HARDWARE:
                hit = ("hw", n, None)
            elif ph in _T:
                hit = ("type", n, _T[ph])
            elif jewelry and ph in STONES:
                hit = ("stone", n, STONES[ph])
            elif jewelry and ph in JEWELRY_METALS:
                hit = ("metal", n, JEWELRY_METALS[ph])
            elif ph in _M:
                hit = ("mat", n, _M[ph])
            elif ph in _C:
                hit = ("col", n, _C[ph])
            if hit:
                break
        tok, lt = toks[i], low[i]
        if hit:
            kind, n, val = hit
            if kind == "type" and typ is None:
                typ = val
            elif kind == "mat":
                mats.append(val)
            elif kind == "metal":
                metal_gold.append(val)
            elif kind == "stone" and val not in stones:
                stones.append(val)
            elif kind == "col":
                cols.append((val, " ".join(low[i:i + n])))
            i += n
            continue
        i += 1
        if lt in FILLER or lt in PURITY or (code and lt == code.lower()):
            continue
        # Premium / Premium quality / Luxury / Lux — реклама; «Soft Lux» (Prada) — назва моделі
        if lt in PROMO and not (lt == "lux" and keep and keep[-1].lower() == "soft"):
            continue
        if lt == "quality" and i >= 2 and low[i - 2] == "premium":
            continue
        if "/" in lt:
            parts = [p for p in lt.split("/") if p]
            if parts and all(p in _C or p in NOT_COLOR for p in parts):
                cols += [(_C[p], p) for p in parts if p in _C]
                continue
            if EYEWEAR_SIZE.match(lt):
                continue
        if re.fullmatch(r"\d{5,}", lt):                       # артикули-числа (50702857)
            continue
        if re.fullmatch(r"[a-z]{1,3}\d{4,}", lt):             # коди виду GG0011
            continue
        if re.fullmatch(r"[/\-–—&,.+]+", tok):
            continue
        if tok.isupper() and tok.isalpha() and len(tok) > 3:  # AMBIDIXTROUS -> Ambidixtrous
            tok = tok.capitalize()
        keep.append(tok.strip(","))
    # золото/срібло в назві сумки — найчастіше фурнітура: колір лише якщо інших кольорів немає
    if not jewelry and len(cols) > 1:
        cols = [c for c in cols if c[1] not in ("gold", "golden", "silver")] or cols
    model = re.sub(r"\s+", " ", " ".join(keep)).strip(" -–—,/")
    return {"type": typ, "materials": mats, "metals": metal_gold, "colors": [c[0] for c in cols], "model": model,
            "stones": stones}


def _spec_stem(value, table):
    v = (value or "").lower()
    for key, stem in table:
        if key in v:
            return stem
    return None


def feed_info(p, dept_title=""):
    dept = p.get("dept") or ""
    brand = p.get("brand") or ""
    if brand == "Інше":
        brand = ""
    specs = p.get("specs") or {}
    a = analyse_name(p.get("name") or "", dept, str(p.get("code") or ""), brand)
    uk, g, cat = DEPT_DEFAULT.get(dept, ("товар", "ч", CAT_ACCESSORIES))
    # тип із назви беремо, лише якщо він пасує відділу (напр. «Ring» у назві сумки — ні)
    if a["type"] and (dept not in DEPT_CATS or a["type"][2] in DEPT_CATS[dept]):
        uk, g, cat = a["type"]

    # матеріал: названий в англійській назві (Tweed, Denim, Suede, Patent, Ostrich…) має пріоритет над
    # загальним із характеристики; далі — характеристика (одна, не «шкіра / канва»); золото/срібло з назви
    # прикраси — лише якщо характеристики немає. Канва в заголовок не пишеться (у g:material — так).
    spec_m = (specs.get("Матеріал") or "").strip()
    spec_single = bool(spec_m) and not _composite(spec_m)
    spec_noun = spec_m[:1].lower() + spec_m[1:]
    spec_stem = _spec_stem(spec_m, SPEC_MAT) if spec_single else None
    material_title = material_noun = None
    if a["materials"]:
        material_title, material_noun = a["materials"][0]
        if spec_single and spec_stem == material_title:     # «Leather» + «теляча шкіра» -> у фід точніше
            material_noun = spec_noun
    elif spec_single:
        material_title = spec_stem if spec_stem is not None else spec_noun
        material_noun = spec_noun
    elif a["metals"] and not spec_m:
        material_title, material_noun = a["metals"][0]
    if spec_m and not material_noun:                       # у g:material — як у характеристиці («шкіра/канва»)
        material_noun = "/".join(x[:1].lower() + x[1:] if x[1:2].islower() else x
                                 for x in re.split(r"\s*/\s*", spec_m))

    # колір: характеристика «Колір», інакше перший колір із назви
    spec_c = (specs.get("Колір") or "").strip()
    color_stem = _spec_stem(spec_c, SPEC_COL) if spec_c and not _composite(spec_c) else None
    if not color_stem and a["colors"]:
        color_stem = a["colors"][0]

    gender = p.get("feedGender") or detect_gender(dept, "%s %s" % (p.get("name") or "", p.get("description") or ""))
    gw = GENDER_WORD.get(gender, {}).get(g)
    head = ("%s %s" % (gw, uk)) if gw else uk[:1].upper() + uk[1:]
    mat_t = decline(material_title, g) if material_title else ""
    if a["stones"]:
        # прикраса з каменем: «з малахітом, срібло в позолоті», колір не додаємо
        tail = [", ".join([" і ".join(a["stones"])] + ([mat_t] if mat_t else []))]
    else:
        col_t = decline(color_stem, g) if color_stem else ""
        # «бірюзова зі страусиної шкіри» читається краще, ніж «зі страусиної шкіри бірюзова»
        tail = [col_t, mat_t] if mat_t.startswith(("з ", "зі ")) else [mat_t, col_t]
    model_words = a["model"].split()
    while True:
        title = re.sub(r"\s+", " ", " ".join([head, brand, " ".join(model_words)] + tail)).strip()
        if len(title) <= MAX_TITLE or not model_words:
            break
        model_words.pop()
    title = title[:MAX_TITLE].rstrip()
    return {
        "title": title, "auto_title": title, "type": uk, "type_gender": g, "gender": gender,
        "gender_uk": GENDER_UK.get(gender, gender), "material": material_noun or "", "material_title": decline(material_title, g) if material_title else "",
        "color": decline(color_stem, "ч") if color_stem else "", "color_title": decline(color_stem, g) if color_stem else "",
        "category": cat, "product_type": ("%s > %s" % (dept_title, brand)) if brand else dept_title,
        "model": " ".join(model_words),
    }


def final(p, dept_title=""):
    """Те, що йде у фід: ручний заголовок (feedTitle) має пріоритет над автоматичним."""
    info = feed_info(p, dept_title)
    manual = (p.get("feedTitle") or "").strip()
    if manual:
        info["title"] = manual[:MAX_TITLE]
    return info
