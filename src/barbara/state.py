from dataclasses import dataclass, field
from copy import deepcopy

@dataclass
class CampaignState:
    campaign_id: str
    system_id: str
    tick: int = 0
    location: str = ""
    facts: dict = field(default_factory=dict)
    world_flags: dict = field(default_factory=dict)
    npcs: dict = field(default_factory=dict)
    factions: dict = field(default_factory=dict)
    rumors: list = field(default_factory=list)
    events: list = field(default_factory=list)
    memory: list = field(default_factory=list)

    def snapshot(self):
        return deepcopy(self)
