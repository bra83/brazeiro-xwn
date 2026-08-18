from copy import deepcopy

class WorldTick:
    MAX_DEPTH=16; MAX_FANOUT=64
    def advance(self,state,mutator=None):
        draft=deepcopy(state); draft.tick+=1
        self._run_npcs(draft); self._run_factions(draft); self._run_clocks(draft)
        if mutator: mutator(draft)
        self._process_events(draft); self._propagate_rumors(draft); self._validate(draft)
        state.__dict__.clear(); state.__dict__.update(draft.__dict__); return state
    def _run_npcs(self,state):
        for npc in state.npcs.values():
            npc['last_simulated_tick']=state.tick
            if npc.get('alive',True) is False: continue
            routine=npc.get('routine',{})
            if isinstance(routine,dict):
                slot=str(state.tick%24); dest=routine.get(slot,routine.get('default'))
                if dest is not None: npc['location']=dest
            goals=npc.get('goals',[])
            if isinstance(goals,list) and goals:
                npc['active_goal']=deepcopy(goals[(state.tick-1)%len(goals)])
    def _run_factions(self,state):
        for faction in state.factions.values():
            if not isinstance(faction,dict): continue
            clocks=faction.get('clocks',{})
            if isinstance(clocks,dict):
                for name,clock in clocks.items():
                    if isinstance(clock,dict) and clock.get('active',True):
                        value=clock.get('value',0); rate=clock.get('rate',1); maximum=clock.get('max',6)
                        if all(isinstance(x,int) and not isinstance(x,bool) for x in [value,rate,maximum]):
                            clock['value']=min(maximum,max(0,value+rate))
    def _run_clocks(self,state):
        clocks=getattr(state,'clocks',{})
        if not isinstance(clocks,dict): return
        for clock in clocks.values():
            if isinstance(clock,dict) and clock.get('active',True):
                v=clock.get('value',0); rate=clock.get('rate',1); mx=clock.get('max',6)
                if all(isinstance(x,int) and not isinstance(x,bool) for x in [v,rate,mx]): clock['value']=min(mx,max(0,v+rate))
    def _process_events(self,state):
        spawned=[]; due=[e for e in state.events if e.get('due_tick',state.tick)<=state.tick and not e.get('resolved')]
        for event in due:
            event['resolved']=True; depth=int(event.get('depth',0)); children=list(event.get('spawn_events',[]))
            if depth>=self.MAX_DEPTH: children=[]; event['causal_limit']='depth'
            if len(children)>self.MAX_FANOUT: children=children[:self.MAX_FANOUT]; event['causal_limit']='fanout'
            for i,child in enumerate(children):
                c=deepcopy(child); c.setdefault('id',f"{event.get('id','event')}:{i}"); c['causes']=event.get('id'); c['depth']=depth+1
                c.setdefault('due_tick',state.tick+max(0,int(c.pop('delay',0)))); c.setdefault('origin',event.get('origin')); spawned.append(c)
        state.events.extend(spawned)
    def _propagate_rumors(self,state):
        routes=state.world_flags.get('routes',[]); edges=set()
        for route in routes:
            if not isinstance(route,(list,tuple)) or len(route)!=2: continue
            a,b=route; edges.add((a,b)); edges.add((b,a))
        for rumor in state.rumors:
            speed=rumor.get('speed',1)
            if not isinstance(speed,int) or isinstance(speed,bool) or speed<0: speed=0
            reached=set(rumor.get('reached',[])); origin=rumor.get('origin')
            if origin is not None: reached.add(origin)
            for _ in range(speed):
                frontier=set(reached); reached.update(b for a,b in edges if a in frontier)
            rumor['reached']=sorted(reached,key=str)
    def visible_rumors(self,state): return [deepcopy(r) for r in state.rumors if state.location in set(r.get('reached',[]))]
    def _validate(self,state):
        if not isinstance(state.tick,int) or isinstance(state.tick,bool): raise ValueError('invalid_tick')
        if not isinstance(state.events,list) or not isinstance(state.rumors,list): raise ValueError('invalid_world_collections')
        for npc in state.npcs.values():
            if 'alive' in npc and not isinstance(npc['alive'],bool): raise ValueError('invalid_npc_alive')
            if 'relationships' in npc and not isinstance(npc['relationships'],dict): raise ValueError('invalid_relationships')
