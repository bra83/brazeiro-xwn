from copy import deepcopy

class WorldTick:
    MAX_DEPTH=16; MAX_FANOUT=64
    def advance(self,state,mutator=None):
        draft=deepcopy(state); draft.tick+=1
        for npc in draft.npcs.values(): npc["last_simulated_tick"]=draft.tick
        if mutator: mutator(draft)
        self._validate(draft)
        state.__dict__.clear(); state.__dict__.update(draft.__dict__); return state
    def _validate(self,state):
        if not isinstance(state.tick,int) or isinstance(state.tick,bool): raise ValueError("invalid_tick")
        for npc in state.npcs.values():
            if "alive" in npc and not isinstance(npc["alive"],bool): raise ValueError("invalid_npc_alive")
            if "relationships" in npc and not isinstance(npc["relationships"],dict): raise ValueError("invalid_relationships")
