// Посередник між сайтом і Telegram: приймає заявку, перевіряє і шле в групу.
// Секрети (BOT_TOKEN, CHAT_ID) задаються через `wrangler secret put`, у коді їх немає.

const ALLOWED_ORIGINS = ['https://via-accessories.com.ua', 'https://www.via-accessories.com.ua'];
const SITE = 'https://via-accessories.com.ua';
const RATE_LIMIT = 5;
const RATE_WINDOW = 600; // секунд

function corsHeaders(origin) {
  return {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
    'Vary': 'Origin',
  };
}

function json(body, status, origin) {
  const headers = { 'Content-Type': 'application/json; charset=utf-8' };
  if (origin) Object.assign(headers, corsHeaders(origin));
  return new Response(JSON.stringify(body), { status, headers });
}

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

// Повертає +380XXXXXXXXX / +міжнародний номер або null
function normalizePhone(raw) {
  const s = String(raw || '');
  if (/[^\d\s()+\-.]/.test(s)) return null;
  const d = s.replace(/\D/g, '');
  let ua = null;
  if (/^380\d{9}$/.test(d)) ua = d;
  else if (/^0\d{9}$/.test(d)) ua = '38' + d;
  if (ua) return '+' + ua;
  if (/^\d{10,15}$/.test(d)) return '+' + d;
  return null;
}

// Простий ліміт через Cache API: лічильник на IP з TTL
async function rateLimited(ip) {
  const cache = caches.default;
  const key = new Request('https://rate.invalid/' + encodeURIComponent(ip));
  const hit = await cache.match(key);
  const count = hit ? parseInt(await hit.text(), 10) || 0 : 0;
  if (count >= RATE_LIMIT) return true;
  const ttl = hit ? Math.max(1, parseInt(hit.headers.get('X-Ttl') || RATE_WINDOW, 10)) : RATE_WINDOW;
  const expires = hit ? parseInt(hit.headers.get('X-Expires'), 10) : Date.now() + RATE_WINDOW * 1000;
  const left = Math.max(1, Math.round((expires - Date.now()) / 1000));
  await cache.put(key, new Response(String(count + 1), {
    headers: { 'Cache-Control': 'max-age=' + left, 'X-Expires': String(expires), 'X-Ttl': String(ttl) },
  }));
  return false;
}

function fmtMoney(n) {
  return new Intl.NumberFormat('uk-UA').format(n).replace(/ /g, ' ');
}

function buildMessage(name, phone, items, test) {
  let sum = 0;
  const lines = [];
  items.forEach((it, i) => {
    const priceTxt = it.price > 0 ? fmtMoney(it.price) + ' грн' : 'ціна уточнюється';
    if (it.price > 0) sum += it.price * it.qty;
    let l = (i + 1) + '. ' + esc(it.name) + (it.code ? ' (код: ' + esc(it.code) + ')' : '') +
      ' x ' + it.qty + ', ' + priceTxt;
    if (it.url) l += '\n    ' + esc(it.url);
    lines.push(l);
  });
  const time = new Intl.DateTimeFormat('uk-UA', {
    timeZone: 'Europe/Kyiv', dateStyle: 'short', timeStyle: 'short',
  }).format(new Date());
  return (test ? '🧪 ТЕСТ\n' : '') +
    '🛍 <b>Нове замовлення</b>\n' +
    '👤 Ім\'я: ' + esc(name) + '\n' +
    '📞 Телефон: <a href="tel:' + phone + '">' + phone + '</a>\n\n' +
    '<b>Товари:</b>\n' + lines.join('\n') + '\n\n' +
    '💰 Разом: <b>' + fmtMoney(sum) + ' грн</b>\n' +
    '🕒 ' + time + ' (Київ)';
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const allowed = ALLOWED_ORIGINS.includes(origin);

    if (request.method === 'OPTIONS') {
      return allowed
        ? new Response(null, { status: 204, headers: corsHeaders(origin) })
        : new Response(null, { status: 403 });
    }
    if (request.method !== 'POST') return json({ ok: false, error: 'Метод не підтримується' }, 405, allowed ? origin : null);
    if (!allowed) return json({ ok: false, error: 'Заборонено' }, 403, null);

    let data;
    try { data = await request.json(); } catch (e) { return json({ ok: false, error: 'Некоректний запит' }, 400, origin); }
    if (!data || typeof data !== 'object') return json({ ok: false, error: 'Некоректний запит' }, 400, origin);

    // Пастка для ботів: вдаємо успіх і нічого не шлемо
    if (data.website) return json({ ok: true }, 200, origin);

    const name = String(data.name || '').trim().replace(/\s+/g, ' ');
    if (name.length < 2 || name.length > 60) return json({ ok: false, error: 'Вкажіть ім\'я (від 2 до 60 символів)' }, 400, origin);

    const phone = normalizePhone(data.phone);
    if (!phone) return json({ ok: false, error: 'Вкажіть коректний номер телефону' }, 400, origin);

    if (!Array.isArray(data.items) || data.items.length === 0 || data.items.length > 30) {
      return json({ ok: false, error: 'Некоректний список товарів' }, 400, origin);
    }
    const items = [];
    for (const raw of data.items) {
      if (!raw || typeof raw !== 'object') return json({ ok: false, error: 'Некоректний список товарів' }, 400, origin);
      const nm = String(raw.name || '').trim().slice(0, 200);
      if (!nm) return json({ ok: false, error: 'Некоректний список товарів' }, 400, origin);
      let qty = Math.floor(Number(raw.qty));
      if (!(qty >= 1)) qty = 1;
      if (qty > 99) qty = 99;
      let price = Number(raw.price);
      if (!isFinite(price) || price < 0 || price > 10000000) price = 0;
      const url = typeof raw.url === 'string' && raw.url.startsWith(SITE + '/') ? raw.url.slice(0, 300) : '';
      items.push({ name: nm, code: String(raw.code || '').trim().slice(0, 50), price, qty, url });
    }

    const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
    if (await rateLimited(ip)) return json({ ok: false, error: 'Забагато заявок. Спробуйте пізніше' }, 429, origin);

    const text = buildMessage(name, phone, items, data.test === true);
    let res;
    try {
      res = await fetch('https://api.telegram.org/bot' + env.BOT_TOKEN + '/sendMessage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: env.CHAT_ID, text, parse_mode: 'HTML', disable_web_page_preview: true }),
      });
    } catch (e) {
      return json({ ok: false, error: 'Не вдалося відправити' }, 502, origin);
    }
    if (!res.ok) return json({ ok: false, error: 'Не вдалося відправити' }, 502, origin);
    return json({ ok: true }, 200, origin);
  },
};
