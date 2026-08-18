class RuleGate:
    def require(self, mechanical:bool, evidence):
        if mechanical and not any(getattr(e,"kind",None)=="RULE" for e in evidence):
            raise LookupError("regra_sem_evidencia_canonica")
        return True
