from .security import public_view

class Memory:
    def remember(self,state,item): state.memory.append(item)
    def compact_context(self,state,limit=12): return public_view(state.memory[-limit:])
    def causal_trace(self,state,event_id):
        by={e.get("id"):e for e in state.events}; out=[]; cur=by.get(event_id); seen=set()
        while cur and cur.get("id") not in seen:
            seen.add(cur.get("id")); out.append(cur); cur=by.get(cur.get("causes"))
        return out
