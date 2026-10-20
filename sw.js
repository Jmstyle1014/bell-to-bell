// Offline support: the game shell is cached on install; fonts are cached the first time they load.
const CACHE = 'bell-to-bell-v5';
const JACK = ['idle', 'walk', 'slip', 'jab', 'jab-stiff', 'cross', 'hook', 'upper', 'hit', 'down', 'block', 'body-cross',
  'stunned', 'get-up', 'win', 'body-jab', 'block-hit', 'body-upper', 'body-hook', 'lose'].map(n => 'art/jack/' + n + '.webp');
const SHELL = ['./', 'index.html', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png', 'icon-maskable-512.png',
  'art/jack/index.json', ...JACK];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  // Page itself: network first so updates arrive, cache as fallback for offline play.
  if (req.mode === 'navigate') {
    e.respondWith(fetch(req).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put('index.html', copy));
      return res;
    }).catch(() => caches.match('index.html')));
    return;
  }
  // Everything else (icons, fonts): cache first.
  if (url.origin === location.origin || url.hostname.endsWith('gstatic.com') || url.hostname.endsWith('googleapis.com')) {
    e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put(req, copy));
      return res;
    })));
  }
});
