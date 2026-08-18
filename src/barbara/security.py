PROTECTED_ROOTS={"campaign_id","system_id","tick","facts","world_flags","npcs","factions","rumors","events"}

def public_view(value):
    if isinstance(value, dict):
        if value.get("private") is True or value.get("visibility") in {"private","director"}:
            return None
        out={}
        for k,v in value.items():
            if k in {"private_agenda","secret","secrets","director_notes","has_private_agenda"}: continue
            sv=public_view(v)
            if sv is not None: out[k]=sv
        return out
    if isinstance(value,list):
        return [x for x in (public_view(v) for v in value) if x is not None]
    return value

def validate_patch(path, value):
    root=path.split(".",1)[0]
    if root in PROTECTED_ROOTS:
        raise ValueError(f"protected_state:{root}")
    if not root.startswith("player_") and root not in {"scene","notes"}:
        raise ValueError(f"namespace_not_allowed:{root}")
    return True
