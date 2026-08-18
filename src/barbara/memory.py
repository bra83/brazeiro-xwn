from copy import deepcopy
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
            # Retain highly salient memories plus the newest context; never mutate entries.
            indexed=list(enumerate(state.memory))
            keep_new={i for i,_ in indexed[-self.MAX_ITEMS//2:]}
            older=indexed[:-self.MAX_ITEMS//2]
            older.sort(key=lambda x:(-float(x[1].get('salience',0.5)),-int(x[1].get('tick',0)),x[0]))
            keep_old={i for i,_ in older[:self.MAX_ITEMS-len(keep_new)]}
            state.memory=[v for i,v in indexed if i in keep_new or i in keep_old]
    def compact_context(self,state,limit=12):
        if not isinstance(limit,int) or isinstance(limit,bool) or limit<1: raise ValueError('invalid_memory_limit')
        public=public_view(state.memory)
        scored=[]
        for i,m in enumerate(public):
            if not isinstance(m,dict): continue
            scored.append((float(m.get('salience',0.5)),int(m.get('tick',0)),i,m))
        selected=sorted(scored,key=lambda x:(-x[0],-x[1],-x[2]))[:limit]
        # Return selected memories chronologically so the narrator receives a coherent sequence.
        selected.sort(key=lambda x:(x[1],x[2]))
        return deepcopy([x[3] for x in selected])
    def causal_trace(self,state,event_id):
        by={e.get('id'):e for e in state.events if isinstance(e,dict) and e.get('id') is not None}; out=[]; cur=by.get(event_id); seen=set()
        while cur and cur.get('id') not in seen:
            seen.add(cur.get('id')); out.append(deepcopy(cur)); cur=by.get(cur.get('causes'))
        return out
