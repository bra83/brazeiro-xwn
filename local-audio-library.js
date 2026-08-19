(function(global){
  'use strict';
  const DB='braseiro-xwn-audio-v4',STORE='tracks';let dbPromise=null,current=null,currentUrl='';
  function supported(){return !!global.indexedDB;}
  function open(){if(!supported())return Promise.reject(new Error('indexeddb_unavailable'));if(dbPromise)return dbPromise;dbPromise=new Promise((resolve,reject)=>{const r=global.indexedDB.open(DB,1);r.onupgradeneeded=()=>{const db=r.result;if(!db.objectStoreNames.contains(STORE))db.createObjectStore(STORE,{keyPath:'id'});};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error||new Error('audio_db_error'));});return dbPromise;}
  async function tx(mode,fn){const db=await open();return new Promise((resolve,reject)=>{const t=db.transaction(STORE,mode),s=t.objectStore(STORE);let value;try{value=fn(s);}catch(e){reject(e);return;}t.oncomplete=()=>resolve(value);t.onerror=()=>reject(t.error||new Error('audio_tx_error'));});}
  async function add(file,name=''){if(!(file instanceof Blob))throw new Error('invalid_audio_file');if(file.size<=0||file.size>80*1024*1024)throw new Error('invalid_audio_size');const mime=String(file.type||'audio/mpeg');if(!/^audio\//i.test(mime))throw new Error('invalid_audio_type');const id=`track-${Date.now()}-${Math.random().toString(16).slice(2)}`,row={id,name:String(name||file.name||'Faixa local').slice(0,120),mime,size:file.size,createdAt:new Date().toISOString(),blob:file};await tx('readwrite',s=>s.put(row));return {...row,blob:undefined};}
  async function list(){const db=await open();return new Promise((resolve,reject)=>{const r=db.transaction(STORE,'readonly').objectStore(STORE).getAll();r.onsuccess=()=>resolve((r.result||[]).map(x=>({id:x.id,name:x.name,mime:x.mime,size:x.size,createdAt:x.createdAt})).sort((a,b)=>a.name.localeCompare(b.name)));r.onerror=()=>reject(r.error);});}
  async function get(id){const db=await open();return new Promise((resolve,reject)=>{const r=db.transaction(STORE,'readonly').objectStore(STORE).get(String(id));r.onsuccess=()=>resolve(r.result||null);r.onerror=()=>reject(r.error);});}
  async function remove(id){if(current?.dataset?.trackId===String(id))stop();await tx('readwrite',s=>s.delete(String(id)));return true;}
  function stop(){if(current){try{current.pause();current.currentTime=0;}catch(_){}}if(currentUrl){URL.revokeObjectURL(currentUrl);currentUrl='';}current=null;}
  async function play(id,{loop=false,volume=1}={}){stop();const row=await get(id);if(!row)throw new Error('audio_track_not_found');currentUrl=URL.createObjectURL(row.blob);const a=new Audio(currentUrl);a.dataset.trackId=row.id;a.loop=!!loop;a.volume=Math.max(0,Math.min(1,Number(volume)||0));a.onended=()=>{if(!a.loop)stop();};await a.play();current=a;return {id:row.id,name:row.name};}
  function status(){return {supported:supported(),database:DB,playing:current?.dataset?.trackId||null};}
  global.XWNLocalAudio={supported,add,list,get,remove,play,stop,status};
})(typeof window!=='undefined'?window:globalThis);
