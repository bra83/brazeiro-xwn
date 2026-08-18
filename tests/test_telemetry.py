import pytest
from barbara.telemetry import Telemetry

def test_snapshot_aggregates_rejection_signatures():
    t=Telemetry(); t.record('reject','protected_state'); t.record('reject','protected_state'); t.record('turn','ok')
    s=t.snapshot(); assert s['total']==3 and s['signatures']['reject:protected_state']==2

def test_compare_reports_only_growth():
    t=Telemetry(); t.record('reject','claim'); base=t.snapshot(); t.record('reject','claim'); t.record('reject','secret')
    d=t.compare(base); assert d['reject:claim']['delta']==1 and d['reject:secret']['delta']==1

def test_sensitive_payload_fields_are_never_retained():
    t=Telemetry(); t.record('reject','x',prompt='private prompt',secret='betray',text='hidden',campaign='c')
    assert t._events==[{'kind':'reject','code':'x','campaign':'c'}]

def test_snapshot_is_stable():
    t=Telemetry(); t.record('b','z'); t.record('a','y'); assert t.snapshot()==t.snapshot()

def test_invalid_kind_and_code_fail_closed():
    t=Telemetry()
    for kind,code in [('', 'x'),('x',''),(None,'x')]:
        with pytest.raises(ValueError): t.record(kind,code)
