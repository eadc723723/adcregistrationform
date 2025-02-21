const CACHE_NAME = "adc-form-v1";
const ASSETS_TO_CACHE = [
  "/register_student/",
  "/static/formapp/css/styles.css",
  "/static/formapp/css/register_student.css",
  "/static/formapp/js/register_student.js",
  "/static/formapp/images/icon-48x48.png",
  "/static/formapp/images/icon-192x192.png",
  "https://cdn.jsdelivr.net/npm/bulma@0.9.3/css/bulma.min.css",
  "https://cdn.jsdelivr.net/npm/slick-carousel/slick/slick.css",
  "https://cdn.jsdelivr.net/npm/slick-carousel/slick/slick-theme.css",
  "https://code.jquery.com/jquery-3.6.0.min.js",
  "https://cdn.jsdelivr.net/npm/slick-carousel/slick/slick.min.js",
];

self.addEventListener("install", (event) => {
  console.log("[Service Worker] Installing service worker...");
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => {
        console.log("[Service Worker] Caching assets");
        return cache.addAll(ASSETS_TO_CACHE);
      })
      .catch((error) => {
        console.error("[Service Worker] Cache addAll failed:", error);
      })
  );
});

self.addEventListener("fetch", (event) => {
  console.log(`[Service Worker] Fetching: ${event.request.url}`);
  event.respondWith(
    caches
      .match(event.request)
      .then((response) => {
        if (response) {
          console.log(`[Service Worker] Serving from cache: ${event.request.url}`);
          return response;
        }
        console.log(`[Service Worker] Fetching from network: ${event.request.url}`);
        return fetch(event.request).then((response) => {
          // Check if we received a valid response
          if (!response || response.status !== 200 || response.type !== "basic") {
            return response;
          }

          // Clone the response
          const responseToCache = response.clone();

          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });

          return response;
        });
      })

      .catch((error) => {
        console.error("[Service Worker] Fetch failed:", error);
        throw error;
      })
  );
});

self.addEventListener("activate", (event) => {
  console.log("[Service Worker] Activating service worker...");
  event.waitUntil(
    caches
      .keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME) {
              console.log(`[Service Worker] Deleting old cache: ${cacheName}`);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log("[Service Worker] Activation complete");
        return self.clients.claim();
      })
      .catch((error) => {
        console.error("[Service Worker] Activation failed:", error);
      })
  );
});
