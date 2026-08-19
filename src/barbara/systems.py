from dataclasses import dataclass, field
from copy import deepcopy
from .adapters import AdapterRegistry, SUPPORTED
from .time_model import default_time_model


@dataclass(frozen=True)
class SystemModule:
    system_id: str
    family: str
    capabilities: frozenset[str]
    mechanics: dict
    time_model: object
    schemas: dict = field(default_factory=dict)
    actions: tuple = ()
    inventory: dict = field(default_factory=dict)
    ui: dict = field(default_factory=dict)
    rag_sources: tuple = ()
    narrative: dict = field(default_factory=dict)
    migrations: tuple = ()

    def supports(self, capability):
        if not isinstance(capability, str) or not capability:
            raise ValueError('invalid_capability')
        return capability in self.capabilities

    def describe(self):
        return {'system_id': self.system_id, 'family': self.family, 'capabilities': sorted(self.capabilities), 'mechanics': deepcopy(self.mechanics), 'time': {'round_seconds': self.time_model.round.seconds, 'exploration_seconds': self.time_model.exploration_turn.seconds, 'travel_seconds': self.time_model.travel_turn.seconds}, 'schemas': deepcopy(self.schemas), 'actions': list(self.actions), 'inventory': deepcopy(self.inventory), 'ui': deepcopy(self.ui), 'rag_sources': list(self.rag_sources), 'narrative': deepcopy(self.narrative), 'migrations': list(self.migrations)}


class SystemModuleRegistry:
    def __init__(self, adapters=None):
        self.adapters = adapters or AdapterRegistry(); self._modules = {}
        for adapter in self.adapters.all():
            profile = adapter.mechanics_profile(); caps = frozenset(profile.pop('capabilities', []))
            self._modules[adapter.system_id] = SystemModule(adapter.system_id, adapter.family, caps, profile, default_time_model(adapter.system_id), schemas={'character': {'type': 'object'}, 'resolution': {'type': 'object'}}, actions=('action', 'dialogue', 'investigation', 'travel', 'combat'), inventory={'style': profile.get('resource_style')}, ui={'schema_driven': True}, narrative={'profile_key': adapter.system_id}, migrations=('1.0.0',))

    def get(self, system_id):
        if system_id not in self._modules: raise KeyError(system_id)
        return self._modules[system_id]

    def all(self): return tuple(self._modules[s] for s in SUPPORTED)
