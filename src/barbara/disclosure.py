class LoreDisclosureGate:
    """RAG retrieval is not permission to disclose."""
    def allowed_evidence(self, state, evidence, *, npc_id=None):
        out=[]; known=set()
        if npc_id is not None:
            npc=state.npcs.get(npc_id,{})
            raw=npc.get('known_facts',[]) if isinstance(npc,dict) else []
            known=set(raw.keys()) if isinstance(raw,dict) else set(raw if isinstance(raw,(list,tuple,set)) else [])
        for e in evidence:
            if getattr(e,'secret',False): continue
            source_id=getattr(e,'source_id',None); policy=getattr(e,'disclosure',None)
            if policy in {'gm_only','director_only','secret'}: continue
            if npc_id is not None and getattr(e,'kind',None) in {'LORE','MEMORY'} and source_id and known and source_id not in known: continue
            out.append(e)
        return out


class ContinuityGate:
    """Cross-check narrative against committed resolution/state."""
    def validate(self,narration,claims,state,resolution=None):
        if not isinstance(narration,str) or not narration.strip(): raise ValueError('invalid_narration')
        resolution=resolution or {}; outcome=resolution.get('outcome') if isinstance(resolution,dict) else None; low=narration.lower()
        if outcome in {'failure','failed'} and any(x in low for x in ('você consegue','você acerta','you succeed','you hit')): raise ValueError('continuity_resolution_contradiction')
        if outcome in {'success','succeeded'} and any(x in low for x in ('você falha','you fail')): raise ValueError('continuity_resolution_contradiction')
        for npc in state.npcs.values():
            if not isinstance(npc,dict) or npc.get('alive',True): continue
            name=str(npc.get('name','')).strip().lower()
            if name and name in low and any(x in low for x in ('permanece de pé','sorri para você','fala com você','stands up','speaks to you')): raise ValueError('continuity_canonical_contradiction')
        return True
