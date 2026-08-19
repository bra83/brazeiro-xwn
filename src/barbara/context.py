from copy import deepcopy

from .security import public_view


class ContextEngine:
    """Builds a typed, canonical scene context from campaign state.

    The narrator never gets to choose geography. Location/terrain/features are
    derived from canonical state and can be checked against generated prose.
    """

    _WATER_WORDS = {
        'rio','river','riacho','stream','córrego','corrego','lago','lake','mar','sea',
        'oceano','ocean','pântano','pantano','swamp','canal','cachoeira','waterfall',
        'água','agua','water'
    }

    def _as_words(self, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, (list, tuple, set)):
            return [str(x) for x in value if x is not None]
        if isinstance(value, dict):
            return [str(k) for k, v in value.items() if v]
        return [str(value)]

    def build(self, state):
        location_id = state.location or ''
        raw_site = deepcopy(state.sites.get(location_id, {})) if location_id else {}
        site = public_view(raw_site) if isinstance(raw_site, dict) else {}
        if not isinstance(site, dict):
            site = {}

        terrain = site.get('terrain') or site.get('biome') or site.get('environment') or site.get('kind')
        features = []
        for key in ('features', 'tags', 'traits', 'landmarks'):
            features.extend(self._as_words(site.get(key)))
        features = [x.strip() for x in features if x and x.strip()]

        hydrology = site.get('hydrology')
        water_flag = site.get('water_present')
        if water_flag is None:
            water_flag = site.get('has_water')
        feature_blob = ' '.join(features).lower()
        if water_flag is None:
            water_flag = any(word in feature_blob for word in self._WATER_WORDS)
        if isinstance(hydrology, str) and hydrology.strip().lower() not in {'', 'none', 'dry', 'absent', 'no'}:
            water_flag = True

        description = site.get('description') or site.get('public_description') or ''
        name = site.get('name') or location_id
        return {
            'location_id': location_id,
            'location_name': str(name or ''),
            'terrain': str(terrain) if terrain is not None else None,
            'features': tuple(features),
            'description': str(description or ''),
            'hydrology': deepcopy(hydrology),
            'water_present': bool(water_flag),
            'weather': public_view(deepcopy(state.weather)),
            'tick': state.tick,
            'state_version': getattr(state, 'state_version', 0),
        }


class WorldConsistencyGate:
    """Rejects obvious geography hallucinations against typed canonical context."""

    _WATER_TERMS = (' rio ', ' river ', ' riacho ', ' stream ', ' córrego ', ' corrego ',
                    ' lago ', ' lake ', ' oceano ', ' ocean ', ' cachoeira ', ' waterfall ')
    _TERRAIN_TERMS = {
        'desert': (' floresta densa ', ' dense forest ', ' selva ', ' jungle ', ' pântano ', ' swamp '),
        'deserto': (' floresta densa ', ' dense forest ', ' selva ', ' jungle ', ' pântano ', ' swamp '),
        'ocean': (' deserto ', ' desert ', ' floresta densa ', ' dense forest '),
        'sea': (' deserto ', ' desert ', ' floresta densa ', ' dense forest '),
    }

    def _blob(self, text):
        return ' ' + ' '.join(str(text).lower().split()) + ' '

    def validate(self, narration, context):
        if not isinstance(narration, str) or not narration.strip():
            raise ValueError('invalid_narration')
        blob = self._blob(narration)
        feature_blob = self._blob(' '.join(context.get('features') or ()))

        if not context.get('water_present'):
            for term in self._WATER_TERMS:
                if term in blob and term not in feature_blob:
                    raise ValueError('narrative_geography_contradiction:water')

        terrain = str(context.get('terrain') or '').strip().lower()
        forbidden = self._TERRAIN_TERMS.get(terrain, ())
        for term in forbidden:
            if term in blob and term not in feature_blob:
                raise ValueError('narrative_geography_contradiction:terrain')
        return True

    def validate_paragraphs(self, narration, mode='fiction', importance='normal'):
        if mode != 'fiction' or importance == 'routine':
            return True
        text = str(narration).strip()
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if len(paragraphs) < 2:
            raise ValueError('narrative_too_few_paragraphs')
        minimum = {'normal': 240, 'meaningful': 500, 'climax': 850}.get(importance, 240)
        if len(text) < minimum:
            raise ValueError('narrative_too_short')
        return True
