from dataclasses import dataclass
import hashlib, math, re

INJECTION_PATTERNS=(r'ignore\s+(all|previous|prior)\s+(instructions|rules)',r'(reveal|print|expose)\s+.*(secret|system prompt|director)',r'you\s+are\s+now\s+',r'follow\s+these\s+instructions')
VALID_KINDS={"RULE","LORE","MEMORY","NPC","LOCATION","EVENT","INFERENCE"}

@dataclass(frozen=True)
class Evidence:
    source_id:str; text:str; kind:str; campaign_id:str; system_id:str; authority:float=1.0; secret:bool=False
    @property
    def checksum(self): return hashlib.sha256(self.text.encode()).hexdigest()

class RAG:
    def __init__(self): self._docs={}; self._quarantine=[]
    @property
    def quarantine(self): return tuple(self._quarantine)
    def _unsafe(self,text):
        low=text.lower(); return any(re.search(p,low,re.I) for p in INJECTION_PATTERNS)
    def replace_source(self,source_id,docs):
        staged=list(docs)
        if any(d.source_id!=source_id for d in staged): raise ValueError('source_mismatch')
        scopes={(d.campaign_id,d.system_id) for d in staged}
        if len(scopes)>1: raise ValueError('mixed_source_scope')
        accepted=[]
        for d in staged:
            if d.kind not in VALID_KINDS: raise ValueError('invalid_evidence_kind')
            if not isinstance(d.text,str) or not d.text.strip(): raise ValueError('empty_evidence')
            if not isinstance(d.authority,(int,float)) or isinstance(d.authority,bool) or not 0<=d.authority<=1: raise ValueError('invalid_authority')
            if self._unsafe(d.text): self._quarantine.append((d.campaign_id,d.system_id,d.source_id,d.checksum)); continue
            accepted.append(d)
        # Validate and quarantine before touching the current source: replacement is atomic.
        if staged:
            campaign_id,system_id=next(iter(scopes))
            fresh={k:v for k,v in self._docs.items() if not (k[0]==campaign_id and k[1]==system_id and k[2]==source_id)}
            for i,d in enumerate(accepted): fresh[(d.campaign_id,d.system_id,source_id,i)]=d
            self._docs=fresh
    def retrieve(self,query,campaign_id,system_id,kinds=None,allow_secret=False,limit=6):
        if not isinstance(limit,int) or isinstance(limit,bool) or limit<1: raise ValueError('invalid_limit')
        q=set(re.findall(r'\w+',str(query).lower())); scored=[]
        for (c,s,_,_),d in self._docs.items():
            if c!=campaign_id or s!=system_id or (kinds and d.kind not in kinds) or (d.secret and not allow_secret): continue
            toks=set(re.findall(r'\w+',d.text.lower())); score=len(q&toks)*d.authority/(1+math.log1p(len(toks)))
            if score>0: scored.append((score,d))
        scored.sort(key=lambda x:(-x[0],x[1].source_id,x[1].checksum))
        out=[]; per_source={}
        for _,d in scored:
            if per_source.get(d.source_id,0)>=2: continue
            out.append(d); per_source[d.source_id]=per_source.get(d.source_id,0)+1
            if len(out)>=limit: break
        return out
