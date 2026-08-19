import pytest
from barbara.adapters import AdapterRegistry,SUPPORTED
from barbara.engine import BarbaraEngine
from barbara.rag import Evidence
from barbara.state import CampaignState

class P:
    def __init__(self): self.context=None
    def generate(self,text,context,state): self.context=context; return {'narration':'O teste foi resolvido pelo sistema.','claims':[],'state_patch':[]}

def add_rule(e,system):
    e.rag.replace_source('core',[Evidence('core','attack combat test rule','RULE','c',system)])

def test_every_adapter_has_explicit_mechanics_profile():
    reg=AdapterRegistry()
    for system in SUPPORTED:
        p=reg.get(system).mechanics_profile()
        assert p['system_id']==system and p['family'] and p['roll_model'] and p['skill_model'] and p['combat_model']

def test_profiles_preserve_major_system_differences():
    reg=AdapterRegistry()
    assert reg.get('gurps').mechanics_profile()['roll_model']=='3d6_roll_under'
    assert reg.get('mausritter').mechanics_profile()['combat_model']=='auto_hit_damage'
    assert reg.get('forbidden_lands').mechanics_profile()['roll_model']=='d6_pool'
    assert reg.get('traveller_2e').mechanics_profile()['roll_model']=='2d6'
    assert reg.get('worlds_without_number').mechanics_profile()['skill_model']=='2d6_skill'

def test_mechanics_profile_reaches_narrator_and_host_result():
    p=P(); e=BarbaraEngine(p); s=CampaignState('c','gurps'); add_rule(e,'gurps')
    r=e.turn(s,'Faço um teste de ataque','r',resolution={'outcome':'success','source':'dice','total':9})
    assert p.context['system_profile']['mechanics']['roll_model']=='3d6_roll_under'
    assert r['system_profile']['mechanics']['family']=='gurps'
    assert p.context['resolution']['system_id']=='gurps'

def test_resolution_bound_to_wrong_system_is_rejected_before_tick():
    e=BarbaraEngine(); s=CampaignState('c','mausritter')
    with pytest.raises(ValueError,match='resolution_system_mismatch'):
        e.turn(s,'Olho a sala','r',resolution={'outcome':'success','system_id':'gurps'})
    assert s.tick==0

def test_resolution_bound_to_wrong_family_is_rejected_before_tick():
    e=BarbaraEngine(); s=CampaignState('c','forbidden_lands')
    with pytest.raises(ValueError,match='resolution_family_mismatch'):
        e.turn(s,'Olho a sala','r',resolution={'outcome':'success','family':'dnd'})
    assert s.tick==0

def test_unbound_resolution_is_normalized_to_active_adapter():
    e=BarbaraEngine(); s=CampaignState('c','traveller_2e')
    r=e.turn(s,'Olho a sala','r',resolution={'outcome':'success','source':'host'})
    assert r['resolution']['system_id']=='traveller_2e' and r['resolution']['family']=='traveller'

def test_xwn_variants_share_family_protocol_but_keep_identity():
    reg=AdapterRegistry()
    for system in ['worlds_without_number','stars_without_number','cities_without_number','ashes_without_number']:
        p=reg.get(system).mechanics_profile()
        assert p['family']=='xwn' and p['skill_model']=='2d6_skill' and p['system_id']==system

def test_mystara_keeps_dnd_mechanics_and_mystara_lore_scope():
    a=AdapterRegistry().get('mystara'); p=a.narrator_profile(BarbaraEngine().rag,'c')
    assert p['family']=='dnd' and p['lore_scope']=='mystara' and p['mechanics']['roll_model']=='d20'
