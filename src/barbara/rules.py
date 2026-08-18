class RuleGate:
    MIN_AUTHORITY=0.5
    def applicable(self,evidence):
        return [e for e in evidence
                if getattr(e,'kind',None)=='RULE'
                and not getattr(e,'secret',False)
                and isinstance(getattr(e,'authority',None),(int,float))
                and not isinstance(getattr(e,'authority',None),bool)
                and getattr(e,'authority',0)>=self.MIN_AUTHORITY]
    def require(self,mechanical:bool,evidence):
        if not isinstance(mechanical,bool): raise ValueError('invalid_mechanical_flag')
        rules=self.applicable(evidence)
        if mechanical and not rules: raise LookupError('regra_sem_evidencia_canonica')
        return rules
