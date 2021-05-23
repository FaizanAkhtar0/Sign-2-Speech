self.addEventListener("install", (event)=>{
    event.waitUntill(
      caches.open("static").then((cache) => {
        return cache.addAll([
          "./",
          "./static/css/style.css",
          "./static/bs5/css/bootstrap-reboot.min.css",
          "./static/bs5/css/bootstrap-grid.min.css",
          "./static/bs5/css/bootstrap.min.css",
          "./static/bs5/js/bootstrap.min.js",
          "./static/img/favicon.png",
        ]);
      })
    );
});

self.addEventListener("fetch", e=>{
    e.respondWith(
        caches.match(e.request).then(response=>{
            return response || fetch(e.request);
        })
    );
// console.log(`Intercepting fetch request for: ${e.request.url}`)
});