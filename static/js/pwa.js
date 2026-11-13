// ホーム画面に追加（PWA）・Service Worker 登録・オフライン表示
(function () {
    const standalone = () => (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) || window.navigator.standalone === true;
    let deferredPrompt = null;

    function showInstall() {
        const box = document.getElementById('install-box');
        if (!box || standalone()) return;
        const ua = navigator.userAgent || '';
        const ios = /iphone|ipad|ipod/i.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1);
        const text = document.getElementById('install-text');
        const btn = document.getElementById('install-btn');
        if (ios) { text.textContent = UI.install_ios; btn.classList.add('hidden'); box.classList.remove('hidden'); }
        else if (deferredPrompt) { text.textContent = UI.install_android; btn.classList.remove('hidden'); box.classList.remove('hidden'); }
    }

    window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); deferredPrompt = e; showInstall(); });
    window.addEventListener('appinstalled', () => { deferredPrompt = null; const b = document.getElementById('install-box'); if (b) b.classList.add('hidden'); });
    window.installApp = async function () {
        if (!deferredPrompt) return;
        deferredPrompt.prompt();
        try { await deferredPrompt.userChoice; } catch (e) {}
        deferredPrompt = null;
        showInstall();
    };

    // ---- 接続モード（スタート画面で選ぶ）。Service Worker もこの値に従う ----
    //   online : いつもどおり。通信できなくても勝手にオフライン画面へは切り替えない
    //   offline: 「/」を開くとオフライン画面（履歴・フレーズ集など）を出す
    const NET_KEY = 'tl_net_mode_v1', NET_CACHE = 'tookie-mode', NET_URL = '/__net_mode';
    window.getNetMode = function () {
        try { return localStorage.getItem(NET_KEY) === 'offline' ? 'offline' : 'online'; } catch (e) { return 'online'; }
    };
    window.setNetMode = async function (mode) {
        mode = mode === 'offline' ? 'offline' : 'online';
        try { localStorage.setItem(NET_KEY, mode); } catch (e) {}
        try { const c = await caches.open(NET_CACHE); await c.put(NET_URL, new Response(mode)); } catch (e) {}
    };
    // オフライン画面の「翻訳画面に戻る」: オンラインモードに戻してから開く
    window.leaveOffline = async function (ev) {
        if (ev) ev.preventDefault();
        await window.setNetMode('online');
        location.href = '/';
    };

    // オフライン表示（メイン画面の上のバナー／オフライン画面の状態表示）
    // navigator.onLine は当てにならないことがあるので、ブラウザが「オフライン」と言ったときは自分のサーバーに実際に届くか確かめる
    async function reachable() {
        if (navigator.onLine !== false) return true;
        try {
            const ctl = new AbortController();
            const t = setTimeout(() => ctl.abort(), 4000);
            const r = await fetch('/healthz', { cache: 'no-store', signal: ctl.signal });
            clearTimeout(t);
            return r.ok;
        } catch (e) { return false; }
    }
    async function syncOnline() {
        const online = await reachable();
        const banner = document.getElementById('offline-banner');
        if (banner) banner.classList.toggle('hidden', online);
        const status = document.getElementById('offline-status');
        if (status) {
            status.textContent = online ? UI.offline_back : UI.offline_title;
            status.classList.toggle('text-emerald-300', online);
            status.classList.toggle('text-amber-200', !online);
        }
    }
    window.addEventListener('online', syncOnline);
    window.addEventListener('offline', syncOnline);

    // オフライン画面は「サーバーに届かなかった」ときに出るので、最初は表示のまま。回線が戻ったときだけ文言を変える
    document.addEventListener('DOMContentLoaded', () => { if (!window.IS_OFFLINE_PAGE) syncOnline(); showInstall(); });

    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/sw.js', { scope: '/' }).then(() => {
                // オフライン画面の保存コピー（表示言語など）を最新にしておく
                if (navigator.onLine !== false) fetch('/offline', { credentials: 'same-origin' }).catch(() => {});
            }).catch(() => {});
        });
    }
})();
