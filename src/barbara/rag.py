from dataclasses import dataclass
import hashlib, math, re, sqlite3, json

INJECTION_PATTERNS=(r'ignore\s+(all|previous|prior)\s+(instructions|rules)',r'(reveal|print|expose)\s+.*(secret|system prompt|director)',r'you\s+are\s+now\s+',r'follow\s+these\s+instructions')
VALID_KINDS={"RULE","LORE","MEMORY","NPC","LOCATION","EVENT","INFERENCE"}

@dataclass(frozen=True)
class Evidence:
    source_id:str; text:str; kind:str; campaign_id:str; system_id:str; authority:float=1.0; secret:bool=False; vector:tuple|None=None
    @property
    def checksum(self): return hashlib.sha256(self.text.encode()).hexdigest()

class RAG:
    def __init__(self,db_path=None):
        self._docs={}; self._quarantine=[]; self.db_path=db_path
        self._db=sqlite3.connect(db_path) if db_path else None
        if self._db:
            self._db.execute('CREATE TABLE IF NOT EXISTS docs(campaign TEXT, system TEXT, source TEXT, idx INTEGER, text TEXT, kind TEXT, authority REAL, secret INTEGER, vector TEXT, checksum TEXT, PRIMARY KEY(campaign,system,source,idx))')
            self._db.execute('CREATE TABLE IF NOT EXISTS quarantine(campaign TEXT, system TEXT, source TEXT, checksum TEXT, PRIMARY KEY(campaign,system,source,checksum))')
            self._db.commit(); self._load()
    def close(self):
        if self._db: self._db.close(); self._db=None
    def _load(self):
        self._docs={}
        for c,s,src,i,text,kind,auth,secret,vec,_ in self._db.execute('SELECT campaign,system,source,idx,text,kind,authority,secret,vector,checksum FROM docs'):
            v=tuple(json.loads(vec)) if vec else None; self._docs[(c,s,src,i)]=Evidence(src,text,kind,c,s,auth,bool(secret),v)
        self._quarantine=[tuple(r) for r in self._db.execute('SELECT campaign,system,source,checksum FROM quarantine')]
    @property
    def quarantine(self): return tuple(self._quarantine)
    def _unsafe(self,text): return any(re.search(p,text,re.I) for p in INJECTION_PATTERNS)
    def _validate(self,d,source_id):
        if d.source_id!=source_id: raise ValueError('source_mismatch')
        if d.kind not in VALID_KINDS: raise ValueError('invalid_evidence_kind')
        if not isinstance(d.text,str) or not d.text.strip(): raise ValueError('empty_evidence')
        if not isinstance(d.authority,(int,float)) or isinstance(d.authority,bool) or not 0<=d.authority<=1: raise ValueError('invalid_authority')
        if d.vector is not None:
            if not isinstance(d.vector,(tuple,list)) or not d.vector or not all(isinstance(x,(int,float)) and not isinstance(x,bool) for x in d.vector): raise ValueError('invalid_vector')
    def replace_source(self,source_id,docs):
        staged=list(docs); scopes={(d.campaign_id,d.system_id) for d in staged}
        if len(scopes)>1: raise ValueError('mixed_source_scope')
        for d in staged: self._validate(d,source_id)
        accepted=[]; quarantined=[]
        for d in staged:
            (quarantined if self._unsafe(d.text) else accepted).append(d)
        if not staged: return
        c,s=next(iter(scopes))
        if self._db:
            try:
                with self._db:
                    self._db.execute('DELETE FROM docs WHERE campaign=? AND system=? AND source=?',(c,s,source_id))
                    for i,d in enumerate(accepted):
                        self._db.execute('INSERT INTO docs VALUES(?,?,?,?,?,?,?,?,?,?)',(c,s,source_id,i,d.text,d.kind,float(d.authority),int(d.secret),json.dumps(list(d.vector)) if d.vector is not None else None,d.checksum))
                    for d in quarantined:
                        self._db.execute('INSERT OR IGNORE INTO quarantine VALUES(?,?,?,?)',(c,s,source_id,d.checksum))
            except Exception:
                self._load(); raise
            self._load(); return
        fresh={k:v for k,v in self._docs.items() if not (k[0]==c and k[1]==s and k[2]==source_id)}
        for i,d in enumerate(accepted): fresh[(c,s,source_id,i)]=d
        self._docs=fresh
        for d in quarantined:
            q=(c,s,source_id,d.checksum)
            if q not in self._quarantine:self._quarantine.append(q)
    def _cosine(self,a,b):
        if a is None or b is None or len(a)!=len(b): return 0.0
        dot=sum(x*y for x,y in zip(a,b)); na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(y*y for y in b))
        return dot/(na*nb) if na and nb else 0.0
    def retrieve(self,query,campaign_id,system_id,kinds=None,allow_secret=False,limit=6,query_vector=None):
        if not isinstance(limit,int) or isinstance(limit,bool) or limit<1: raise ValueError('invalid_limit')
        q=set(re.findall(r'\w+',str(query).lower())); scored=[]
        for (c,s,_,_),d in self._docs.items():
            if c!=campaign_id or s!=system_id or (kinds and d.kind not in kinds) or (d.secret and not allow_secret): continue
            toks=set(re.findall(r'\w+',d.text.lower())); lexical=len(q&toks)/(1+math.log1p(len(toks))); vector=max(0.0,self._cosine(query_vector,d.vector)); score=(0.65*lexical+0.35*vector)*d.authority
            if score>0: scored.append((score,d))
        scored.sort(key=lambda x:(-x[0],x[1].source_id,x[1].checksum)); out=[]; per_source={}
        for _,d in scored:
            if per_source.get(d.source_id,0)>=2: continue
            out.append(d); per_source[d.source_id]=per_source.get(d.source_id,0)+1
            if len(out)>=limit: break
        return out
