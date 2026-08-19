(function(global){
  'use strict';
  const DB='braseiro-xwn-snapshots-v4',STORE='snapshots';let dbPromise=null;
  function supported(){return !!global.indexedDB;}
  function open(){if(!supported())return Promise.reject(new Error('indexeddb_unavailable'));if(dbPromise)return dbPromise;dbPromise=new Promise((resolve,reject)=>{const r=global.indexedDB.open(DB,1);r.onupgradeneeded=()=>{const db=r.result;if(!db.objectStoreNames.contains(STORE)){const s=db.createObjectStore(STORE,{keyPath:'id'});s.createIndex('system','system',{unique:false});s.createIndex('createdAt','createdAt',{unique:false});}};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error||new Error('snapshot_db_error'));});return dbPromise;}
  async function put(snapshot){if(!snapshot||snapshot.schema!=='braseiro-xwn-snapshot-1')throw new Error('invalid_snapshot');const row={...snapshot,id:snapshot.id||`snap-${Date.now()}-${Math.random().toString(16).slice(2)}`};const db=await open();await new Promise((resolve,reject)=>{const t=db.transaction(STORE,'readwrite');t.objectStore(STORE).put(row);t.oncomplete=resolve;t.onerror=()=>reject(t.error);});await trim(row.system,20);return {...row,state:undefined};}
  async function all(){const db=await open();return new Promise((resolve,reject)=>{const r=db.transaction(STORE,'readonly').objectStore(STORE).getAll();r.onsuccess=()=>resolve((r.result||[]).sort((a,b)=>String(b.createdAt).localeCompare(String(a.createdAt))));r.onerror=()=>reject(r.error);});}
  async function list(system){return (await all()).filter(x=>!system||x.system===system).map(x=>({id:x.id,label:x.label,system:x.system,campaignId:x.campaignId,day:x.day,hour:x.hour,createdAt:x.createdAt,sha:x.sha}));}
  async function get(id){const db=await open();return new Promise((resolve,reject)=>{const r=db.transaction(STORE,'readonly').objectStore(STORE).get(String(id));r.onsuccess=()=>resolve(r.result||null);r.onerror=()=>reject(r.error);});}
  async function remove(id){const db=await open();return new Promise((resolve,reject)=>{const t=db.transaction(STORE,'readwrite');t.objectStore(STORE).delete(String(id));t.oncomplete=()=>resolve(true);t.onerror=()=>reject(t.error);});}
  async function trim(system,max=20){const rows=(await all()).filter(x=>x.system===system);for(const row of rows.slice(max))await remove(row.id);}
  global.XWNSnapshotStore={supported,put,list,get,remove};
})(typeof window!=='undefined'?window:globalThis);
