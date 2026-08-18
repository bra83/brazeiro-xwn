import copy
class World:
 def tick(self,state,steps=1):
  draft=copy.deepcopy(state)
  for _ in range(steps):
   draft.tick+=1
   for n in draft.npcs.values(): n["last_simulated_tick"]=draft.tick
   due=[e for e in draft.events if e.get("at",10**18)<=draft.tick and not e.get("done")]
   for e in due:
    e["done"]=True
    for child in e.get("spawn_events",[])[:64]:
     if child.get("depth",0)<=16: draft.events.append(child)
  return draft
