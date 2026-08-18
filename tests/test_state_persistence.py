import pytest
from barbara.state import CampaignState

def test_state_roundtrip_is_lossless_and_deterministic():
    s=CampaignState('c','gurps',tick=7,location='office',facts={'a':1},npcs={'n':{'alive':True}},clocks={'doom':{'value':2}},economy={'cash':5},weather={'rain':True})
    raw=s.to_json(); restored=CampaignState.from_json(raw)
    assert restored==s and restored.to_json()==raw

def test_roundtrip_is_defensive_copy():
    data={'campaign_id':'c','system_id':'gurps','facts':{'x':[]}}
    s=CampaignState.from_dict(data); data['facts']['x'].append('corrupt')
    assert s.facts=={'x':[]}

def test_unknown_state_fields_fail_closed():
    with pytest.raises(ValueError): CampaignState.from_dict({'campaign_id':'c','system_id':'gurps','director_override':True})

def test_negative_or_boolean_tick_rejected():
    for tick in [-1,True]:
        with pytest.raises(ValueError): CampaignState('c','gurps',tick=tick).validate()

def test_collection_type_corruption_rejected():
    cases=[{'npcs':[]},{'events':{}},{'clocks':[]},{'economy':[]},{'memory':{}}]
    for kw in cases:
        with pytest.raises(ValueError): CampaignState('c','gurps',**kw).validate()

def test_malformed_json_rejected():
    for raw in ['{bad','[]','null']:
        with pytest.raises(ValueError): CampaignState.from_json(raw)
