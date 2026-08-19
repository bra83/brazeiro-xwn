import re
from copy import deepcopy

class MechanicsAuthority:
    _EXPLICIT_MECHANICAL=(r'\b(rolo|rolar|role|jogo|jogar)\s+(?:um\s+)?(?:dado|dados|teste|ataque|per[ií]cia)\b',r'\b(fa[cç]o|fazer)\s+(?:um\s+)?teste\b',r'\bquanto\s+dano\b',r'\bteste\s+de\b',r'\b(roll|make)\s+(?:a\s+)?(?:check|test|attack|save)\b',r'\bhow much damage\b')
    _OUTCOME_ASSERTIONS=(r'\bvoc[eê]\s+(acerta|erra|falha|consegue|vence|perde)\b',r'\b(o|seu)\s+ataque\s+(acerta|erra|atinge|falha)\b',r'\bteste\s+(passa|falha|teve sucesso)\b',r'\byou\s+(hit|miss|fail|succeed|win|lose)\b',r'\b(?:the|your)\s+attack\s+(hits|misses|fails)\b')
    def requires_rule(self,text,mechanical=False,plan=None):
        if not isinstance(mechanical,bool):raise ValueError('invalid_mechanical_flag')
        if mechanical:return True
        low=str(text).lower()
        if plan and plan.get('mode')=='meta' and any(w in low for w in ('regra','regras','rule','rules','como funciona','how does')):return True
        return any(re.search(p,low,re.I) for p in self._EXPLICIT_MECHANICAL)
    def validate_resolution(self,resolution):
        if resolution is None:return None
        if not isinstance(resolution,dict):raise ValueError('invalid_resolution')
        allowed={'resolution_id','outcome','roll','total','target','margin','details','source','system_id','family','mechanic','effects'}
        if set(resolution)-allowed:raise ValueError('invalid_resolution_field')
        outcome=resolution.get('outcome')
        if outcome not in {'success','failure','critical_success','critical_failure','partial'}:raise ValueError('invalid_resolution_outcome')
        source=resolution.get('source','host')
        if source not in {'host','adapter','dice'}:raise ValueError('untrusted_resolution_source')
        for k in ('roll','total','target','margin'):
            if k in resolution and (not isinstance(resolution[k],(int,float)) or isinstance(resolution[k],bool)):raise ValueError('invalid_resolution_number')
        for k in ('resolution_id','system_id','family','mechanic'):
            if k in resolution and (not isinstance(resolution[k],str) or not resolution[k]):raise ValueError('invalid_resolution_binding')
        if 'effects' in resolution and not isinstance(resolution['effects'],list):raise ValueError('invalid_resolution_effects')
        out=deepcopy(resolution); out['source']=source; return out
    def validate_narration(self,narration,check_required=False,resolution=None):
        if not check_required or resolution is not None:return True
        rendered=str(narration).lower()
        if any(re.search(p,rendered,re.I) for p in self._OUTCOME_ASSERTIONS):raise ValueError('resultado_mecanico_sem_autoridade')
        return True
