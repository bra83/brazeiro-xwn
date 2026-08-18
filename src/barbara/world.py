from copy import deepcopy

class WorldTick:
    MAX_DEPTH=16; MAX_FANOUT=64
    def advance(self,state,mutator=None):
        draft=deepcopy(state); draft.tick+=1
        for npc in draft.npcs.values(): npc["last_simulated_tick"]=draft.tick
        if mutator: mutator(draft)
        self._process_events(draft)
        self._propagate_rumors(draft)
        self._validate(draft)
        state.__dict__.clear(); state.__dict__.update(draft.__dict__); return state
    def _process_events(self,state):
        spawned=[]
        due=[e for e in state.events if e.get('due_tick',state.tick)<=state.tick and not e.get('resolved')]
        for event in due:
            event['resolved']=True
            depth=int(event.get('depth',0))
            children=list(event.get('spawn_events',[]))
            if depth>=self.MAX_DEPTH: children=[]; event['causal_limit']='depth'
            if len(children)>self.MAX_FANOUT: children=children[:self.MAX_FANOUT]; event['causal_limit']='fanout'
            for i,child in enumerate(children):
                c=deepcopy(child); c.setdefault('id',f"{event.get('id','event')}:{i}")
                c['causes']=event.get('id'); c['depth']=depth+1
                c.setdefault('due_tick',state.tick+max(0,int(c.pop('delay',0))))
                c.setdefault('origin',event.get('origin'))
                spawned.append(c)
        state.events.extend(spawned)
    def _propagate_rumors(self,state):
        routes=state.world_flags.get('routes',[])
        edges=set()
        for a,b in routes:
            edges.add((a,b)); edges.add((b,a))
        for rumor in state.rumors:
            reached=set(rumor.get('reached',[])); reached.add(rumor.get('origin'))
            frontier=set(reached)
            for a,b in edges:
                if a in frontier: reached.add(b)
            rumor['reached']=sorted(x for x in reached if x is not None)
    def visible_rumors(self,state):
        return [deepcopy(r) for r in state.rumors if state.location in set(r.get('reached',[]))]
    def _validate(self,state):
        if not isinstance(state.tick,int) or isinstance(state.tick,bool): raise ValueError("invalid_tick")
        if not isinstance(state.events,list) or not isinstance(state.rumors,list): raise ValueError('invalid_world_collections')
        for npc in state.npcs.values():
            if "alive" in npc and not isinstance(npc["alive"],bool): raise ValueError("invalid_npc_alive")
            if "relationships" in npc and not isinstance(npc["relationships"],dict): raise ValueError("invalid_relationships")
