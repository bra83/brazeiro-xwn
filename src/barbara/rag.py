from dataclasses import dataclass
import hashlib, math, re

@dataclass(frozen=True)
class Evidence:
    source_id:str; text:str; kind:str; campaign_id:str; system_id:str; authority:float=1.0; secret:bool=False
    @property
    def checksum(self): return hashlib.sha256(self.text.encode()).hexdigest()

class RAG:
    def __init__(self): self._docs={}
    def replace_source(self, source_id, docs):
        staged=list(docs)
        if any(d.source_id!=source_id for d in staged): raise ValueError("source_mismatch")
        # A source identity is scoped by campaign + system. Reingesting one
        # campaign must never delete an identically named source elsewhere.
        scopes={(d.campaign_id,d.system_id) for d in staged}
        if len(scopes)>1: raise ValueError("mixed_source_scope")
        if staged:
            campaign_id, system_id=next(iter(scopes))
            self._docs={k:v for k,v in self._docs.items()
                        if not (k[0]==campaign_id and k[1]==system_id and k[2]==source_id)}
        for i,d in enumerate(staged): self._docs[(d.campaign_id,d.system_id,source_id,i)]=d
    def retrieve(self, query, campaign_id, system_id, kinds=None, allow_secret=False, limit=6):
        q=set(re.findall(r"\w+",query.lower()))
        scored=[]
        for (c,s,_,_),d in self._docs.items():
            if c!=campaign_id or s!=system_id or (kinds and d.kind not in kinds) or (d.secret and not allow_secret): continue
            toks=set(re.findall(r"\w+",d.text.lower())); score=len(q&toks)*d.authority/(1+math.log1p(len(toks)))
            if score>0: scored.append((score,d))
        scored.sort(key=lambda x:x[0], reverse=True)
        out=[]; per_source={}
        for _,d in scored:
            if per_source.get(d.source_id,0)>=2: continue
            out.append(d); per_source[d.source_id]=per_source.get(d.source_id,0)+1
            if len(out)>=limit: break
        return out
