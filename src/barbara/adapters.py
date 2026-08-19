from dataclasses import dataclass
from copy import deepcopy

SUPPORTED=("dnd","mystara","mausritter","forbidden_lands","the_one_ring","gurps","worlds_without_number","stars_without_number","cities_without_number","ashes_without_number","tales_from_the_loop","traveller_2e")

_MECHANICS={
 'dnd':{'roll_model':'d20','skill_model':'d20','combat_model':'d20','resource_style':'class_based'},
 'mystara':{'roll_model':'d20','skill_model':'d20','combat_model':'d20','resource_style':'class_based'},
 'mausritter':{'roll_model':'d20_roll_under','skill_model':'save_roll_under','combat_model':'auto_hit_damage','resource_style':'slot_inventory'},
 'forbidden_lands':{'roll_model':'d6_pool','skill_model':'year_zero_pool','combat_model':'year_zero_pool','resource_style':'conditions_and_resources'},
 'the_one_ring':{'roll_model':'feat_die_plus_success_dice','skill_model':'target_number','combat_model':'stance_and_attack_roll','resource_style':'endurance_hope_shadow'},
 'gurps':{'roll_model':'3d6_roll_under','skill_model':'3d6_roll_under','combat_model':'3d6_attack_defense','resource_style':'fp_hp'},
 'worlds_without_number':{'roll_model':'mixed','skill_model':'2d6_skill','combat_model':'d20_attack','resource_style':'xwn'},
 'stars_without_number':{'roll_model':'mixed','skill_model':'2d6_skill','combat_model':'d20_attack','resource_style':'xwn'},
 'cities_without_number':{'roll_model':'mixed','skill_model':'2d6_skill','combat_model':'d20_attack','resource_style':'xwn'},
 'ashes_without_number':{'roll_model':'mixed','skill_model':'2d6_skill','combat_model':'d20_attack','resource_style':'xwn'},
 'tales_from_the_loop':{'roll_model':'d6_pool','skill_model':'year_zero_pool','combat_model':'condition_driven','resource_style':'conditions'},
 'traveller_2e':{'roll_model':'2d6','skill_model':'2d6_target','combat_model':'2d6_attack','resource_style':'characteristics_and_damage'},
}

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
        if not self.rules_required:return True
        for (c,s,_,_),e in rag._docs.items():
            if c==campaign_id and s==self.system_id and e.kind=='RULE' and not e.secret and e.authority>=self.min_rule_authority:return True
        return False
    def mechanics_profile(self):
        profile=deepcopy(_MECHANICS[self.system_id]); profile.update({'system_id':self.system_id,'family':self.family})
        return profile
    def validate_resolution(self,resolution):
        if resolution is None:return None
        if not isinstance(resolution,dict):raise ValueError('invalid_resolution')
        bound=resolution.get('system_id')
        if bound is not None and bound!=self.system_id:raise ValueError('resolution_system_mismatch')
        family=resolution.get('family')
        if family is not None and family!=self.family:raise ValueError('resolution_family_mismatch')
        out=deepcopy(resolution); out.setdefault('system_id',self.system_id); out.setdefault('family',self.family); return out
    def narrator_profile(self,rag,campaign_id):
        return {'system_id':self.system_id,'family':self.family,'lore_scope':self.lore_scope,'rules_ready':self.rules_ready(rag,campaign_id),'min_rule_authority':self.min_rule_authority,'mechanics':self.mechanics_profile()}

class AdapterRegistry:
    def __init__(self):
        families={'dnd':'dnd','mystara':'dnd','mausritter':'mausritter','forbidden_lands':'year_zero','the_one_ring':'the_one_ring','gurps':'gurps','worlds_without_number':'xwn','stars_without_number':'xwn','cities_without_number':'xwn','ashes_without_number':'xwn','tales_from_the_loop':'year_zero','traveller_2e':'traveller'}
        self._items={k:Adapter(k,families[k],True,'mystara' if k=='mystara' else None) for k in SUPPORTED}
    def get(self,system_id):
        if system_id not in self._items:raise KeyError(system_id)
        return self._items[system_id]
    def all(self):return tuple(self._items[k] for k in SUPPORTED)
