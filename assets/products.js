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
            out.push({ brand: b, cover: (p.images && p.images.length) ? p.images[0] : "" });
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
