/* TOOKIE Service Worker — 版が変わるたびに新しいキャッシュを作り、古いものは消す */
const VERSION = {{ version|tojson }};
const CACHE = 'tookie-' + VERSION;
const RUNTIME = 'tookie-runtime-v1';     // CDN（Tailwind・FontAwesome）は版をまたいで残す
const MODE_CACHE = 'tookie-mode';        // スタート画面で選んだ接続モード（online / offline）。ページ側が書き込む
const MODE_URL = '/__net_mode';
const OFFLINE_URL = '/offline';
const PRECACHE = {{ precache|tojson }};
const CDN_PRECACHE = {{ cdn|tojson }};
const CDN_HOSTS = {{ cdn_hosts|tojson }};

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const c = await caches.open(CACHE);
    // 1つ取れなくても全体を失敗させない
    await Promise.allSettled([OFFLINE_URL, ...PRECACHE].map((u) => c.add(new Request(u, { cache: 'reload' }))));
    const r = await caches.open(RUNTIME);
    await Promise.allSettled(CDN_PRECACHE.map((u) => r.add(new Request(u, { mode: u.endsWith('.css') || u.endsWith('.woff2') ? 'cors' : 'no-cors' }))));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keep = [CACHE, RUNTIME, MODE_CACHE];
    for (const k of await caches.keys()) if (!keep.includes(k)) await caches.delete(k);
    await self.clients.claim();
  })());
});

async function netMode() {
  try {
    const hit = await (await caches.open(MODE_CACHE)).match(MODE_URL);
    return hit && (await hit.text()) === 'offline' ? 'offline' : 'online';
  } catch (e) { return 'online'; }
}

// 最新があれば取る（2.5秒まで）。取れなければ端末に保存してあるオフライン画面
async function offlinePage() {
  try {
    const ctl = new AbortController();
    const t = setTimeout(() => ctl.abort(), 2500);
    const res = await fetch(OFFLINE_URL, { signal: ctl.signal, credentials: 'same-origin' });
    clearTimeout(t);
    if (res && res.ok) { (await caches.open(CACHE)).put(OFFLINE_URL, res.clone()); return res; }
  } catch (e) {}
  const cached = await caches.match(OFFLINE_URL);
  return cached || new Response('Offline', { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
}

// 画面の読み込み。オンラインモードでは何も差し替えない（通信できなければブラウザ本来のエラー）。
// オフラインモードのときだけ、「/」でオフライン画面を出し、通信に失敗した画面もオフライン画面にする
async function navigate(req) {
  if ((await netMode()) !== 'offline') return fetch(req);
  const u = new URL(req.url);
  if (req.method === 'GET' && u.origin === location.origin && u.pathname === '/') return offlinePage();
  try {
    return await fetch(req);
  } catch (e) {
    return offlinePage();
  }
}

async function cacheFirst(req) {
  const hit = await caches.match(req);
  if (hit) return hit;
  const res = await fetch(req);
  if (res && res.ok) (await caches.open(CACHE)).put(req, res.clone());
  return res;
}

async function networkFirstUpdate(req) {
  try {
    const res = await fetch(req);
    if (res && res.ok) (await caches.open(CACHE)).put(OFFLINE_URL, res.clone());
    return res;
  } catch (e) {
    const hit = await caches.match(OFFLINE_URL);
    if (hit) return hit;
    throw e;
  }
}

async function staleWhileRevalidate(req) {
  const cache = await caches.open(RUNTIME);
  const hit = await cache.match(req);
  const fresh = fetch(req).then((res) => {
    if (res && (res.ok || res.type === 'opaque')) cache.put(req, res.clone());
    return res;
  }).catch(() => null);
  return hit || (await fresh) || Response.error();
}

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.mode === 'navigate') {
    // /offline そのものを開いたときは最新を取りに行き、だめなら保存コピー
    const u = new URL(req.url);
    if (u.origin === location.origin && u.pathname === OFFLINE_URL && req.method === 'GET') {
      event.respondWith(networkFirstUpdate(req));
    } else {
      event.respondWith(navigate(req));
    }
    return;
  }
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin === location.origin) {
    if (url.pathname.startsWith('/static/')) event.respondWith(cacheFirst(req));
    else if (url.pathname === OFFLINE_URL) event.respondWith(networkFirstUpdate(req));
    return;   // API などはそのままネットワークへ
  }
  if (CDN_HOSTS.includes(url.hostname)) event.respondWith(staleWhileRevalidate(req));
});
