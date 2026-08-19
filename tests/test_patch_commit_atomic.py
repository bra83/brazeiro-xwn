import pytest
from barbara.engine import BarbaraEngine
from barbara.state import CampaignState

class P:
    def __init__(self,patches): self.patches=patches
    def generate(self,*args): return {'narration':'A cena continua com detalhes suficientes para registrar a mudança.','claims':[],'state_patch':self.patches}

def assert_provider_patch_rejected(patches,state=None):
    s=state or CampaignState('c','gurps'); e=BarbaraEngine(P(patches))
    before=s.snapshot()
    with pytest.raises(ValueError,match='provider_state_patch_forbidden'):
        e.turn(s,'look','r')
    assert s.to_dict()==before.to_dict()
    return s

def test_provider_cannot_commit_player_patch():
    assert_provider_patch_rejected([{'path':'player_notes.clue','value':'red key'}])

def test_provider_cannot_commit_scene_or_notes_patch():
    assert_provider_patch_rejected([{'path':'scene.light','value':'dim'},{'path':'notes.session','value':'clue found'}])

def test_provider_patch_rejection_rolls_back_world_tick_atomically():
    s=CampaignState('c','gurps',npcs={'n':{'alive':True}},player_state={'player_notes':{'clue':'text'}})
    assert_provider_patch_rejected([{'path':'notes.ok','value':1},{'path':'player_notes.clue.deep','value':'bad'}],s)
    assert s.tick==0 and 'last_simulated_tick' not in s.npcs['n']

def test_provider_cannot_commit_structural_patch():
    s=assert_provider_patch_rejected([{'path':'economy.cash','value':999999}])
    assert s.economy=={}

def test_provider_patch_value_never_enters_state_even_if_mutated_after_rejection():
    value={'items':['key']}; s=CampaignState('c','gurps')
    assert_provider_patch_rejected([{'path':'player_inventory.bag','value':value}],s)
    value['items'].append('poison')
    assert s.player_state=={}
