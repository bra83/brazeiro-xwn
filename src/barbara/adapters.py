from dataclasses import dataclass

SUPPORTED=("dnd","mystara","mausritter","forbidden_lands","the_one_ring","gurps","worlds_without_number","stars_without_number","cities_without_number","ashes_without_number","tales_from_the_loop","traveller_2e")

@dataclass(frozen=True)
class Adapter:
    system_id:str
    family:str
    rules_required:bool=True
    lore_scope:str|None=None
    min_rule_authority:float=0.5
    def validate_campaign(self,state):
        if state.system_id!=self.system_id: raise ValueError('adapter_system_mismatch')
        return True
    def rules_ready(self,rag,campaign_id):
        if not self.rules_required: return True
        for (c,s,_,_),e in rag._docs.items():
            if c==campaign_id and s==self.system_id and e.kind=='RULE' and not e.secret and e.authority>=self.min_rule_authority: return True
        return False
    def narrator_profile(self,rag,campaign_id):
        return {
            'system_id':self.system_id,
            'family':self.family,
            'lore_scope':self.lore_scope,
            'rules_ready':self.rules_ready(rag,campaign_id),
            'min_rule_authority':self.min_rule_authority,
        }

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
