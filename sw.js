const CACHE='braseiro-xwn-wwn-v300';
const SHARE_CACHE='braseiro-shares-v1';
const SHARE_KEY='./__shared_scene_image__';
const CORE=['./','./index.html','./styles.css','./app.js','./engine.js','./audioEngineV2.js','./gmBridge.js','./rules-index.js','./hex-library.js','./manifest.webmanifest','./assets/app-icon.svg'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE&&k!==SHARE_CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{
  const u=new URL(e.request.url);
  if(e.request.method==='POST'&&u.pathname.endsWith('/share-target/')){
    e.respondWith((async()=>{
      const data=await e.request.formData();
      const file=data.get('image');
      if(file&&file.size){const c=await caches.open(SHARE_CACHE);await c.put(SHARE_KEY,new Response(file,{headers:{'Content-Type':file.type||'image/png'}}));}
      return Response.redirect(new URL('./?shared-image=1',self.registration.scope).href,303);
    })());return;
  }
  if(e.request.method!=='GET')return;
  e.respondWith(caches.match(e.request).then(hit=>hit||fetch(e.request).then(res=>{if(res&&res.ok){const copy=res.clone();caches.open(CACHE).then(c=>c.put(e.request,copy));}return res;}).catch(()=>caches.match('./index.html'))));
});
