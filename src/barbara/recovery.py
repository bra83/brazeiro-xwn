import time


class RecoveryPolicy:
    RETRYABLE={'timeout','rate_limit','provider_unavailable','transport_unavailable'}
    def __init__(self,max_attempts=2,base_delay=0):
        if not isinstance(max_attempts,int) or isinstance(max_attempts,bool) or not 1<=max_attempts<=3: raise ValueError('invalid_max_attempts')
        if not isinstance(base_delay,(int,float)) or isinstance(base_delay,bool) or base_delay<0 or base_delay>5: raise ValueError('invalid_base_delay')
        self.max_attempts=max_attempts; self.base_delay=base_delay
    def classify(self,exc):
        if isinstance(exc,TimeoutError): return 'timeout'
        code=getattr(exc,'status_code',None) or getattr(exc,'code',None)
        if code==429: return 'rate_limit'
        if code in (500,502,503,504): return 'provider_unavailable'
        text=str(exc).lower()
        if 'transport_error' in text or 'connection' in text or 'network is unreachable' in text or 'name resolution' in text:
            return 'transport_unavailable'
        return 'fatal'
    def run(self,call):
        last=None
        for attempt in range(self.max_attempts):
            try: return call()
            except Exception as exc:
                last=exc; kind=self.classify(exc)
                if kind not in self.RETRYABLE or attempt+1>=self.max_attempts: raise
                if self.base_delay: time.sleep(self.base_delay*(2**attempt))
        raise last
