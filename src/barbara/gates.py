PROTECTED={"tick","campaign_id","system","memory","events","rumors","npcs","factions"}
def rule_gate(needs_rule,evidence):
 if needs_rule and not any(e.kind=="RULE" for e in evidence): raise ValueError("regra_sem_evidencia_canonica")
def apply_patch(state,patch):
 for k,v in patch.items():
  if k in PROTECTED: raise ValueError("estado_protegido")
  if k not in state.facts: raise ValueError("namespace_nao_autorizado")
  if type(v) is not type(state.facts[k]): raise TypeError("tipo_invalido")
  state.facts[k]=v
