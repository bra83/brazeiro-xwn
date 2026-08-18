import pytest
from barbara.engine import BarbaraEngine
from barbara.state import CampaignState

class P:
    def __init__(self,out): self.out=out
    def generate(self,*args): return self.out

def rejected(out):
    s=CampaignState('c','gurps'); e=BarbaraEngine(P(out))
    with pytest.raises(ValueError): e.turn(s,'look','r')
    assert s.tick==0

def test_non_object_output_rejected_and_rolled_back(): rejected(123)
def test_empty_narration_rejected_and_rolled_back(): rejected({'narration':'','claims':[],'state_patch':[]})
def test_unknown_field_rejected(): rejected({'narration':'ok','claims':[],'state_patch':[],'director_secret':'x'})
def test_claims_must_be_strings(): rejected({'narration':'ok','claims':[{'fact':'x'}],'state_patch':[]})
def test_protected_patch_rejected_before_commit(): rejected({'narration':'ok','claims':[],'state_patch':[{'path':'npcs.bob.alive','value':False}]})
def test_malformed_patch_rejected(): rejected({'narration':'ok','claims':[],'state_patch':[{'path':'player_notes.x'}]})
def test_legacy_string_provider_is_normalized():
    s=CampaignState('c','gurps'); r=BarbaraEngine(P('A long scene.')).turn(s,'look','r')
    assert r['narration']=='A long scene.' and r['claims']==[] and r['state_patch']==[] and s.tick==1
