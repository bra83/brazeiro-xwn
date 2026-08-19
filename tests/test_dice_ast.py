import pytest
from barbara.dice import DiceEngine, SeededRandomSource, SequenceRandomSource


def test_gurps_style_3d6_roll_under_is_expressible_without_gurps_engine():
    engine = DiceEngine(SequenceRandomSource([3, 4, 5]))
    expr = {'op':'compare','left':{'op':'sum','args':[{'op':'dice','count':3,'sides':6}]},'right':12,'comparator':'<='}
    out = engine.evaluate(expr)
    assert out['value']['success'] is True
    assert out['value']['left'] == 12
    assert [e['value'] for e in out['trace'] if e['op']=='die'] == [3,4,5]


def test_d20_advantage_is_composition_not_a_dnd_specific_roller():
    engine = DiceEngine(SequenceRandomSource([7, 18]))
    expr = {'op':'sum','args':[{'op':'keep_highest','expr':{'op':'dice','count':2,'sides':20},'count':1}]}
    out = engine.evaluate(expr)
    assert out['value'] == 18


def test_d6_success_pool_is_generic_ast():
    engine = DiceEngine(SequenceRandomSource([2,6,5,6,1]))
    expr = {'op':'count_successes','expr':{'op':'dice','count':5,'sides':6},'threshold':6,'comparator':'>='}
    assert engine.evaluate(expr)['value'] == 2


def test_seeded_random_source_replays_exactly():
    expr = {'op':'dice','count':8,'sides':20}
    a = DiceEngine(SeededRandomSource('campaign-seed')).evaluate(expr)
    b = DiceEngine(SeededRandomSource('campaign-seed')).evaluate(expr)
    assert a == b


def test_malformed_or_excessive_ast_fails_closed():
    with pytest.raises(ValueError): DiceEngine().evaluate({'op':'dice','count':1000,'sides':6})
    with pytest.raises(ValueError): DiceEngine().evaluate({'op':'die','sides':1})
    with pytest.raises(ValueError): DiceEngine().evaluate({'op':'eval_python','code':'1+1'})
