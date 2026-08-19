import json
from copy import deepcopy
from .state import CampaignState
from .pipeline import ActionPipeline

class HostBridge:
    """Stable JSON boundary for Android/desktop hosts integrating Barbara 1.0."""
    REQUEST_FIELDS={'text','request_id','mechanical','importance','resolution','expected_state_version','resume_action_id'}
    def __init__(self,engine):
        self.engine=engine
        self.pipeline=ActionPipeline(engine)
    def new_campaign(self,campaign_id,system_id,**initial):
        state=CampaignState(campaign_id,system_id,**initial); state.validate(); return state.to_json()
    def turn(self,state_json,request):
        if not isinstance(request,dict): raise ValueError('invalid_host_request')
        unknown=set(request)-self.REQUEST_FIELDS
        if unknown: raise ValueError('unknown_host_request_fields:'+','.join(sorted(unknown)))
        if 'request_id' not in request: raise ValueError('missing_host_request_field')
        state=CampaignState.from_json(state_json)
        if request.get('resume_action_id') is not None:
            result=self.pipeline.resume(
                state,
                request['resume_action_id'],
                request['request_id'],
                deepcopy(request.get('resolution')),
                expected_state_version=request.get('expected_state_version'),
            )
            return {'state':state.to_json(),'result':deepcopy(result)}
        if 'text' not in request: raise ValueError('missing_host_request_field')
        text=request['text']; request_id=request['request_id']
        if not isinstance(text,str) or not text.strip(): raise ValueError('invalid_host_text')
        result=self.pipeline.execute(
            state,
            text,
            request_id,
            mechanical=request.get('mechanical',False),
            importance=request.get('importance','normal'),
            resolution=deepcopy(request.get('resolution')),
            expected_state_version=request.get('expected_state_version'),
        )
        return {'state':state.to_json(),'result':deepcopy(result)}
    def turn_json(self,state_json,request_json):
        try: request=json.loads(request_json)
        except (TypeError,json.JSONDecodeError) as exc: raise ValueError('invalid_host_request_json') from exc
        return json.dumps(self.turn(state_json,request),ensure_ascii=False,sort_keys=True,separators=(',',':'))
