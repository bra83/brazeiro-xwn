import pytest
from barbara.adapters import AdapterRegistry


def test_system_capabilities_replace_system_name_conditionals_for_features():
    reg=AdapterRegistry()
    assert reg.supports('gurps','combat.hit_locations')
    assert not reg.supports('mausritter','combat.hit_locations')
    assert reg.supports('mausritter','inventory.slot_zones')
    assert reg.supports('forbidden_lands','roll.push')
    assert reg.supports('traveller_2e','vehicles.starships')


def test_every_system_exposes_common_runtime_capabilities():
    reg=AdapterRegistry()
    for adapter in reg.all():
        assert adapter.supports('rules.deterministic')
        assert adapter.supports('actions.interruptible')
        assert adapter.supports('dice.ast')


def test_capabilities_are_visible_to_narrator_profile_and_mechanics_profile():
    reg=AdapterRegistry(); a=reg.get('gurps')
    assert 'combat.hit_locations' in a.mechanics_profile()['capabilities']


def test_invalid_capability_name_fails_closed():
    with pytest.raises(ValueError): AdapterRegistry().get('gurps').supports('')
