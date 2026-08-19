from copy import deepcopy
import re
from .rag import RAG
from .rules import RuleGate
from .world import WorldTick
from .memory import Memory
from .security import public_view,validate_patch
from .recovery import RecoveryPolicy
from .narrative import NarrativePolicy
from .knowledge import KnowledgeBoundary
from .grounding import ClaimGrounding
from .telemetry import Telemetry
from .adapters import AdapterRegistry

class BarbaraEngine:
    MAX_NARRATION=20000
    def __init__(self,provider=None,recovery=None,narrative=None,knowledge=None,grounding=None,rag=None,rag_db_path=None,embedder=None,telemetry=None,adapters=None):
        if rag is not None and rag_db_path is not None: raise ValueError('rag_configuration_conflict')
        self.provider=provider
        self.rag=rag if rag is not None else RAG(rag_db_path)
        self.rules=RuleGate(); self.world=WorldTick(); self.memory=Memory()
        self.recovery=recovery or RecoveryPolicy(); self.narrative=narrative or NarrativePolicy(); self.knowledge=knowledge or KnowledgeBoundary(); self.grounding=grounding or ClaimGrounding()
        self.embedder=embedder; self.telemetry=telemetry or Telemetry(); self.adapters=adapters or AdapterRegistry(); self._requests={}
    def _fingerprint(self,state,text,mechanical,importance): return (state.campaign_id,state.system_id,text,mechanical,importance)
    def _adapter(self,state):
        try: adapter=self.adapters.get(state.system_id)
        except KeyError as e: raise ValueError('unsupported_system:'+str(state.system_id)) from e
        adapter.validate_campaign(state); return adapter
    def _query_vector(self,text):
        if self.embedder is None: return None
        fn=getattr(self.embedder,'embed',None)
        if not callable(fn): raise ValueError('invalid_embedder')
        vector=fn(text)
        if not isinstance(vector,(list,tuple)) or not vector or not all(isinstance(x,(int,float)) and not isinstance(x,bool) for x in vector): raise ValueError('invalid_query_vector')
        return tuple(float(x) for x in vector)
    def _error_code(self,exc):
        msg=str(exc).split(':',1)[0]
        return msg if re.fullmatch(r'[A-Za-z0-9_\-]{1,80}',msg or '') else exc.__class__.__name__
    def narrator_context(self,state,evidence,text='',importance='normal',adapter=None):
        adapter=adapter or self._adapter(state)
        safe=[{'source_id':e.source_id,'kind':e.kind,'text':e.text,'checksum':e.checksum} for e in evidence if not e.secret]
        qcount=self.narrative.question_count(text)
        return public_view({'location':state.location,'facts':state.facts,'memory':self.memory.compact_context(state),'rumors':self.world.visible_rumors(state),'npcs':self.knowledge.visible_npcs(state),'evidence':safe,'system_profile':adapter.narrator_profile(self.rag,state.campaign_id),'narrative_policy':self.narrative.narrator_directives(importance,qcount)})
    def _validate_provider_output(self,out,state,evidence,importance='normal'):
        if isinstance(out,str): out={'narration':out,'claims':[],'state_patch':[]}
        if not isinstance(out,dict): raise ValueError('invalid_provider_output')
        if set(out)-{'narration','claims','state_patch'}: raise ValueError('unknown_provider_field')
        narration=out.get('narration'); claims=out.get('claims',[]); patches=out.get('state_patch',[])
        if not isinstance(narration,str) or not narration.strip() or len(narration)>self.MAX_NARRATION: raise ValueError('invalid_narration')
        if len(narration)<self.narrative.minimum_acceptable_chars(importance): raise ValueError('narrativa_resumida_demais')
        claims=self.grounding.validate(claims,state,evidence,self.world.visible_rumors(state))
        if not isinstance(patches,list): raise ValueError('invalid_state_patch')
        for p in patches:
            if not isinstance(p,dict) or set(p)!={'path','value'}: raise ValueError('invalid_patch_entry')
            validate_patch(p['path'],p['value'])
        return {'narration':narration,'claims':deepcopy(claims),'state_patch':deepcopy(patches)}
    def _apply_patches(self,state,patches):
        for p in patches:
            parts=p['path'].split('.'); root=parts.pop(0)
            if root.startswith('player_'):
                target=state.player_state; parts.insert(0,root)
            elif root in {'scene','notes'}: target=getattr(state,root)
            else: raise ValueError('patch_root_not_committable')
            if not parts: raise ValueError('patch_requires_leaf')
            for key in parts[:-1]:
                current=target.get(key)
                if current is None: target[key]={}; current=target[key]
                if not isinstance(current,dict): raise ValueError('patch_path_type_conflict')
                target=current
            target[parts[-1]]=deepcopy(p['value'])
        state.validate()
    def turn(self,state,text,request_id,mechanical=False,importance='normal'):
        self.narrative.target_chars(importance)
        fingerprint=self._fingerprint(state,text,mechanical,importance)
        if request_id in self._requests:
            old,result=self._requests[request_id]
            if old!=fingerprint: raise ValueError('request_id_collision')
            self.telemetry.record('turn','idempotent',campaign=state.campaign_id,system=state.system_id)
            return deepcopy(result)
        before=state.snapshot()
        try:
            adapter=self._adapter(state)
            query_vector=self._query_vector(text)
            evidence=self.rag.retrieve(text,state.campaign_id,state.system_id,kinds={'RULE','LORE','MEMORY'},allow_secret=False,query_vector=query_vector)
            self.rules.require(mechanical,evidence); mode=self.narrative.classify(text)
            if self.narrative.advances_world(text): self.world.advance(state)
            context=self.narrator_context(state,evidence,text,importance,adapter)
            result={'tick':state.tick,'evidence':[e.checksum for e in evidence],'text':text,'mode':mode,'world_advanced':mode=='fiction','importance':importance,'system_profile':deepcopy(context['system_profile'])}
            if self.provider:
                raw=self.recovery.run(lambda:self.provider.generate(text,context,state))
                validated=self._validate_provider_output(raw,state,evidence,importance)
                self._apply_patches(state,validated['state_patch']); result.update(validated)
        except Exception as exc:
            state.__dict__.clear(); state.__dict__.update(before.__dict__)
            self.telemetry.record('reject',self._error_code(exc),campaign=state.campaign_id,system=state.system_id)
            raise
        self._requests[request_id]=(fingerprint,deepcopy(result))
        self.telemetry.record('turn','ok',campaign=state.campaign_id,system=state.system_id,mode=result['mode'])
        return deepcopy(result)
