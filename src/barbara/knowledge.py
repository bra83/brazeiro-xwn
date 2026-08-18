from copy import deepcopy
from .security import public_view

class KnowledgeBoundary:
    NPC_PUBLIC_FIELDS={
        'name','location','current_activity','mood','disposition','appearance','status','alive',
        'known_facts','heard_rumors','knowledge_public','relationships_public'
    }
    def visible_npcs(self,state):
        out={}
        for npc_id,npc in state.npcs.items():
            if not isinstance(npc,dict): continue
            if npc.get('location')!=state.location: continue
            public={k:deepcopy(v) for k,v in npc.items() if k in self.NPC_PUBLIC_FIELDS}
            cleaned=public_view(public)
            if cleaned: out[npc_id]=cleaned
        return out
    def npc_knows(self,state,npc_id,fact_id):
        npc=state.npcs.get(npc_id)
        if not isinstance(npc,dict): return False
        known=npc.get('known_facts',[])
        if isinstance(known,dict): return fact_id in known
        if isinstance(known,(list,tuple,set)): return fact_id in known
        return False
