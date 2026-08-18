from dataclasses import dataclass

SUPPORTED=("dnd","mystara","mausritter","forbidden_lands","the_one_ring","gurps","worlds_without_number","stars_without_number","cities_without_number","ashes_without_number","tales_from_the_loop","traveller_2e")

@dataclass(frozen=True)
class Adapter:
    system_id:str
    family:str
    rules_required:bool=True
    lore_scope:str|None=None
    def validate_campaign(self,state):
        if state.system_id!=self.system_id: raise ValueError('adapter_system_mismatch')
        return True
    def rules_ready(self,rag,campaign_id):
        if not self.rules_required: return True
        # Readiness means at least one canonical RULE exists in the exact campaign/system scope.
        for (c,s,_,_),e in rag._docs.items():
            if c==campaign_id and s==self.system_id and e.kind=='RULE' and not e.secret and e.authority>0: return True
        return False

class AdapterRegistry:
    def __init__(self):
        families={
          'dnd':'dnd','mystara':'dnd','mausritter':'mausritter','forbidden_lands':'year_zero',
          'the_one_ring':'the_one_ring','gurps':'gurps','worlds_without_number':'xwn','stars_without_number':'xwn',
          'cities_without_number':'xwn','ashes_without_number':'xwn','tales_from_the_loop':'year_zero','traveller_2e':'traveller'}
        self._items={k:Adapter(k,families[k],True,'mystara' if k=='mystara' else None) for k in SUPPORTED}
    def get(self,system_id):
        if system_id not in self._items: raise KeyError(system_id)
        return self._items[system_id]
    def all(self): return tuple(self._items[k] for k in SUPPORTED)
