from copy import deepcopy
import hashlib,json,re
from .rag import RAG
from .rules import RuleGate
from .world import WorldTick
from .memory import Memory
from .security import public_view
from .recovery import RecoveryPolicy
from .narrative import NarrativePolicy
from .knowledge import KnowledgeBoundary
from .grounding import ClaimGrounding
from .telemetry import Telemetry
from .adapters import AdapterRegistry
from .mechanics import MechanicsAuthority
from .effects import EffectResolver

class BarbaraEngine:
    MAX_NARRATION=20000
    MAX_REQUEST_LOG=1000
    _RETRIEVAL_HINTS={'combat':'combat attack ataque ataco golpe strike fight damage dano defense defesa','travel':'travel journey viagem viajo road estrada trail trilha movement movimento','investigation':'investigation investigate investigação exam examine examino search procura clue pista perception percepção','dialogue':'dialogue social conversa persuasion persuasão reaction reação influence influência','action':'action ação check teste skill perícia ability habilidade','meta':'rule regra rules regras mechanics mecânica'}
    def __init__(self,provider=None,recovery=None,narrative=None,knowledge=None,grounding=None,rag=None,rag_db_path=None,embedder=None,telemetry=None,adapters=None,mechanics=None,effects=None):
        if rag is not None and rag_db_path is not None:raise ValueError('rag_configuration_conflict')
        self.provider=provider; self.rag=rag if rag is not None else RAG(rag_db_path); self.rules=RuleGate(); self.world=WorldTick(); self.memory=Memory(); self.recovery=recovery or RecoveryPolicy(); self.narrative=narrative or NarrativePolicy(); self.knowledge=knowledge or KnowledgeBoundary(); self.grounding=grounding or ClaimGrounding(); self.embedder=embedder; self.telemetry=telemetry or Telemetry(); self.adapters=adapters or AdapterRegistry(); self.mechanics=mechanics or MechanicsAuthority(); self.effects=effects or EffectResolver(); self._request_bindings={}
    def _fingerprint(self,state,text,mechanical,importance,resolution):return [state.campaign_id,state.system_id,text,mechanical,importance,deepcopy(resolution)]
    def _validate_request_id(self,request_id):
        if not isinstance(request_id,str) or not request_id or len(request_id)>160:raise ValueError('invalid_request_id')
    def _validate_expected_state_version(self,state,expected_state_version):
        if expected_state_version is None:return
        if not isinstance(expected_state_version,int) or isinstance(expected_state_version,bool) or expected_state_version<0:raise ValueError('invalid_expected_state_version')
        if expected_state_version!=state.state_version:raise ValueError('state_version_conflict')
    def _binding_key(self,state,request_id):return (state.campaign_id,request_id)
    def _check_binding(self,state,request_id,fingerprint):
        entry=self._request_bindings.get(self._binding_key(state,request_id))
        if entry is None:return None
        if entry['fingerprint']!=fingerprint:raise ValueError('request_id_collision')
        return deepcopy(entry['result'])
    def _bind_request(self,state,request_id,fingerprint,result):self._request_bindings[self._binding_key(state,request_id)]={'fingerprint':deepcopy(fingerprint),'result':deepcopy(result)}
    def _retrieval_query(self,text,plan,rule_required=False):
        q=str(text)
        if rule_required:
            hint=self._RETRIEVAL_HINTS.get(plan.get('kind'),'')
            if hint:q=f'{q} {hint}'
        return q
    def _query_vector(self,text):
        if self.embedder is None:return None
        fn=getattr(self.embedder,'embed',None)
        if not callable(fn):raise ValueError('invalid_embedder')
        vector=fn(text)
        if not isinstance(vector,(list,tuple)) or not vector or not all(isinstance(x,(int,float)) and not isinstance(x,bool) for x in vector):raise ValueError('invalid_query_vector')
        return tuple(float(x) for x in vector)
    def _error_code(self,exc):
        msg=str(exc).split(':',1)[0]; return msg if re.fullmatch(r'[A-Za-z0-9_\-]{1,80}',msg or '') else exc.__class__.__name__
    def _adapter(self,state):
        try:adapter=self.adapters.get(state.system_id)
        except KeyError as exc:raise ValueError(f'unsupported_system:{state.system_id}') from exc
        adapter.validate_campaign(state); return adapter
    def _system_profile(self,state):return self._adapter(state).narrator_profile(self.rag,state.campaign_id)
    def _public_world_context(self,state):
        site=deepcopy(state.sites.get(state.location,{})) if state.location else {}; ledger=[deepcopy(e) for e in state.public_ledger[-20:] if isinstance(e,dict) and (e.get('origin') in {None,state.location} or state.location=='')]; return {'site':public_view(site),'ledger':public_view(ledger)}
    def _world_imprint(self,state):
        world=self._public_world_context(state); data={'location':state.location,'site':world['site'],'ledger':world['ledger'],'weather':public_view(state.weather),'economy':public_view(state.economy)}
        raw=json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':'),default=str).encode(); return hashlib.sha256(raw).hexdigest()
    def _story_occasion(self,state,plan):
        if plan.get('mode')!='fiction' or not state.location:return 'continuation'
        discovery=state.discovery; locations=discovery.get('locations',{})
        if not discovery.get('campaign_started',False):return 'campaign_opening'
        previous=locations.get(state.location)
        if not isinstance(previous,dict):return 'first_arrival'
        if previous.get('imprint')!=self._world_imprint(state):return 'changed_return'
        return 'continuation'
    def _mark_discovery(self,state,plan):
        if plan.get('mode')!='fiction' or not state.location:return
        state.discovery['campaign_started']=True; locations=state.discovery.setdefault('locations',{})
        locations[state.location]={'last_seen_tick':state.tick,'imprint':self._world_imprint(state)}
    def narrator_context(self,state,evidence,text='',importance='normal',turn_plan=None,resolution=None):
        safe=[{'source_id':e.source_id,'kind':e.kind,'text':e.text,'checksum':e.checksum} for e in evidence if not e.secret]; qcount=self.narrative.question_count(text); world=self._public_world_context(state); memories=self.memory.compact_context(state,query=text,location=state.location); occasion=(turn_plan or {}).get('story_obligation','continuation')
        return public_view({'location':state.location,'facts':state.facts,'memory':memories,'rumors':self.world.visible_rumors(state),'npcs':self.knowledge.visible_npcs(state),'site':world['site'],'public_ledger':world['ledger'],'world_state_for_dramatization':{'weather':state.weather,'economy':state.economy},'world_experience':{'occasion':occasion,'player_has_preexisting_local_knowledge':occasion not in {'campaign_opening','first_arrival'},'instruction':'Transform current world state into perceivable fiction. Do not report hidden/global state as a briefing.'},'evidence':safe,'resolution':deepcopy(resolution),'system_profile':self._system_profile(state),'narrative_policy':self.narrative.narrator_directives(importance,qcount,turn_plan)})
    def _validate_provider_output(self,out,state,evidence,context,user_text,importance='normal',plan=None,resolution=None):
        legacy_string=isinstance(out,str); legacy_opt_out=bool(legacy_string and getattr(self.provider,'legacy_text',False))
        if legacy_string:out={'narration':out,'claims':[]}
        if not isinstance(out,dict):raise ValueError('invalid_provider_output')
        if set(out)-{'narration','claims','state_patch'}:raise ValueError('unknown_provider_field')
        narration=out.get('narration'); claims=out.get('claims',[]); patches=out.get('state_patch',[])
        if patches not in (None,[]):raise ValueError('provider_state_patch_forbidden')
        if not isinstance(narration,str) or not narration.strip() or len(narration)>self.MAX_NARRATION:raise ValueError('invalid_narration')
        if len(narration)<self.narrative.minimum_acceptable_chars(importance):raise ValueError('narrativa_resumida_demais')
        self.narrative.validate_player_agency(user_text,narration); self.mechanics.validate_narration(narration,bool(plan and plan.get('check_required')),resolution)
        if not legacy_opt_out:
            self.narrative.validate_response_coverage(user_text,narration); self.narrative.validate_scene_ending(narration,importance)
            if getattr(self.provider,'enforce_story_contract',False):self.narrative.validate_story_obligation(narration,(plan or {}).get('story_obligation','continuation'))
        claims=self.grounding.validate(claims,state,evidence,self.world.visible_rumors(state),public_context=context)
        return {'narration':narration,'claims':deepcopy(claims)}
    def _remember_request(self,state,request_id,fingerprint,result):
        state.request_log[request_id]={'fingerprint':deepcopy(fingerprint),'result':deepcopy(result)}
        if len(state.request_log)>self.MAX_REQUEST_LOG:
            victim=min(state.request_log,key=lambda rid:(int(state.request_log[rid].get('result',{}).get('tick',0)),rid))
            if victim!=request_id:state.request_log.pop(victim,None)
            else:
                others=[rid for rid in state.request_log if rid!=request_id]
                if others:state.request_log.pop(min(others,key=lambda rid:(int(state.request_log[rid].get('result',{}).get('tick',0)),rid)),None)
    def _append_turn_event(self,state,request_id,state_version,text,plan,resolution):
        payload={'mode':plan['mode'],'world_advanced':bool(plan['world_advances']),'text':text}
        if isinstance(resolution,dict):
            payload['outcome']=resolution.get('outcome'); payload['resolution_id']=resolution.get('resolution_id')
        event={'event_id':f'{request_id}:turn','type':'turn_committed','request_id':request_id,'tick':state.tick,'state_version':state_version,'payload':payload}
        state.event_log.append(event); return event['event_id']
    def _commit_draft(self,state,draft):
        draft.validate(); state.__dict__.clear(); state.__dict__.update(deepcopy(draft.__dict__)); state.validate()
    def turn(self,state,text,request_id,mechanical=False,importance='normal',resolution=None,expected_state_version=None):
        self._validate_request_id(request_id); state.validate(); adapter=self._adapter(state); base_plan=self.narrative.turn_plan(text,mechanical,importance); inferred=self.mechanics.requires_rule(text,mechanical,base_plan); effective_mechanical=bool(mechanical or (inferred and base_plan['mode']=='fiction')); plan=self.narrative.turn_plan(text,effective_mechanical,importance); plan=self.narrative.apply_story_obligation(plan,self._story_occasion(state,plan)); trusted_resolution=adapter.validate_resolution(self.mechanics.validate_resolution(resolution)); profile=adapter.narrator_profile(self.rag,state.campaign_id); fingerprint=self._fingerprint(state,text,effective_mechanical,importance,trusted_resolution)
        bound=self._check_binding(state,request_id,fingerprint)
        if bound is not None:self.telemetry.record('turn','idempotent',campaign=state.campaign_id,system=state.system_id); return bound
        if request_id in state.request_log:
            entry=state.request_log[request_id]
            if entry['fingerprint']!=fingerprint:raise ValueError('request_id_collision')
            self._bind_request(state,request_id,fingerprint,entry['result']); self.telemetry.record('turn','idempotent',campaign=state.campaign_id,system=state.system_id); return deepcopy(entry['result'])
        self._validate_expected_state_version(state,expected_state_version)
        try:
            gate_required=bool(effective_mechanical or (self.provider is not None and inferred and plan['mode']=='meta')); retrieval_query=self._retrieval_query(text,plan,gate_required); query_vector=self._query_vector(retrieval_query); evidence=self.rag.retrieve(retrieval_query,state.campaign_id,state.system_id,kinds={'RULE','LORE','MEMORY'},allow_secret=False,query_vector=query_vector); self.rules.require(gate_required,evidence)
            draft=state.snapshot(); next_version=state.state_version+1; event_ids=[]
            if plan['world_advances']:self.world.advance(draft)
            resolution_effects=trusted_resolution.get('effects',[]) if isinstance(trusted_resolution,dict) else []
            applied_effects=self.effects.apply(draft,resolution_effects,request_id,next_version)
            event_ids.extend(e['event_id'] for e in draft.event_log if e.get('request_id')==request_id)
            self._mark_discovery(draft,plan); draft.state_version=next_version; event_ids.append(self._append_turn_event(draft,request_id,next_version,text,plan,trusted_resolution)); draft.validate()
            context=self.narrator_context(draft,evidence,text,importance,plan,trusted_resolution); result={'tick':draft.tick,'state_version':next_version,'evidence':[e.checksum for e in evidence],'text':text,'mode':plan['mode'],'world_advanced':plan['world_advances'],'importance':importance,'system_profile':profile,'turn_plan':deepcopy(plan),'presentation':deepcopy(plan['channels']),'resolution':deepcopy(trusted_resolution),'effects_applied':deepcopy(applied_effects),'event_ids':event_ids}
            if self.provider:
                provider_state=draft.snapshot(); raw=self.recovery.run(lambda:self.provider.generate(text,context,provider_state)); validated=self._validate_provider_output(raw,draft,evidence,context,text,importance,plan,trusted_resolution); result.update(validated)
            self._remember_request(draft,request_id,fingerprint,result); draft.validate(); self._commit_draft(state,draft); self._bind_request(state,request_id,fingerprint,result)
        except Exception as exc:
            self.telemetry.record('reject',self._error_code(exc),campaign=state.campaign_id,system=state.system_id); raise
        self.telemetry.record('turn','ok',campaign=state.campaign_id,system=state.system_id,mode=result['mode']); return deepcopy(result)
