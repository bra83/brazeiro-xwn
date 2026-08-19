from copy import deepcopy

class WorldTick:
    MAX_DEPTH=16; MAX_FANOUT=64; MAX_NPC_MEMORY=100
    def advance(self,state,mutator=None):
        draft=deepcopy(state); draft.tick+=1
        self._run_npcs(draft); self._run_factions(draft); self._run_clocks(draft)
        if mutator: mutator(draft)
        self._process_events(draft); self._propagate_rumors(draft); self._update_npc_memory(draft); self._validate(draft)
        state.__dict__.clear(); state.__dict__.update(draft.__dict__); return state
    def _run_npcs(self,state):
        for npc in state.npcs.values():
            if not isinstance(npc,dict): continue
            npc['last_simulated_tick']=state.tick
            if npc.get('alive',True) is False: continue
            routine=npc.get('routine',{})
            if isinstance(routine,dict):
                slot=str(state.tick%24); dest=routine.get(slot,routine.get('default'))
                if dest is not None: npc['location']=dest
            goals=npc.get('goals',[])
            if isinstance(goals,list) and goals: npc['active_goal']=deepcopy(goals[(state.tick-1)%len(goals)])
    def _run_factions(self,state):
        interval=state.world_flags.get('faction_turn_interval',1)
        if not isinstance(interval,int) or isinstance(interval,bool) or interval<1: raise ValueError('invalid_faction_turn_interval')
        if state.tick%interval: return
        for faction in state.factions.values():
            if not isinstance(faction,dict): continue
            faction['last_turn_tick']=state.tick
            clocks=faction.get('clocks',{})
            if isinstance(clocks,dict):
                for clock in clocks.values():
                    if isinstance(clock,dict) and clock.get('active',True):
                        value=clock.get('value',0); rate=clock.get('rate',1); maximum=clock.get('max',6)
                        if all(isinstance(x,int) and not isinstance(x,bool) for x in [value,rate,maximum]): clock['value']=min(maximum,max(0,value+rate))
    def _run_clocks(self,state):
        for clock in state.clocks.values():
            if isinstance(clock,dict) and clock.get('active',True):
                v=clock.get('value',0); rate=clock.get('rate',1); mx=clock.get('max',6)
                if all(isinstance(x,int) and not isinstance(x,bool) for x in [v,rate,mx]): clock['value']=min(mx,max(0,v+rate))
    def _set_nested(self,target,path,value):
        if not isinstance(path,str) or not path or path.startswith('.') or '..' in path: raise ValueError('invalid_site_change_path')
        parts=path.split('.')
        if any(not p or p.startswith('_') for p in parts): raise ValueError('invalid_site_change_path')
        cur=target
        for part in parts[:-1]:
            old=cur.get(part)
            if old is None: cur[part]={}; old=cur[part]
            if not isinstance(old,dict): raise ValueError('site_change_type_conflict')
            cur=old
        cur[parts[-1]]=deepcopy(value)
    def _apply_event_effects(self,state,event):
        for change in event.get('site_changes',[]):
            if not isinstance(change,dict) or set(change)!={'site_id','path','value'}: raise ValueError('invalid_site_change')
            site_id=change['site_id']
            if not isinstance(site_id,str) or not site_id: raise ValueError('invalid_site_id')
            site=state.sites.setdefault(site_id,{})
            if not isinstance(site,dict): raise ValueError('invalid_site_state')
            self._set_nested(site,change['path'],change['value']); site['last_changed_tick']=state.tick
        summary=event.get('summary')
        if summary is not None:
            if not isinstance(summary,str) or not summary.strip(): raise ValueError('invalid_event_summary')
            entry={'event_id':event.get('id'),'tick':state.tick,'summary':summary,'origin':event.get('origin')}
            visibility=str(event.get('visibility','public')).lower()
            if visibility in {'secret','private','director','gm','gm_only','director_only'}: state.secret_ledger.append(entry)
            else: state.public_ledger.append(entry)
    def _process_events(self,state):
        spawned=[]; due=[e for e in state.events if isinstance(e,dict) and e.get('due_tick',state.tick)<=state.tick and not e.get('resolved')]
        for event in due:
            event['resolved']=True; event['resolved_tick']=state.tick; self._apply_event_effects(state,event)
            depth=int(event.get('depth',0)); children=list(event.get('spawn_events',[]))
            if depth>=self.MAX_DEPTH: children=[]; event['causal_limit']='depth'
            if len(children)>self.MAX_FANOUT: children=children[:self.MAX_FANOUT]; event['causal_limit']='fanout'
            for i,child in enumerate(children):
                if not isinstance(child,dict): raise ValueError('invalid_spawn_event')
                c=deepcopy(child); c.setdefault('id',f"{event.get('id','event')}:{i}"); c['causes']=event.get('id'); c['depth']=depth+1
                delay=c.pop('delay',0)
                if not isinstance(delay,int) or isinstance(delay,bool) or delay<0: raise ValueError('invalid_event_delay')
                c.setdefault('due_tick',state.tick+delay); c.setdefault('origin',event.get('origin')); spawned.append(c)
        state.events.extend(spawned)
    def _propagate_rumors(self,state):
        routes=state.world_flags.get('routes',[]); edges=set()
        for route in routes:
            if not isinstance(route,(list,tuple)) or len(route)!=2: continue
            a,b=route; edges.add((a,b)); edges.add((b,a))
        decay=state.world_flags.get('rumor_decay_per_hop',0.1)
        if not isinstance(decay,(int,float)) or isinstance(decay,bool) or not 0<=decay<=1: raise ValueError('invalid_rumor_decay')
        for rumor in state.rumors:
            if not isinstance(rumor,dict): raise ValueError('invalid_rumor')
            speed=rumor.get('speed',1)
            if not isinstance(speed,int) or isinstance(speed,bool) or speed<0: speed=0
            base=rumor.get('confidence',0.5)
            if not isinstance(base,(int,float)) or isinstance(base,bool) or not 0<=base<=1: raise ValueError('invalid_rumor_confidence')
            truth=rumor.get('truth_status','unknown')
            if truth not in {'unknown','true','false'}: raise ValueError('invalid_rumor_truth_status')
            reached=set(rumor.get('reached',[])); origin=rumor.get('origin'); confidence=dict(rumor.get('confidence_by_location',{}))
            if origin is not None: reached.add(origin); confidence.setdefault(str(origin),float(base))
            for _ in range(speed):
                frontier=set(reached)
                for a,b in edges:
                    if a not in frontier: continue
                    reached.add(b); source_conf=float(confidence.get(str(a),base)); new=max(0.0,source_conf-float(decay))
                    confidence[str(b)]=max(float(confidence.get(str(b),0.0)),new)
            rumor['reached']=sorted(reached,key=str); rumor['confidence_by_location']=confidence; rumor.setdefault('truth_status',truth)
    def _update_npc_memory(self,state):
        resolved=[e for e in state.events if isinstance(e,dict) and e.get('resolved_tick')==state.tick and e.get('summary')]
        for npc in state.npcs.values():
            if not isinstance(npc,dict) or npc.get('alive',True) is False: continue
            loc=npc.get('location'); memory=npc.setdefault('memory',[]); heard=npc.setdefault('heard_rumors',[])
            if not isinstance(memory,list) or not isinstance(heard,list): raise ValueError('invalid_npc_memory')
            known_event_ids={m.get('event_id') for m in memory if isinstance(m,dict)}
            for e in resolved:
                if e.get('origin')==loc and str(e.get('visibility','public')).lower()=='public' and e.get('id') not in known_event_ids:
                    memory.append({'event_id':e.get('id'),'summary':e.get('summary'),'observed_tick':state.tick})
            known_rumor_ids={r.get('id') for r in heard if isinstance(r,dict)}
            for rumor in state.rumors:
                if loc in set(rumor.get('reached',[])) and rumor.get('id') not in known_rumor_ids:
                    heard.append({'id':rumor.get('id'),'text':rumor.get('text',''),'confidence':rumor.get('confidence_by_location',{}).get(str(loc),rumor.get('confidence',0.5)),'heard_tick':state.tick})
            if len(memory)>self.MAX_NPC_MEMORY: del memory[:-self.MAX_NPC_MEMORY]
            if len(heard)>self.MAX_NPC_MEMORY: del heard[:-self.MAX_NPC_MEMORY]
    def visible_rumors(self,state):
        out=[]
        for rumor in state.rumors:
            if state.location not in set(rumor.get('reached',[])): continue
            r=deepcopy(rumor); r['confidence']=r.get('confidence_by_location',{}).get(str(state.location),r.get('confidence',0.5)); r.pop('truth_status',None)
            out.append(r)
        return out
    def _validate(self,state):
        state.validate()
        for npc in state.npcs.values():
            if not isinstance(npc,dict): raise ValueError('invalid_npc')
            if 'alive' in npc and not isinstance(npc['alive'],bool): raise ValueError('invalid_npc_alive')
            if 'relationships' in npc and not isinstance(npc['relationships'],dict): raise ValueError('invalid_relationships')
