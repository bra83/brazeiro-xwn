import pytest
from barbara.engine import BarbaraEngine
from barbara.state import CampaignState
from barbara.recovery import RecoveryPolicy

class Flaky:
    def __init__(self,failures,exc=TimeoutError): self.failures=failures; self.calls=0; self.exc=exc
    def generate(self,*args):
        self.calls+=1
        if self.calls<=self.failures: raise self.exc('temporary')
        return 'recovered'

class HTTPErrorish(RuntimeError):
    def __init__(self,code): self.status_code=code

def test_timeout_retries_and_world_advances_once():
    p=Flaky(1); s=CampaignState('c','gurps'); r=BarbaraEngine(p).turn(s,'look','r')
    assert p.calls==2 and s.tick==1 and r['narration']=='recovered'

def test_exhausted_retry_rolls_world_back():
    p=Flaky(9); s=CampaignState('c','gurps')
    with pytest.raises(TimeoutError): BarbaraEngine(p).turn(s,'look','r')
    assert p.calls==2 and s.tick==0

def test_fatal_error_is_never_retried():
    class Fatal:
        calls=0
        def generate(self,*a): self.calls+=1; raise ValueError('bad request')
    p=Fatal(); s=CampaignState('c','gurps')
    with pytest.raises(ValueError): BarbaraEngine(p).turn(s,'look','r')
    assert p.calls==1 and s.tick==0

def test_rate_limit_and_503_are_retryable():
    policy=RecoveryPolicy()
    assert policy.classify(HTTPErrorish(429))=='rate_limit'
    assert policy.classify(HTTPErrorish(503))=='provider_unavailable'

def test_policy_parameters_fail_closed():
    for n in [0,4,True]:
        with pytest.raises(ValueError): RecoveryPolicy(max_attempts=n)
    for d in [-1,6,True]:
        with pytest.raises(ValueError): RecoveryPolicy(base_delay=d)
