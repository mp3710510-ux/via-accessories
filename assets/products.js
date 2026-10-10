/* ============================================================
   ЄДИНЕ ДЖЕРЕЛО ДАНИХ ПРО ТОВАРИ
   Раніше дані про товари дублювалися: один список у catalog.html
   (для карток), інший у product.html (для сторінки товару).
   Тепер це один об'єкт PRODUCTS, і catalog.html, і product.html
   беруть дані звідси.

   ЯК ДОДАТИ ТОВАР:
   Скопіюйте будь-який блок нижче, поміняйте ключ (id) на новий
   унікальний, наприклад "bags-5", і заповніть поля.

   ПОЛЯ ТОВАРУ:
   - dept        — ключ відділу (bags, shoes, watches, jewelry,
                   accessories, eyewear)
   - category    — назва категорії для відображення
   - brand       — бренд товару (Louis Vuitton, Chanel...). Товари без
                   конкретного бренду — brand:"Інше"
   - name        — назва товару
   - price       — ціна рядком, як показуємо користувачу
   - code        — код (артикул) товару, лише цифри
   - images      — МАСИВ шляхів до фото. Можна 1, можна 3 і
                   більше — галерея на сторінці товару та
                   мініатюри підлаштуються автоматично.
                   Перше фото масиву використовується як обкладинка
                   в каталозі.
   - video       — шлях до відео (mp4) або null, якщо відео немає
   - description — текст опису
   - specs       — об'єкт "характеристика: значення"
   ============================================================ */

var DEPARTMENTS_META = {
    bags:         { title: "Сумки",      subtitle: "Колекція сумок від провідних брендів" },
    shoes:        { title: "Взуття",     subtitle: "Взуття преміальної якості" },
    watches:      { title: "Годинники",  subtitle: "Швейцарські годинники та хронографи" },
    jewelry:      { title: "Прикраси",   subtitle: "Ювелірні вироби та біжутерія" },
    accessories:  { title: "Аксесуари",  subtitle: "Деталі, які завершують образ" },
    eyewear:      { title: "Окуляри",    subtitle: "Сонцезахисні та оптичні окуляри" }
};

/* Логотипи брендів для плиток у каталозі. Ключ — точне значення brand.
   Бренду без логотипа тут немає — для нього плитка показує фото сумки.
   Розширення файлів (.JPG) — у верхньому регістрі, як на диску: хостинг чутливий до регістру. */
var BRAND_LOGOS = {
    "Louis Vuitton":   "content/watermarked/Лого Лв.JPG",
    "Chanel":          "content/watermarked/Лого Ш.JPG",
    "Dior":            "content/watermarked/Лого Д.JPG",
    "Dolce & Gabbana": "content/watermarked/Лого Дг.JPG",
    "Balenciaga":      "content/watermarked/Лого Бл.jpg",
    "Coach":           "content/watermarked/Лого Кч.jpg",
    "Hermès":          "content/watermarked/Лого Н.jpg",
    "Loro Piana":      "content/watermarked/Лого Лп.jpg",
    "Prada":           "content/watermarked/Лого П.jpg",
    "Bottega Veneta":  "content/watermarked/Лого Бв.jpg"
};

