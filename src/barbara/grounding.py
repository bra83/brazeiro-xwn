import json,re

class ClaimGrounding:
    PREFIXES=('FACT:','RULE:','RUMOR:','INFERENCE:')
    STOP={'a','o','as','os','de','da','do','das','dos','e','é','um','uma','the','of','and','is','to','in'}
    def _tokens(self,text):
        return {t for t in re.findall(r'\w+',str(text).lower(),re.UNICODE) if len(t)>1 and t not in self.STOP}
    def _flatten(self,value):
        if isinstance(value,dict):
            out=[]
            for k,v in value.items(): out.extend(self._flatten(k)); out.extend(self._flatten(v))
            return out
        if isinstance(value,(list,tuple,set)):
            out=[]
            for v in value: out.extend(self._flatten(v))
            return out
        return [str(value)]
    def _supported(self,claim,sources):
        ct=self._tokens(claim)
        if not ct: return False
        for source in sources:
            st=self._tokens(source)
            if not st: continue
            overlap=len(ct & st)/len(ct)
            if overlap>=0.6 or ct<=st: return True
        return False
    def validate(self,claims,state,evidence,visible_rumors):
        if not isinstance(claims,list) or not all(isinstance(c,str) for c in claims): raise ValueError('invalid_claims')
        facts=self._flatten(getattr(state,'facts',{}))
        rules=[e.text for e in evidence if getattr(e,'kind',None)=='RULE' and not getattr(e,'secret',False)]
        canon=facts+[e.text for e in evidence if getattr(e,'kind',None) in {'LORE','MEMORY'} and not getattr(e,'secret',False)]
        rumors=self._flatten(visible_rumors)
        out=[]
        for raw in claims:
            claim=raw.strip()
            if not claim: raise ValueError('empty_claim')
            upper=claim.upper()
            if upper.startswith('INFERENCE:'):
                if not claim.split(':',1)[1].strip(): raise ValueError('empty_inference')
                out.append(claim); continue
            if upper.startswith('RUMOR:'):
                body=claim.split(':',1)[1]
                if not self._supported(body,rumors): raise ValueError('rumor_sem_evidencia')
                out.append(claim); continue
            if upper.startswith('RULE:'):
                body=claim.split(':',1)[1]
                if not self._supported(body,rules): raise ValueError('regra_claim_sem_evidencia')
                out.append(claim); continue
            body=claim.split(':',1)[1] if upper.startswith('FACT:') else claim
            if not self._supported(body,canon): raise ValueError('fato_claim_sem_evidencia')
            out.append(claim)
        return out
