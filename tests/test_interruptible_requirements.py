from barbara.engine import BarbaraEngine
from barbara.rag import Evidence
from barbara.state import CampaignState


def add_rule(e):
    e.rag.replace_source('r',[Evidence('r','combat attack reaction choice opposed roll rule','RULE','c','gurps')])


def test_rules_kernel_can_pause_for_choice_without_advancing_world():
    e=BarbaraEngine(); add_rule(e); s=CampaignState('c','gurps')
    r=e.turn(s,'Faço um teste de ataque','choice',mechanical=True,resolution={'requirement':'choice_required','source':'rules_kernel'})
    assert r['phase']=='WAITING_FOR_CHOICE' and r['requirement']=='choice_required'
    assert s.tick==0 and s.pending_action['phase']=='WAITING_FOR_CHOICE'


def test_rules_kernel_can_pause_for_reaction_or_opposed_roll():
    for req,phase in [('reaction_required','WAITING_FOR_REACTION'),('opposed_roll','WAITING_FOR_OPPOSED_ROLL')]:
        e=BarbaraEngine(); add_rule(e); s=CampaignState('c','gurps')
        r=e.turn(s,'Faço um teste de ataque',req,mechanical=True,resolution={'requirement':req,'source':'rules_kernel'})
        assert r['phase']==phase and s.tick==0


def test_generic_resume_accepts_non_roll_pending_phase_and_commits_only_when_resolved():
    e=BarbaraEngine(); add_rule(e); s=CampaignState('c','gurps')
    first=e.turn(s,'Faço um teste de ataque','start',mechanical=True,resolution={'requirement':'choice_required','source':'rules_kernel'})
    action_id=first['pending_action']['action_id']; version=s.state_version
    done=e.resume_action(s,action_id,'finish',{'requirement':'resolved','outcome':'success','source':'rules_kernel'},expected_state_version=version)
    assert done['phase']=='COMPLETED' and s.pending_action=={}
    assert s.tick==1
