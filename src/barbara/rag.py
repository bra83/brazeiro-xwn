class RAG:
 def __init__(self): self.docs=[]
 def ingest(self,campaign,system,evidence):
  self.docs=[d for d in self.docs if not(d[0]==campaign and d[1]==system and d[2].source==evidence.source)]+[(campaign,system,evidence)]
 def retrieve(self,campaign,system,q,public=True,k=6):
  terms=set(q.lower().split()); out=[]
  for c,s,e in self.docs:
   if c!=campaign or s!=system or (public and e.secret): continue
   score=len(terms & set(e.text.lower().split()))*e.authority
   if score: out.append((score,e))
  return [e for _,e in sorted(out,key=lambda x:x[0],reverse=True)[:k]]
