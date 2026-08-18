import pytest
from barbara.engine import BarbaraEngine
from barbara.state import CampaignState

class P:
    def __init__(self,patches): self.patches=patches
    def generate(self,*args): return {'narration':'A cena continua com detalhes suficientes para registrar a mudança.','claims':[],'state_patch':self.patches}

def test_valid_player_patch_is_committed_and_persisted():
    s=CampaignState('c','gurps'); e=BarbaraEngine(P([{'path':'player_notes.clue','value':'red key'}]))
    e.turn(s,'look','r')
    assert s.player_state['player_notes']['clue']=='red key'
    restored=CampaignState.from_json(s.to_json())
    assert restored.player_state==s.player_state

def test_scene_and_notes_patches_commit():
    s=CampaignState('c','gurps'); e=BarbaraEngine(P([{'path':'scene.light','value':'dim'},{'path':'notes.session','value':'clue found'}]))
    e.turn(s,'look','r')
    assert s.scene['light']=='dim' and s.notes['session']=='clue found'

def test_nested_patch_type_conflict_rolls_back_world_tick_and_all_patches():
    s=CampaignState('c','gurps',player_state={'player_notes':{'clue':'text'}})
    e=BarbaraEngine(P([{'path':'notes.ok','value':1},{'path':'player_notes.clue.deep','value':'bad'}]))
    with pytest.raises(ValueError,match='patch_path_type_conflict'): e.turn(s,'look','r')
    assert s.tick==0 and s.notes=={} and s.player_state=={'player_notes':{'clue':'text'}}

def test_provider_cannot_commit_structural_patch():
    s=CampaignState('c','gurps'); e=BarbaraEngine(P([{'path':'economy.cash','value':999999}]))
    with pytest.raises(ValueError): e.turn(s,'look','r')
    assert s.tick==0 and s.economy=={}

def test_patch_value_is_defensively_copied():
    value={'items':['key']}; s=CampaignState('c','gurps'); e=BarbaraEngine(P([{'path':'player_inventory.bag','value':value}]))
    e.turn(s,'look','r'); value['items'].append('poison')
    assert s.player_state['player_inventory']['bag']=={'items':['key']}
