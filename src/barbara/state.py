from dataclasses import dataclass,field,asdict
from copy import deepcopy
import json

@dataclass
class CampaignState:
    campaign_id:str
    system_id:str
    tick:int=0
    location:str=''
    facts:dict=field(default_factory=dict)
    world_flags:dict=field(default_factory=dict)
    npcs:dict=field(default_factory=dict)
    factions:dict=field(default_factory=dict)
    rumors:list=field(default_factory=list)
    events:list=field(default_factory=list)
    memory:list=field(default_factory=list)
    clocks:dict=field(default_factory=dict)
    economy:dict=field(default_factory=dict)
    weather:dict=field(default_factory=dict)
    player_state:dict=field(default_factory=dict)
    scene:dict=field(default_factory=dict)
    notes:dict=field(default_factory=dict)
    sites:dict=field(default_factory=dict)
    public_ledger:list=field(default_factory=list)
    secret_ledger:list=field(default_factory=list)
    request_log:dict=field(default_factory=dict)
    discovery:dict=field(default_factory=dict)
    state_version:int=0
    event_log:list=field(default_factory=list)
    def snapshot(self): return deepcopy(self)
    def validate(self):
        if not isinstance(self.campaign_id,str) or not self.campaign_id: raise ValueError('invalid_campaign_id')
        if not isinstance(self.system_id,str) or not self.system_id: raise ValueError('invalid_system_id')
        if not isinstance(self.tick,int) or isinstance(self.tick,bool) or self.tick<0: raise ValueError('invalid_tick')
        if not isinstance(self.state_version,int) or isinstance(self.state_version,bool) or self.state_version<0: raise ValueError('invalid_state_version')
        if not isinstance(self.location,str): raise ValueError('invalid_location')
        for name in ('facts','world_flags','npcs','factions','clocks','economy','weather','player_state','scene','notes','sites','request_log','discovery'):
            if not isinstance(getattr(self,name),dict): raise ValueError('invalid_'+name)
        for name in ('rumors','events','event_log','memory','public_ledger','secret_ledger'):
            if not isinstance(getattr(self,name),list): raise ValueError('invalid_'+name)
        for entry in self.event_log:
            if not isinstance(entry,dict): raise ValueError('invalid_event_log_entry')
            if not isinstance(entry.get('event_id'),str) or not entry['event_id']: raise ValueError('invalid_event_log_entry')
            if not isinstance(entry.get('type'),str) or not entry['type']: raise ValueError('invalid_event_log_entry')
            if not isinstance(entry.get('request_id'),str) or not entry['request_id']: raise ValueError('invalid_event_log_entry')
            if not isinstance(entry.get('tick'),int) or isinstance(entry['tick'],bool) or entry['tick']<0: raise ValueError('invalid_event_log_entry')
        if 'campaign_started' in self.discovery and not isinstance(self.discovery['campaign_started'],bool): raise ValueError('invalid_discovery_campaign_started')
        if 'locations' in self.discovery and not isinstance(self.discovery['locations'],dict): raise ValueError('invalid_discovery_locations')
        for rid,entry in self.request_log.items():
            if not isinstance(rid,str) or not rid or len(rid)>160: raise ValueError('invalid_request_id')
            if not isinstance(entry,dict) or set(entry)!={'fingerprint','result'}: raise ValueError('invalid_request_log_entry')
            if not isinstance(entry['fingerprint'],list) or not isinstance(entry['result'],dict): raise ValueError('invalid_request_log_entry')
        return True
    def to_dict(self): self.validate(); return deepcopy(asdict(self))
    def to_json(self): return json.dumps(self.to_dict(),ensure_ascii=False,sort_keys=True,separators=(',',':'))
    @classmethod
    def from_dict(cls,data):
        if not isinstance(data,dict): raise ValueError('invalid_state_document')
        allowed={f.name for f in cls.__dataclass_fields__.values()}
        unknown=set(data)-allowed
        if unknown: raise ValueError('unknown_state_fields:'+','.join(sorted(unknown)))
        obj=cls(**deepcopy(data)); obj.validate(); return obj
    @classmethod
    def from_json(cls,raw):
        try: data=json.loads(raw)
        except (TypeError,json.JSONDecodeError) as e: raise ValueError('invalid_state_json') from e
        return cls.from_dict(data)