var PRODUCTS = {

    "Лв-1": { dept:"bags", category:"Сумки", brand:"Louis Vuitton", name:"Vanity PM Monogram Empreinte Black", price:"4200 грн", code:"7322",
        images:["content/watermarked/Лв 1-1.jpg","content/watermarked/Лв 1-2.jpg","content/watermarked/Лв 1-3.jpg"],
        video:"content/watermarked/Лв 1-4.mp4",
        description:"Сумка Louis Vuitton Vanity PM Monogram Empreinte Black. Матеріал — шкіра, фурнітура золотого кольору. У комплекті коробка, пильник та документи.",
        specs:{"Розмір":"19/14/10","Матеріал":"Шкіра","Комплект":"Коробка, пильник, документи","Фурнітура":"Золото"} },

    "Лв-2": { dept:"bags", category:"Сумки", brand:"Louis Vuitton", name:"Vanity PM Monogram Multicolor", price:"5600 грн", code:"7478",
        images:["content/watermarked/Лв 2-1.jpg","content/watermarked/Лв 2-2.jpg","content/watermarked/Лв 2-3.jpg"], video:"content/watermarked/Лв 2-4.mp4",
        description:"Сумка Louis Vuitton Vanity PM Monogram Multicolor. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"19x12","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Лв-3": { dept:"bags", category:"Сумки", brand:"Louis Vuitton", name:"Vanity PM Monogram Empreinte Leather", price:"5000 грн", code:"7408",
        images:["content/watermarked/Лв 3-1.jpg","content/watermarked/Лв 3-2.jpg","content/watermarked/Лв 3-3.jpg"], video:"content/watermarked/Лв 3-4.mp4",
        description:"Сумка Louis Vuitton Vanity PM Monogram Empreinte Leather. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"19х14","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Лв-4": { dept:"bags", category:"Сумки", brand:"Louis Vuitton", name:"Vanity Monogram Canvas", price:"5700 грн", code:"7435",
        images:["content/watermarked/Лв 4-1.jpg","content/watermarked/Лв 4-2.jpg","content/watermarked/Лв 4-3.jpg"], video:"content/watermarked/Лв 4-4.mp4",
        description:"Сумка Louis Vuitton Vanity Monogram Canvas. Матеріал — шкіра / канва. Повний комплект.",
        specs:{"Розмір":"19х13","Матеріал":"шкіра / канва","Комплект":"Повний комплект"} },
    "Лв-5": { dept:"bags", category:"Сумки", brand:"Louis Vuitton", name:"Pochette Felicie Monogram Canvas", price:"5100 грн", code:"7439",
        images:["content/watermarked/Лв 5-1.jpg","content/watermarked/Лв 5-2.jpg","content/watermarked/Лв 5-3.jpg"], video:"content/watermarked/Лв 5-4.mp4",
        description:"Сумка Louis Vuitton Pochette Felicie Monogram Canvas. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"21х12","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Лв-6": { dept:"bags", category:"Сумки", brand:"Louis Vuitton", name:"Alma BB Damier Ebene Brown", price:"5500 грн", code:"76837",
        images:["content/watermarked/Лв 6-1.jpg","content/watermarked/Лв 6-2.jpg","content/watermarked/Лв 6-3.jpg"], video:"content/watermarked/Лв 6-4.mp4",
        description:"Сумка Louis Vuitton Alma BB Damier Ebene Brown. Матеріал — шкіра. Комплект: брендова коробка, пильник, документи.",
        specs:{"Розмір":"23.5x17.5x11.5","Матеріал":"шкіра","Комплект":"брендова коробка, пильник, документи"} },
    "Лв-7": { dept:"bags", category:"Сумки", brand:"Louis Vuitton", name:"Alma BB Monogram Denim Cream", price:"5800 грн", code:"76801",
        images:["content/watermarked/Лв 7-1.jpg","content/watermarked/Лв 7-2.jpg","content/watermarked/Лв 7-3.jpg"], video:"content/watermarked/Лв 7-4.mp4",
        description:"Сумка Louis Vuitton Alma BB Monogram Denim Cream. Матеріал — текстиль / шкіра. Повний комплект.",
        specs:{"Розмір":"24x17x11","Матеріал":"текстиль / шкіра","Комплект":"Повний комплект"} },
    "Лв-8": { dept:"bags", category:"Сумки", brand:"Louis Vuitton", name:"Pochette Metis Pink / Gold", price:"5200 грн", code:"0366",
        images:["content/watermarked/Лв 8-1.jpg","content/watermarked/Лв 8-2.jpg","content/watermarked/Лв 8-3.jpg"], video:"content/watermarked/Лв 8-4.mp4",
        description:"Сумка Louis Vuitton Pochette Metis Pink / Gold. Матеріал — шкіра / канва. Повний комплект.",
        specs:{"Розмір":"24x18x6","Матеріал":"шкіра / канва","Комплект":"Повний комплект"} },
    "Лв-9": { dept:"bags", category:"Сумки", brand:"Louis Vuitton", name:"Pochette Metis East West Black", price:"5500 грн", code:"7417",
        images:["content/watermarked/Лв 9-1.jpg","content/watermarked/Лв 9-2.jpg","content/watermarked/Лв 9-3.jpg"], video:"content/watermarked/Лв 9-4.mp4",
        description:"Сумка Louis Vuitton Pochette Metis East West Black. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"25х18","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Лв-10": { dept:"bags", category:"Сумки", brand:"Louis Vuitton", name:"Capucines Mini Black", price:"5400 грн", code:"0314",
        images:["content/watermarked/Лв 10-1.jpg","content/watermarked/Лв 10-2.jpg","content/watermarked/Лв 10-3.jpg"], video:"content/watermarked/Лв 10-4.mp4",
        description:"Сумка Louis Vuitton Capucines Mini Black. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"20х14х7","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Лв-11": { dept:"bags", category:"Сумки", brand:"Louis Vuitton", name:"Capucines MM Black Multicolor Embroidered Monogram", price:"6600 грн", code:"76842",
        images:["content/watermarked/Лв 11-1.jpg","content/watermarked/Лв 11-2.jpg","content/watermarked/Лв 11-3.jpg"], video:"content/watermarked/Лв 11-4.mp4",
        description:"Сумка Louis Vuitton Capucines MM Black Multicolor Embroidered Monogram. Матеріал — шкіра / текстиль. Повний комплект.",
        specs:{"Розмір":"27х18","Матеріал":"шкіра / текстиль","Комплект":"Повний комплект"} },
    "Лв-12": { dept:"bags", category:"Сумки", brand:"Louis Vuitton", name:"Capucines Mini Black with Gold", price:"5400 грн", code:"76890",
        images:["content/watermarked/Лв 12-1.jpg","content/watermarked/Лв 12-2.jpg","content/watermarked/Лв 12-3.jpg"], video:"content/watermarked/Лв 12-4.mp4",
        description:"Сумка Louis Vuitton Capucines Mini Black with Gold. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"20х13","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Лв-13": { dept:"bags", category:"Сумки", brand:"Louis Vuitton", name:"Keepall Bandouliere 25 Monogram Light Canvas", price:"5400 грн", code:"0745",
        images:["content/watermarked/Лв 13-1.jpg","content/watermarked/Лв 13-2.jpg","content/watermarked/Лв 13-3.jpg"], video:"content/watermarked/Лв 13-4.mp4",
        description:"Сумка Louis Vuitton Keepall Bandouliere 25 Monogram Light Canvas. Матеріал — канва / шкіра. Повний комплект.",
        specs:{"Розмір":"25x15","Матеріал":"канва / шкіра","Комплект":"Повний комплект"} },
    "Лв-14": { dept:"bags", category:"Сумки", brand:"Louis Vuitton", name:"Keepall 45 x Chrome Hearts Style", price:"5100 грн", code:"0703",
        images:["content/watermarked/Лв 14-1.jpg","content/watermarked/Лв 14-2.jpg","content/watermarked/Лв 14-3.jpg"], video:"content/watermarked/Лв 14-4.mp4",
        description:"Сумка Louis Vuitton Keepall 45 x Chrome Hearts Style. Матеріал — шкіра / канва. Комплект: пильник.",
        specs:{"Розмір":"45х26","Матеріал":"шкіра / канва","Комплект":"пильник"} },

    "Бл-1": { dept:"bags", category:"Сумки", brand:"Balenciaga", name:"Le City Suede Bag Chocolate Brown", price:"6800 грн", code:"3871",
        images:["content/watermarked/Бл 1-1.jpg","content/watermarked/Бл 1-2.jpg","content/watermarked/Бл 1-3.jpg"], video:"content/watermarked/Бл 1-4.mp4",
        description:"Сумка Balenciaga Le City Suede Bag Chocolate Brown. Матеріал — замш / шкіра. Повний комплект.",
        specs:{"Розмір":"30х19х7","Матеріал":"замш / шкіра","Комплект":"Повний комплект"} },
    "Бл-2": { dept:"bags", category:"Сумки", brand:"Balenciaga", name:"Le City Suede Bag Black", price:"6800 грн", code:"3870",
        images:["content/watermarked/Бл 2-1.jpg","content/watermarked/Бл 2-2.jpg","content/watermarked/Бл 2-3.jpg"], video:"content/watermarked/Бл 2-4.mp4",
        description:"Сумка Balenciaga Le City Suede Bag Black. Матеріал — замш / шкіра. Повний комплект.",
        specs:{"Розмір":"30х19х7","Матеріал":"замш / шкіра","Комплект":"Повний комплект"} },
    "Бл-3": { dept:"bags", category:"Сумки", brand:"Balenciaga", name:"Le City Suede Bag White", price:"6800 грн", code:"3870W",
        images:["content/watermarked/Бл 3-1.jpg","content/watermarked/Бл 3-2.jpg","content/watermarked/Бл 3-3.jpg"], video:"content/watermarked/Бл 3-4.mp4",
        description:"Сумка Balenciaga Le City Suede Bag White. Матеріал — замш / шкіра. Повний комплект.",
        specs:{"Розмір":"30х19х7","Матеріал":"замш / шкіра","Комплект":"Повний комплект"} },
    "Бл-4": { dept:"bags", category:"Сумки", brand:"Balenciaga", name:"Le City Pink", price:"6100 грн", code:"3866",
        images:["content/watermarked/Бл 4-1.jpg","content/watermarked/Бл 4-2.jpg","content/watermarked/Бл 4-3.jpg"], video:"content/watermarked/Бл 4-4.mp4",
        description:"Сумка Balenciaga Le City Pink. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"23х15","Матеріал":"шкіра","Комплект":"Повний комплект"} },

    "Кч-1": { dept:"bags", category:"Сумки", brand:"Coach", name:"Pillow Tabby Quilted in Borodo", price:"4900 грн", code:"5705",
        images:["content/watermarked/Кч 1-1.jpg","content/watermarked/Кч 1-2.jpg","content/watermarked/Кч 1-3.jpg"], video:"content/watermarked/Кч 1-4.mp4",
        description:"Сумка Coach Pillow Tabby Quilted in Borodo. Матеріал — шкіра. Комплект: брендова коробка, пильник, документи.",
        specs:{"Розмір":"21х16","Матеріал":"шкіра","Комплект":"брендова коробка, пильник, документи"} },
    "Кч-2": { dept:"bags", category:"Сумки", brand:"Coach", name:"Tabby Shoulder Bag Black with Gold", price:"5300 грн", code:"5744",
        images:["content/watermarked/Кч 2-1.jpg","content/watermarked/Кч 2-2.jpg","content/watermarked/Кч 2-3.jpg"], video:"content/watermarked/Кч 2-4.mp4",
        description:"Сумка Coach Tabby Shoulder Bag Black with Gold. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"30 см","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Кч-3": { dept:"bags", category:"Сумки", brand:"Coach", name:"Pillow Tabby Backpack Black with Gold", price:"4900 грн", code:"5722",
        images:["content/watermarked/Кч 3-1.jpg","content/watermarked/Кч 3-2.jpg","content/watermarked/Кч 3-3.jpg"], video:"content/watermarked/Кч 3-4.mp4",
        description:"Сумка Coach Pillow Tabby Backpack Black with Gold. Матеріал — шкіра. Комплект: брендова коробка, пильник, документи.",
        specs:{"Розмір":"20х20х12","Матеріал":"шкіра","Комплект":"брендова коробка, пильник, документи"} },
    "Кч-4": { dept:"bags", category:"Сумки", brand:"Coach", name:"Tabby Shoulder Bag Pink with Gold Hardware", price:"4900 грн", code:"5739",
        images:["content/watermarked/Кч 4-1.jpg","content/watermarked/Кч 4-2.jpg","content/watermarked/Кч 4-3.jpg"], video:"content/watermarked/Кч 4-4.mp4",
        description:"Сумка Coach Tabby Shoulder Bag Pink with Gold Hardware. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"21x11x7","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Кч-5": { dept:"bags", category:"Сумки", brand:"Coach", name:"Tabby 26 Bow Print Shoulder Bag White/Pink", price:"5200 грн", code:"5741",
        images:["content/watermarked/Кч 5-1.jpg","content/watermarked/Кч 5-2.jpg","content/watermarked/Кч 5-3.jpg"], video:"content/watermarked/Кч 5-4.mp4",
        description:"Сумка Coach Tabby 26 Bow Print Shoulder Bag White/Pink. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"26х15","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Кч-6": { dept:"bags", category:"Сумки", brand:"Coach", name:"Signature Canvas Bag", price:"4600 грн", code:"5743",
        images:["content/watermarked/Кч 6-1.jpg","content/watermarked/Кч 6-2.jpg","content/watermarked/Кч 6-3.jpg"], video:"content/watermarked/Кч 6-4.mp4",
        description:"Сумка Coach Signature Canvas Bag. Матеріал — шкіра / канва. Повний комплект.",
        specs:{"Розмір":"24x13","Матеріал":"шкіра / канва","Комплект":"Повний комплект"} },

    "Ш-1": { dept:"bags", category:"Сумки", brand:"Chanel", name:"25 Light Blue Denim Handbag", price:"6200 грн", code:"11438",
        images:["content/watermarked/Ш 1-1.jpg","content/watermarked/Ш 1-2.jpg","content/watermarked/Ш 1-3.jpg"], video:"content/watermarked/Ш 1-4.mp4",
        description:"Сумка Chanel 25 Light Blue Denim Handbag. Матеріал — джинс. Повний комплект.",
        specs:{"Розмір":"26х20","Матеріал":"джинс","Комплект":"Повний комплект"} },
    "Ш-2": { dept:"bags", category:"Сумки", brand:"Chanel", name:"25 Small Handbag Yellow Lambskin with Gold Hardware", price:"5500 грн", code:"3550",
        images:["content/watermarked/Ш 2-1.jpg","content/watermarked/Ш 2-2.jpg","content/watermarked/Ш 2-3.jpg"], video:"content/watermarked/Ш 2-4.mp4",
        description:"Сумка Chanel 25 Small Handbag Yellow Lambskin with Gold Hardware. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"22х20","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Ш-3": { dept:"bags", category:"Сумки", brand:"Chanel", name:"25 Small Handbag Black Lambskin with Silver Hardware", price:"5400 грн", code:"3545",
        images:["content/watermarked/Ш 3-1.jpg","content/watermarked/Ш 3-2.jpg","content/watermarked/Ш 3-3.jpg"], video:"content/watermarked/Ш 3-4.mp4",
        description:"Сумка Chanel 25 Small Handbag Black Lambskin with Silver Hardware. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"22х20","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Ш-4": { dept:"bags", category:"Сумки", brand:"Chanel", name:"25 Small Handbag White Lambskin with Gold Hardware", price:"5500 грн", code:"3546",
        images:["content/watermarked/Ш 4-1.jpg","content/watermarked/Ш 4-2.jpg","content/watermarked/Ш 4-3.jpg"], video:"content/watermarked/Ш 4-4.mp4",
        description:"Сумка Chanel 25 Small Handbag White Lambskin with Gold Hardware. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"22х20","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Ш-5": { dept:"bags", category:"Сумки", brand:"Chanel", name:"Mini Flap Bag Burgundy", price:"4600 грн", code:"3978",
        images:["content/watermarked/Ш 5-1.jpg","content/watermarked/Ш 5-2.jpg","content/watermarked/Ш 5-3.jpg"], video:"content/watermarked/Ш 5-4.mp4",
        description:"Сумка Chanel Mini Flap Bag Burgundy. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"20х13х7","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Ш-6": { dept:"bags", category:"Сумки", brand:"Chanel", name:"Mini Flap Bag Black", price:"5000 грн", code:"3977",
        images:["content/watermarked/Ш 6-1.jpg","content/watermarked/Ш 6-2.jpg","content/watermarked/Ш 6-3.jpg"], video:"content/watermarked/Ш 6-4.mp4",
        description:"Сумка Chanel Mini Flap Bag Black. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"20х13х7","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Ш-7": { dept:"bags", category:"Сумки", brand:"Chanel", name:"Top Handle Flap Bag White", price:"6200 грн", code:"3919",
        images:["content/watermarked/Ш 7-1.jpg","content/watermarked/Ш 7-2.jpg","content/watermarked/Ш 7-3.jpg"], video:"content/watermarked/Ш 7-4.mp4",
        description:"Сумка Chanel Top Handle Flap Bag White. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"32x15x11,5","Матеріал":"шкіра","Комплект":"Повний комплект"} },

    "Ш-8": { dept:"bags", category:"Сумки", brand:"Chanel", name:"Vanity Case Bag in White Leather", price:"5200 грн", code:"3967",
        images:["content/watermarked/Ш 8-1.jpg","content/watermarked/Ш 8-2.jpg","content/watermarked/Ш 8-3.jpg"], video:"content/watermarked/Ш 8-4.mp4",
        description:"Сумка Chanel Vanity Case Bag in White Leather. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"18х10","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Ш-9": { dept:"bags", category:"Сумки", brand:"Chanel", name:"Vanity Case Bag in Black Leather", price:"5200 грн", code:"3910",
        images:["content/watermarked/Ш 9-1.jpg","content/watermarked/Ш 9-2.jpg","content/watermarked/Ш 9-3.jpg"], video:"content/watermarked/Ш 9-4.mp4",
        description:"Сумка Chanel Vanity Case Bag in Black Leather. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"19х13","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Ш-10": { dept:"bags", category:"Сумки", brand:"Chanel", name:"Vanity Case Cream", price:"5400 грн", code:"3985",
        images:["content/watermarked/Ш 10-1.jpg","content/watermarked/Ш 10-2.jpg","content/watermarked/Ш 10-3.jpg"], video:"content/watermarked/Ш 10-4.mp4",
        description:"Сумка Chanel Vanity Case Cream. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"22,5х14х6","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Ш-11": { dept:"bags", category:"Сумки", brand:"Chanel", name:"Mini Vanity Case in Black Lambskin", price:"5100 грн", code:"9811",
        images:["content/watermarked/Ш 11-1.jpg","content/watermarked/Ш 11-2.jpg","content/watermarked/Ш 11-3.jpg"], video:"content/watermarked/Ш 11-4.mp4",
        description:"Сумка Chanel Mini Vanity Case in Black Lambskin. Матеріал — шкіра. Комплект: брендова коробка, пильник, документи.",
        specs:{"Розмір":"17х10х8","Матеріал":"шкіра","Комплект":"брендова коробка, пильник, документи"} },
    "Ш-12": { dept:"bags", category:"Сумки", brand:"Chanel", name:"Mini Vanity Case in Bordo Lambskin Gold-Tone Hardware", price:"4600 грн", code:"3855",
        images:["content/watermarked/Ш 12-1.jpg","content/watermarked/Ш 12-2.jpg","content/watermarked/Ш 12-3.jpg"], video:"content/watermarked/Ш 12-4.mp4",
        description:"Сумка Chanel Mini Vanity Case in Bordo Lambskin Gold-Tone Hardware. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"10х9","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Ш-13": { dept:"bags", category:"Сумки", brand:"Chanel", name:"Mini Vanity Case in Bordo / Gold", price:"4900 грн", code:"3845",
        images:["content/watermarked/Ш 13-1.jpg","content/watermarked/Ш 13-2.jpg","content/watermarked/Ш 13-3.jpg"], video:"content/watermarked/Ш 13-4.mp4",
        description:"Сумка Chanel Mini Vanity Case in Bordo / Gold. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"16x10,5x8","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Ш-14": { dept:"bags", category:"Сумки", brand:"Chanel", name:"Mini Vanity Case in White Lambskin with Gold", price:"4900 грн", code:"3899",
        images:["content/watermarked/Ш 14-1.jpg","content/watermarked/Ш 14-2.jpg","content/watermarked/Ш 14-3.jpg"], video:"content/watermarked/Ш 14-4.mp4",
        description:"Сумка Chanel Mini Vanity Case in White Lambskin with Gold. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"17х10х8","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Ш-15": { dept:"bags", category:"Сумки", brand:"Chanel", name:"22 Bag Calfskin White / Silver", price:"5600 грн", code:"3913",
        images:["content/watermarked/Ш 15-1.jpg","content/watermarked/Ш 15-2.jpg","content/watermarked/Ш 15-3.jpg"], video:"content/watermarked/Ш 15-4.mp4",
        description:"Сумка Chanel 22 Bag Calfskin White / Silver. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"35х42","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Ш-16": { dept:"bags", category:"Сумки", brand:"Chanel", name:"Classic Flap Top Handle Caviar Black with Gold", price:"5200 грн", code:"7969",
        images:["content/watermarked/Ш 16-1.jpg","content/watermarked/Ш 16-2.jpg","content/watermarked/Ш 16-3.jpg"], video:"content/watermarked/Ш 16-4.mp4",
        description:"Сумка Chanel Classic Flap Top Handle Caviar Black with Gold. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"20х13","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Ш-17": { dept:"bags", category:"Сумки", brand:"Chanel", name:"Classic Flap Top Handle Caviar Pink with Gold", price:"5300 грн", code:"7961",
        images:["content/watermarked/Ш 17-1.jpg","content/watermarked/Ш 17-2.jpg","content/watermarked/Ш 17-3.jpg"], video:"content/watermarked/Ш 17-4.mp4",
        description:"Сумка Chanel Classic Flap Top Handle Caviar Pink with Gold. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"20х12","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Ш-18": { dept:"bags", category:"Сумки", brand:"Chanel", name:"Classic Flap 25 Bordo Caviar Gold Hardware", price:"5500 грн", code:"11434",
        images:["content/watermarked/Ш 18-1.jpg","content/watermarked/Ш 18-2.jpg","content/watermarked/Ш 18-3.jpg"], video:"content/watermarked/Ш 18-4.mp4",
        description:"Сумка Chanel Classic Flap 25 Bordo Caviar Gold Hardware. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"25х16х7","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Ш-19": { dept:"bags", category:"Сумки", brand:"Chanel", name:"Classic Flap 25 Ice Blue Caviar Silver Hardware", price:"5700 грн", code:"11457",
        images:["content/watermarked/Ш 19-1.jpg","content/watermarked/Ш 19-2.jpg","content/watermarked/Ш 19-3.jpg"], video:"content/watermarked/Ш 19-4.mp4",
        description:"Сумка Chanel Classic Flap 25 Ice Blue Caviar Silver Hardware. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"25х16х7","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Ш-20": { dept:"bags", category:"Сумки", brand:"Chanel", name:"Classic Flap 25 Cream Light Gold Hardware", price:"5700 грн", code:"7810",
        images:["content/watermarked/Ш 20-1.jpg","content/watermarked/Ш 20-2.jpg","content/watermarked/Ш 20-3.jpg"], video:"content/watermarked/Ш 20-4.mp4",
        description:"Сумка Chanel Classic Flap 25 Cream Light Gold Hardware. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"25х16х7","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Ш-21": { dept:"bags", category:"Сумки", brand:"Chanel", name:"Classic 25 Flap Caviar Blue with Gold Hardware", price:"5700 грн", code:"11687",
        images:["content/watermarked/Ш 21-1.jpg","content/watermarked/Ш 21-2.jpg","content/watermarked/Ш 21-3.jpg"], video:"content/watermarked/Ш 21-4.mp4",
        description:"Сумка Chanel Classic 25 Flap Caviar Blue with Gold Hardware. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"25х16х7","Матеріал":"шкіра","Комплект":"Повний комплект"} },

    "Д-1": { dept:"bags", category:"Сумки", brand:"Dior", name:"Saddle Bag Toile de Jouy Pink", price:"6200 грн", code:"6391",
        images:["content/watermarked/Д 1-1.jpg","content/watermarked/Д 1-2.jpg","content/watermarked/Д 1-3.jpg"], video:"content/watermarked/Д 1-4.mp4",
        description:"Сумка Dior Saddle Bag Toile de Jouy Pink. Матеріал — текстиль. Повний комплект.",
        specs:{"Розмір":"25х20","Матеріал":"текстиль","Комплект":"Повний комплект"} },
    "Д-2": { dept:"bags", category:"Сумки", brand:"Dior", name:"Lady Dior Bag Mint Gray with Gold", price:"5900 грн", code:"6395",
        images:["content/watermarked/Д 2-1.jpg","content/watermarked/Д 2-2.jpg","content/watermarked/Д 2-3.jpg"], video:"content/watermarked/Д 2-4.mp4",
        description:"Сумка Dior Lady Dior Bag Mint Gray with Gold. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"20x17","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Д-3": { dept:"bags", category:"Сумки", brand:"Dior", name:"Lady Dior Bag Black with Gold", price:"5900 грн", code:"6395(1)",
        images:["content/watermarked/Д 3-1.jpg","content/watermarked/Д 3-2.jpg","content/watermarked/Д 3-3.jpg"], video:"content/watermarked/Д 3-4.mp4",
        description:"Сумка Dior Lady Dior Bag Black with Gold. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"20x17","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Д-4": { dept:"bags", category:"Сумки", brand:"Dior", name:"Caro Bag in Blue Tweed with Gold", price:"5400 грн", code:"5437",
        images:["content/watermarked/Д 4-1.jpg","content/watermarked/Д 4-2.jpg","content/watermarked/Д 4-3.jpg"], video:"content/watermarked/Д 4-4.mp4",
        description:"Сумка Dior Caro Bag in Blue Tweed with Gold. Матеріал — текстиль. Комплект: брендова коробка, пильник, документи.",
        specs:{"Розмір":"22x15x7","Матеріал":"текстиль","Комплект":"брендова коробка, пильник, документи"} },
    "Д-5": { dept:"bags", category:"Сумки", brand:"Dior", name:"Lady Black Gold", price:"4300 грн", code:"6332",
        images:["content/watermarked/Д 5-1.jpg","content/watermarked/Д 5-2.jpg","content/watermarked/Д 5-3.jpg"], video:"content/watermarked/Д 5-4.mp4",
        description:"Сумка Dior Lady Black Gold. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"12х11х3,5","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Д-6": { dept:"bags", category:"Сумки", brand:"Dior", name:"Lady D-Joy Bag Mint Gray with Gold", price:"5800 грн", code:"6394",
        images:["content/watermarked/Д 6-1.jpg","content/watermarked/Д 6-2.jpg","content/watermarked/Д 6-3.jpg"], video:"content/watermarked/Д 6-4.mp4",
        description:"Сумка Dior Lady D-Joy Bag Mint Gray with Gold. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"22х11","Матеріал":"шкіра","Комплект":"Повний комплект"} },

    "Дг-1": { dept:"bags", category:"Сумки", brand:"Dolce & Gabbana", name:"Mini Sicily Green Patent Leather", price:"4500 грн", code:"92261",
        images:["content/watermarked/Дг 1-1.jpg","content/watermarked/Дг 1-2.jpg","content/watermarked/Дг 1-3.jpg"], video:"content/watermarked/Дг 1-4.mp4",
        description:"Сумка Dolce & Gabbana Mini Sicily Green Patent Leather. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"19,5x13x4","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Дг-2": { dept:"bags", category:"Сумки", brand:"Dolce & Gabbana", name:"Mini Sicily Black Bag", price:"4400 грн", code:"92163",
        images:["content/watermarked/Дг 2-1.jpg","content/watermarked/Дг 2-2.jpg","content/watermarked/Дг 2-3.jpg"], video:"content/watermarked/Дг 2-4.mp4",
        description:"Сумка Dolce & Gabbana Mini Sicily Black Bag. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"19,5x13x4","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Дг-3": { dept:"bags", category:"Сумки", brand:"Dolce & Gabbana", name:"Medium Sicily Cherry Lacquer Bag", price:"4600 грн", code:"92187",
        images:["content/watermarked/Дг 3-1.jpg","content/watermarked/Дг 3-2.jpg","content/watermarked/Дг 3-3.jpg"], video:"content/watermarked/Дг 3-4.mp4",
        description:"Сумка Dolce & Gabbana Medium Sicily Cherry Lacquer Bag. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"18x17x6","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Дг-4": { dept:"bags", category:"Сумки", brand:"Dolce & Gabbana", name:"DG Logo Leopard Patent Mini Bag", price:"4600 грн", code:"7885",
        images:["content/watermarked/Дг 4-1.jpg","content/watermarked/Дг 4-2.jpg","content/watermarked/Дг 4-3.jpg"], video:"content/watermarked/Дг 4-4.mp4",
        description:"Сумка Dolce & Gabbana DG Logo Leopard Patent Mini Bag. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"16х14","Матеріал":"шкіра","Комплект":"Повний комплект"} },

    "Н-1": { dept:"bags", category:"Сумки", brand:"Hermès", name:"Kelly Mini 19 Bag in Black Epsom Leather with Gold", price:"4900 грн", code:"3482",
        images:["content/watermarked/Н 1-1.jpg","content/watermarked/Н 1-2.jpg","content/watermarked/Н 1-3.jpg"], video:"content/watermarked/Н 1-4.mp4",
        description:"Сумка Hermès Kelly Mini 19 Bag in Black Epsom Leather with Gold. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"19х12","Матеріал":"шкіра","Відділення":"Один відділ","Комплект":"Повний комплект"} },
    "Н-2": { dept:"bags", category:"Сумки", brand:"Hermès", name:"Birkin 30/25 Silver Hardware", price:"6000 грн", code:"8382",
        images:["content/watermarked/Н 2-1.jpg","content/watermarked/Н 2-2.jpg","content/watermarked/Н 2-3.jpg"], video:"content/watermarked/Н 2-4.mp4",
        description:"Сумка Hermès Birkin 30/25 Silver Hardware. Матеріал — шкіра. Комплект: коробка, транспортна коробка, пильник, документ. Фурнітура: Срібна; Додатково: плечовий ремішок, хустинка, замок, коник.",
        specs:{"Розмір":"30/25","Матеріал":"шкіра","Фурнітура":"Срібна","Додатково":"плечовий ремішок, хустинка, замок, коник","Комплект":"коробка, транспортна коробка, пильник, документ"} },
    "Н-3": { dept:"bags", category:"Сумки", brand:"Hermès", name:"Birkin 30/25", price:"6600 грн", code:"9474",
        images:["content/watermarked/Н 3-1.jpg","content/watermarked/Н 3-2.jpg","content/watermarked/Н 3-3.jpg"], video:"content/watermarked/Н 3-4.mp4",
        description:"Сумка Hermès Birkin 30/25. Матеріал — шкіра. Комплект: коробка, пильник, документи. Додатково: хустинка, коник, замок, плечовий ремінь.",
        specs:{"Розмір":"30/25","Матеріал":"шкіра","Додатково":"хустинка, коник, замок, плечовий ремінь","Комплект":"коробка, пильник, документи"} },
    "Н-4": { dept:"bags", category:"Сумки", brand:"Hermès", name:"Birkin Premium Togo 25/20", price:"6500 грн", code:"47864",
        images:["content/watermarked/Н 4-1.jpg","content/watermarked/Н 4-2.jpg","content/watermarked/Н 4-3.jpg"], video:"content/watermarked/Н 4-4.mp4",
        description:"Сумка Hermès Birkin Premium Togo 25/20. Матеріал — шкіра Togo. Комплект: пильник, коробка, стрічка, буклети, замок+ключики, коник, хустинка. Особливості: фабричний номер вибито на шкірі, два ключики.",
        specs:{"Розмір":"25/20","Матеріал":"шкіра Togo","Особливості":"фабричний номер вибито на шкірі, два ключики","Комплект":"пильник, коробка, стрічка, буклети, замок+ключики, коник, хустинка"} },

    "Лп-1": { dept:"bags", category:"Сумки", brand:"Loro Piana", name:"Extra Pocket 23 in Smooth Leather Chocolate Brown", price:"4700 грн", code:"3213",
        images:["content/watermarked/Лп 1-1.jpg","content/watermarked/Лп 1-2.jpg","content/watermarked/Лп 1-3.jpg"], video:"content/watermarked/Лп 1-4.mp4",
        description:"Сумка Loro Piana Extra Pocket 23 in Smooth Leather Chocolate Brown. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"23х15","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Лп-2": { dept:"bags", category:"Сумки", brand:"Loro Piana", name:"Extra Pocket 23 in Smooth Leather Dark Green", price:"4500 грн", code:"3209",
        images:["content/watermarked/Лп 2-1.jpg","content/watermarked/Лп 2-2.jpg","content/watermarked/Лп 2-3.jpg"], video:"content/watermarked/Лп 2-4.mp4",
        description:"Сумка Loro Piana Extra Pocket 23 in Smooth Leather Dark Green. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"23х15","Матеріал":"шкіра","Комплект":"Повний комплект"} },
    "Лп-3": { dept:"bags", category:"Сумки", brand:"Loro Piana", name:"Extra Pocket 20 in Teal Ostrich Leather", price:"4400 грн", code:"3224",
        images:["content/watermarked/Лп 3-1.jpg","content/watermarked/Лп 3-2.jpg","content/watermarked/Лп 3-3.jpg"], video:"content/watermarked/Лп 3-4.mp4",
        description:"Сумка Loro Piana Extra Pocket 20 in Teal Ostrich Leather. Матеріал — шкіра. Повний комплект.",
        specs:{"Розмір":"20x11","Матеріал":"шкіра","Комплект":"Повний комплект"} },

    "П-1": { dept:"bags", category:"Сумки", brand:"Prada", name:"Bonnie Soft Lux Leather Handbag", price:"6200 грн", code:"0204",
        images:["content/watermarked/П 1-1.jpg","content/watermarked/П 1-2.jpg","content/watermarked/П 1-3.jpg"], video:"content/watermarked/П 1-4.mp4",
        description:"Сумка Prada Bonnie Soft Lux Leather Handbag. Матеріал — теляча шкіра. Повний комплект.",
        specs:{"Розмір":"30 см","Матеріал":"теляча шкіра","Комплект":"Повний комплект"} },

    "Бв-1": { dept:"bags", category:"Сумки", brand:"Bottega Veneta", name:"Bang Bang Bag in Brown", price:"4400 грн", code:"7374",
        images:["content/watermarked/Бв 1-1.jpg","content/watermarked/Бв 1-2.jpg","content/watermarked/Бв 1-3.jpg"], video:null,
        description:"Сумка Bottega Veneta Bang Bang Bag in Brown. Матеріал — шкіра. Комплект: брендова коробка, пильник.",
        specs:{"Розмір":"20x11x6","Матеріал":"шкіра","Відділення":"Один основний відділ","Комплект":"брендова коробка, пильник"} },
    "Бв-2": { dept:"bags", category:"Сумки", brand:"Bottega Veneta", name:"Bang Bang Bag in Black", price:"4400 грн", code:"7372",
        images:["content/watermarked/Бв 2-1.jpg","content/watermarked/Бв 2-2.jpg","content/watermarked/Бв 2-3.jpg"], video:null,
        description:"Сумка Bottega Veneta Bang Bang Bag in Black. Матеріал — шкіра. Комплект: брендова коробка, пильник.",
        specs:{"Розмір":"20x11x6","Матеріал":"шкіра","Відділення":"Один основний відділ","Комплект":"брендова коробка, пильник"} },

};

/* ===== Допоміжні функції ===== */

function getProductsByDept(deptKey) {
    var out = [];
    Object.keys(PRODUCTS).forEach(function (id) {
        if (PRODUCTS[id].dept === deptKey) {
            var p = PRODUCTS[id];
            out.push({
                id: id, dept: p.dept, category: p.category, brand: p.brand, name: p.name,
                price: p.price, code: p.code, images: p.images, video: p.video,
                description: p.description, specs: p.specs
            });
        }
    });
    return out;
}

function getAllProducts() {
    var out = [];
    Object.keys(PRODUCTS).forEach(function (id) {
        var p = PRODUCTS[id];
        out.push({
            id: id, dept: p.dept, category: p.category, brand: p.brand, name: p.name,
            price: p.price, code: p.code, images: p.images, video: p.video,
            description: p.description, specs: p.specs
        });
    });
    return out;
}

/* Список унікальних брендів у відділі, з фото-обкладинкою (перше фото
   першого товару цього бренду). Використовується для сторінки
   "Каталог -> Відділ -> бренди" перед показом самих товарів. */
function getBrandsByDept(deptKey) {
    var items = getProductsByDept(deptKey);
    var seen = {};
    var out = [];
    items.forEach(function (p) {
        var b = p.brand || "Інше";
        if (!seen[b]) {
            seen[b] = true;
            var logo = Object.prototype.hasOwnProperty.call(BRAND_LOGOS, b) ? BRAND_LOGOS[b] : "";
            out.push({
                brand: b,
                cover: logo || ((p.images && p.images.length) ? p.images[0] : ""),
                isLogo: !!logo
            });
        }
    });
    return out;
}

/* Товари конкретного бренду. deptKey необов'язковий — якщо вказаний,
   фільтрує ще й за відділом (сторінка "Відділ -> Бренд"); якщо ні —
   всі товари цього бренду з усіх відділів (посилання з футера). */
function getProductsByBrand(brandName, deptKey) {
    var items = deptKey ? getProductsByDept(deptKey) : getAllProducts();
    return items.filter(function (p) { return p.brand === brandName; });
}
