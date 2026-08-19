import re

class ClaimGrounding:
    PREFIXES=('FACT:','RULE:','RUMOR:','INFERENCE:')
    STOP={'a','o','as','os','de','da','do','das','dos','e','é','um','uma','the','of','and','is','to','in'}
    OPPOSITES=(
        ({'alive','vivo','viva'},{'dead','morto','morta'}),
        ({'open','aberto','aberta'},{'closed','fechado','fechada'}),
        ({'present','presente'},{'absent','ausente'}),
        ({'success','sucesso','sucede'},{'failure','falha','fracasso'}),
        ({'true','verdadeiro','verdadeira'},{'false','falso','falsa'}),
    )
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
    def _contradicts(self,claim_tokens,source_tokens):
        for left,right in self.OPPOSITES:
            if (claim_tokens & left and source_tokens & right) or (claim_tokens & right and source_tokens & left): return True
        return False
    def _supported(self,claim,sources):
        ct=self._tokens(claim)
        if not ct: return False
        claim_numbers=set(re.findall(r'(?<!\w)[+-]?\d+(?:[.,]\d+)?',str(claim)))
        for source in sources:
            st=self._tokens(source)
            if not st or self._contradicts(ct,st): continue
            source_numbers=set(re.findall(r'(?<!\w)[+-]?\d+(?:[.,]\d+)?',str(source)))
            if claim_numbers and source_numbers and claim_numbers!=source_numbers: continue
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
            if not any(upper.startswith(prefix) for prefix in self.PREFIXES): raise ValueError('claim_type_required')
            body=claim.split(':',1)[1].strip()
            if not body: raise ValueError('empty_claim_body')
            if upper.startswith('INFERENCE:'):
                out.append(claim); continue
            if upper.startswith('RUMOR:'):
                if not self._supported(body,rumors): raise ValueError('rumor_sem_evidencia')
                out.append(claim); continue
            if upper.startswith('RULE:'):
                if not self._supported(body,rules): raise ValueError('regra_claim_sem_evidencia')
                out.append(claim); continue
            if not self._supported(body,canon): raise ValueError('fato_claim_sem_evidencia')
            out.append(claim)
        return out
