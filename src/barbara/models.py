from dataclasses import dataclass, field
from typing import Any
@dataclass(frozen=True)
class Evidence:
    text:str; kind:str; source:str; authority:float=1.0; secret:bool=False
@dataclass
class CampaignState:
    campaign_id:str; system:str; tick:int=0; location:str=""; facts:dict[str,Any]=field(default_factory=dict); memory:list[dict]=field(default_factory=list); npcs:dict[str,dict]=field(default_factory=dict); factions:dict[str,dict]=field(default_factory=dict); rumors:list[dict]=field(default_factory=list); events:list[dict]=field(default_factory=list)
