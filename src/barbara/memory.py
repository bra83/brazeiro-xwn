from copy import deepcopy
import re
from .security import public_view

class Memory:
    MAX_ITEMS=1000
    def remember(self,state,item):
        if not isinstance(item,dict): raise ValueError('invalid_memory_item')
        entry=deepcopy(item)
        entry.setdefault('tick',state.tick)
        entry.setdefault('salience',0.5)
        sal=entry['salience']
        if not isinstance(sal,(int,float)) or isinstance(sal,bool) or not 0<=sal<=1: raise ValueError('invalid_salience')
        state.memory.append(entry)
        if len(state.memory)>self.MAX_ITEMS:
            indexed=list(enumerate(state.memory)); keep_new={i for i,_ in indexed[-self.MAX_ITEMS//2:]}; older=indexed[:-self.MAX_ITEMS//2]
            older.sort(key=lambda x:(-float(x[1].get('salience',0.5)),-int(x[1].get('tick',0)),x[0])); keep_old={i for i,_ in older[:self.MAX_ITEMS-len(keep_new)]}
            state.memory=[v for i,v in indexed if i in keep_new or i in keep_old]
    def _tokens(self,value): return set(re.findall(r'\w+',str(value).lower()))
    def compact_context(self,state,limit=12,query='',location=None):
        if not isinstance(limit,int) or isinstance(limit,bool) or limit<1: raise ValueError('invalid_memory_limit')
        public=public_view(state.memory); q=self._tokens(query); scored=[]; now=state.tick
        for i,m in enumerate(public):
            if not isinstance(m,dict): continue
            sal=float(m.get('salience',0.5)); tick=int(m.get('tick',0)); text=m.get('text',m.get('summary',m.get('event',m)))
            toks=self._tokens(text); relevance=(len(q&toks)/max(1,len(q))) if q else 0.0
            loc=m.get('location'); locality=1.0 if location and loc==location else 0.0
            recency=1.0/(1.0+max(0,now-tick)); score=0.45*sal+0.30*relevance+0.15*locality+0.10*recency
            scored.append((score,tick,i,m))
        selected=sorted(scored,key=lambda x:(-x[0],-x[1],-x[2]))[:limit]; selected.sort(key=lambda x:(x[1],x[2]))
        return deepcopy([x[3] for x in selected])
    def canonical_layers(self,state):
        return {'canonical_facts':deepcopy(state.facts),'campaign_state':{'tick':state.tick,'location':state.location,'player_state':deepcopy(state.player_state)},'event_log':deepcopy(state.event_log),'episodic_memory':deepcopy(state.memory),'npc_memory':{nid:deepcopy(npc.get('memory',[])) for nid,npc in state.npcs.items() if isinstance(npc,dict)},'semantic_memory':deepcopy(state.notes.get('semantic_memory',{})),'knowledge_graph':deepcopy(state.notes.get('knowledge_graph',{})),'summaries':deepcopy(state.notes.get('memory_summaries',{})),'inferences':deepcopy(state.notes.get('inferences',[])),'rumors':deepcopy(state.rumors)}
    def record_belief(self,state,npc_id,key,value,confidence=0.5):
        npc=state.npcs.get(npc_id)
        if not isinstance(npc,dict): raise ValueError('unknown_npc')
        if not isinstance(confidence,(int,float)) or isinstance(confidence,bool) or not 0<=confidence<=1: raise ValueError('invalid_confidence')
        beliefs=npc.setdefault('beliefs',{}); beliefs[str(key)]={'value':deepcopy(value),'confidence':float(confidence),'tick':state.tick}; return deepcopy(beliefs[str(key)])
    def record_inference(self,state,text,evidence_ids=()):
        if not isinstance(text,str) or not text.strip(): raise ValueError('invalid_inference')
        bucket=state.notes.setdefault('inferences',[]); entry={'text':text.strip(),'evidence_ids':list(evidence_ids),'tick':state.tick}; bucket.append(entry); return deepcopy(entry)
    def causal_trace(self,state,event_id):
        by={e.get('id'):e for e in state.events if isinstance(e,dict) and e.get('id') is not None}; out=[]; cur=by.get(event_id); seen=set()
        while cur and cur.get('id') not in seen:
            seen.add(cur.get('id')); out.append(deepcopy(cur)); cur=by.get(cur.get('causes'))
        return out
