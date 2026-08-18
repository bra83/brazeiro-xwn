import pytest
from barbara.security import public_view,validate_patch

def test_top_level_private_fails_closed():
    assert public_view({'visibility':'director','text':'kill the king'})=={}

def test_recursive_sensitive_aliases_removed():
    raw={'a':[{'private_goal':'betray'},{'x':({'gm_only':'poison'}, {'safe':'yes'})}], 'safe':'ok'}
    out=public_view(raw); blob=repr(out)
    assert 'betray' not in blob and 'poison' not in blob and out['safe']=='ok'

def test_visibility_case_insensitive():
    assert public_view({'visibility':'GM_ONLY','text':'hidden'})=={}

def test_patch_protected_structural_roots():
    for root in ['economy','clocks','weather','living_world','authorizations','facts','npcs']:
        with pytest.raises(ValueError): validate_patch(root+'.x',1)

def test_patch_rejects_malformed_paths():
    for p in ['', '.facts','player_notes..facts','player_notes._internal','_private.x']:
        with pytest.raises(ValueError): validate_patch(p,1)

def test_patch_allows_explicit_public_namespaces():
    for p in ['player_notes.clue','player_preferences.voice','scene.description','notes.session']:
        assert validate_patch(p,'x')
