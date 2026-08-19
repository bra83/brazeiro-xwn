from copy import deepcopy


class ResolutionEnvelopeValidator:
    """Canonical contract for trusted mechanical resolutions.

    This validator is intentionally backward-compatible with the current host
    resolution shape while accepting the richer envelope used by the P0 runtime.
    LLM/provider output is never a trusted source.
    """

    OUTCOMES = {'success','failure','critical_success','critical_failure','partial','tie'}
    SOURCES = {'host','adapter','dice','rules_kernel'}
    REQUIREMENTS = {'no_roll','roll_required','choice_required','reaction_required','opposed_roll','resolved'}
    ALLOWED = {
        'resolution_id','system_id','family','source','mechanic','action','actor','targets',
        'requirement','outcome','roll','total','target','margin','details','rolls','modifiers',
        'effects','costs','events','rule_refs','rng_trace','metadata'
    }

    def _string(self, value, code, optional=False):
        if optional and value is None:
            return
        if not isinstance(value, str) or not value:
            raise ValueError(code)

    def _number(self, value, code):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(code)

    def _list(self, value, code):
        if not isinstance(value, list):
            raise ValueError(code)

    def validate(self, resolution):
        if resolution is None:
            return None
        if not isinstance(resolution, dict):
            raise ValueError('invalid_resolution')
        unknown = set(resolution) - self.ALLOWED
        if unknown:
            raise ValueError('invalid_resolution_field')

        out = deepcopy(resolution)
        outcome = out.get('outcome')
        if outcome is not None and outcome not in self.OUTCOMES:
            raise ValueError('invalid_resolution_outcome')
        requirement = out.get('requirement')
        if requirement is not None and requirement not in self.REQUIREMENTS:
            raise ValueError('invalid_resolution_requirement')
        source = out.get('source', 'host')
        if source not in self.SOURCES:
            raise ValueError('untrusted_resolution_source')
        out['source'] = source

        for key in ('resolution_id','system_id','family','mechanic','action','actor'):
            if key in out:
                self._string(out[key], 'invalid_resolution_binding')
        for key in ('roll','total','target','margin'):
            if key in out:
                self._number(out[key], 'invalid_resolution_number')
        for key in ('targets','rolls','modifiers','effects','costs','events','rule_refs'):
            if key in out:
                self._list(out[key], 'invalid_resolution_'+key)
        if 'details' in out and not isinstance(out['details'], (dict, list, str, int, float, bool, type(None))):
            raise ValueError('invalid_resolution_details')
        if 'metadata' in out and not isinstance(out['metadata'], dict):
            raise ValueError('invalid_resolution_metadata')
        if 'rng_trace' in out and not isinstance(out['rng_trace'], (dict, list, str, int, float, type(None))):
            raise ValueError('invalid_resolution_rng_trace')

        if requirement == 'resolved' and outcome is None:
            raise ValueError('resolved_without_outcome')
        if outcome is not None and requirement in {'roll_required','choice_required','reaction_required','opposed_roll'}:
            raise ValueError('unresolved_requirement_has_outcome')
        return out
