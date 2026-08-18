from copy import deepcopy
from .rag import RAG
from .rules import RuleGate
from .world import WorldTick
from .memory import Memory
from .security import public_view,validate_patch
from .recovery import RecoveryPolicy
from .narrative import NarrativePolicy
from .knowledge import KnowledgeBoundary

class BarbaraEngine:
    MAX_NARRATION=20000
    def __init__(self,provider=None,recovery=None,narrative=None,knowledge=None):
        self.provider=provider; self.rag=RAG(); self.rules=RuleGate(); self.world=WorldTick(); self.memory=Memory(); self.recovery=recovery or RecoveryPolicy(); self.narrative=narrative or NarrativePolicy(); self.knowledge=knowledge or KnowledgeBoundary(); self._requests={}
    def _fingerprint(self,state,text,mechanical,importance): return (state.campaign_id,state.system_id,text,mechanical,importance)
    def narrator_context(self,state,evidence,text='',importance='normal'):
        safe=[{'source_id':e.source_id,'kind':e.kind,'text':e.text,'checksum':e.checksum} for e in evidence if not e.secret]
        qcount=self.narrative.question_count(text)
        return public_view({'location':state.location,'facts':state.facts,'memory':self.memory.compact_context(state),'rumors':self.world.visible_rumors(state),'npcs':self.knowledge.visible_npcs(state),'evidence':safe,'narrative_policy':self.narrative.narrator_directives(importance,qcount)})
    def _validate_provider_output(self,out,importance='normal'):
        if isinstance(out,str): out={'narration':out,'claims':[],'state_patch':[]}
        if not isinstance(out,dict): raise ValueError('invalid_provider_output')
        if set(out)-{'narration','claims','state_patch'}: raise ValueError('unknown_provider_field')
        narration=out.get('narration'); claims=out.get('claims',[]); patches=out.get('state_patch',[])
        if not isinstance(narration,str) or not narration.strip() or len(narration)>self.MAX_NARRATION: raise ValueError('invalid_narration')
        if len(narration)<self.narrative.minimum_acceptable_chars(importance): raise ValueError('narrativa_resumida_demais')
        if not isinstance(claims,list) or not all(isinstance(x,str) for x in claims): raise ValueError('invalid_claims')
        if not isinstance(patches,list): raise ValueError('invalid_state_patch')
        for p in patches:
            if not isinstance(p,dict) or set(p)!={'path','value'}: raise ValueError('invalid_patch_entry')
            validate_patch(p['path'],p['value'])
        return {'narration':narration,'claims':deepcopy(claims),'state_patch':deepcopy(patches)}
    def _apply_patches(self,state,patches):
        for p in patches:
            parts=p['path'].split('.'); root=parts.pop(0)
            if root.startswith('player_'):
                target=state.player_state
                parts.insert(0,root)
            elif root in {'scene','notes'}:
                target=getattr(state,root)
            else:
                raise ValueError('patch_root_not_committable')
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
            return deepcopy(result)
        evidence=self.rag.retrieve(text,state.campaign_id,state.system_id,kinds={'RULE','LORE','MEMORY'},allow_secret=False)
        self.rules.require(mechanical,evidence); before=state.snapshot(); mode=self.narrative.classify(text)
        try:
            if self.narrative.advances_world(text): self.world.advance(state)
            context=self.narrator_context(state,evidence,text,importance)
            result={'tick':state.tick,'evidence':[e.checksum for e in evidence],'text':text,'mode':mode,'world_advanced':mode=='fiction','importance':importance}
            if self.provider:
                raw=self.recovery.run(lambda:self.provider.generate(text,context,state))
                validated=self._validate_provider_output(raw,importance)
                self._apply_patches(state,validated['state_patch'])
                result.update(validated)
        except Exception:
            state.__dict__.clear(); state.__dict__.update(before.__dict__); raise
        self._requests[request_id]=(fingerprint,deepcopy(result)); return deepcopy(result)
