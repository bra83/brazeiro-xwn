PROTECTED_ROOTS={"campaign_id","system_id","tick","facts","world_flags","npcs","factions","rumors","events","economy","clocks","weather","living_world","authorizations","sites","public_ledger","secret_ledger"}
SENSITIVE_KEYS={"private_agenda","secret","secrets","director_notes","has_private_agenda","private_goal","private_goals","hidden_goal","hidden_goals","knowledge_private","gm_only","director_only","secret_ledger"}
PRIVATE_VISIBILITY={"private","director","gm","gm_only","director_only"}
_DROP=object()

def _public(value):
    if isinstance(value,dict):
        if value.get("private") is True or str(value.get("visibility","")).lower() in PRIVATE_VISIBILITY:
            return _DROP
        out={}
        for k,v in value.items():
            if str(k).lower() in SENSITIVE_KEYS: continue
            sv=_public(v)
            if sv is not _DROP: out[k]=sv
        return out
    if isinstance(value,list):
        out=[]
        for v in value:
            sv=_public(v)
            if sv is not _DROP: out.append(sv)
        return out
    if isinstance(value,tuple):
        out=[]
        for v in value:
            sv=_public(v)
            if sv is not _DROP: out.append(sv)
        return tuple(out)
    return value

def public_view(value):
    cleaned=_public(value)
    return {} if cleaned is _DROP else cleaned

def validate_patch(path,value):
    if not isinstance(path,str) or not path or path.startswith('.') or '..' in path:
        raise ValueError('invalid_patch_path')
    parts=path.split('.')
    if any(not p or p.startswith('_') for p in parts): raise ValueError('invalid_patch_path')
    root=parts[0]
    if root in PROTECTED_ROOTS: raise ValueError(f"protected_state:{root}")
    if not root.startswith("player_") and root not in {"scene","notes"}: raise ValueError(f"namespace_not_allowed:{root}")
    return True
