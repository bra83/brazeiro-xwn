from copy import deepcopy

from .security import public_view


class ContextEngine:
    """Build typed, canonical scene context from campaign state.

    Geography is never inferred by the narrator. The adapter/atlas populates
    canonical site data and this projection is the only geography the narrator
    is allowed to treat as real.
    """

    _WATER_WORDS = {
        'rio', 'river', 'riacho', 'stream', 'córrego', 'corrego', 'lago', 'lake',
        'mar', 'sea', 'oceano', 'ocean', 'pântano', 'pantano', 'swamp', 'canal',
        'cachoeira', 'waterfall', 'nascente', 'spring', 'delta', 'estuário', 'estuario',
    }
    _DRY_TERRAINS = {
        'desert', 'deserto', 'dunes', 'duna', 'dunas', 'badlands', 'semiarid',
        'semiárido', 'semiarido', 'wasteland', 'ermo', 'estepe seca', 'dry steppe',
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

    def _has_water_word(self, *values):
        blob = ' '.join(str(v).lower() for v in values if v is not None)
        return any(word in blob for word in self._WATER_WORDS)

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

        description = site.get('description') or site.get('public_description') or ''
        hydrology = site.get('hydrology')
        explicit_water = site.get('water_present')
        if explicit_water is None:
            explicit_water = site.get('has_water')

        geography_known = bool(location_id and site)
        water_present = None
        if isinstance(explicit_water, bool):
            water_present = explicit_water
        elif hydrology is not None:
            if isinstance(hydrology, str):
                low = hydrology.strip().lower()
                water_present = low not in {'', 'none', 'dry', 'absent', 'no', 'false'}
            else:
                water_present = bool(hydrology)
        elif self._has_water_word(' '.join(features), description):
            water_present = True
        elif terrain is not None and str(terrain).strip().lower() in self._DRY_TERRAINS:
            water_present = False
        elif geography_known and any(k in site for k in ('features', 'tags', 'traits', 'landmarks')):
            water_present = False

        name = site.get('name') or location_id
        hazards = self._as_words(site.get('hazards'))
        return {
            'location_id': location_id,
            'location_name': str(name or ''),
            'terrain': str(terrain) if terrain is not None else None,
            'features': tuple(features),
            'description': str(description or ''),
            'hydrology': deepcopy(hydrology),
            'water_present': water_present,
            'geography_known': geography_known,
            'lighting': deepcopy(site.get('lighting')),
            'visibility': deepcopy(site.get('visibility')),
            'cover': deepcopy(site.get('cover')),
            'noise': deepcopy(site.get('noise')),
            'temperature': deepcopy(site.get('temperature')),
            'hazards': tuple(x.strip() for x in hazards if x and x.strip()),
            'geometry': deepcopy(site.get('geometry')),
            'connections': deepcopy(site.get('connections')),
            'weather': public_view(deepcopy(state.weather)),
            'tick': state.tick,
            'state_version': getattr(state, 'state_version', 0),
        }


class WorldConsistencyGate:
    """Reject obvious geography hallucinations against typed canonical context."""

    _WATER_TERMS = (
        ' rio ', ' river ', ' riacho ', ' stream ', ' córrego ', ' corrego ',
        ' lago ', ' lake ', ' oceano ', ' ocean ', ' cachoeira ', ' waterfall ',
        ' pântano ', ' pantano ', ' swamp ', ' canal ', ' nascente ', ' spring ',
    )
    _TERRAIN_TERMS = {
        'desert': (' floresta densa ', ' dense forest ', ' selva ', ' jungle ', ' pântano ', ' pantano ', ' swamp '),
        'deserto': (' floresta densa ', ' dense forest ', ' selva ', ' jungle ', ' pântano ', ' pantano ', ' swamp '),
        'ocean': (' deserto ', ' desert ', ' floresta densa ', ' dense forest '),
        'sea': (' deserto ', ' desert ', ' floresta densa ', ' dense forest '),
        'oceano': (' deserto ', ' desert ', ' floresta densa ', ' dense forest '),
        'mar': (' deserto ', ' desert ', ' floresta densa ', ' dense forest '),
    }

    def _blob(self, text):
        return ' ' + ' '.join(str(text).lower().split()) + ' '

    def validate(self, narration, context):
        if not isinstance(narration, str) or not narration.strip():
            raise ValueError('invalid_narration')
        if not isinstance(context, dict) or not context.get('geography_known'):
            return True

        blob = self._blob(narration)
        feature_blob = self._blob(' '.join(context.get('features') or ()))

        if context.get('water_present') is False:
            for term in self._WATER_TERMS:
                if term in blob and term not in feature_blob:
                    raise ValueError('narrative_geography_contradiction:water')

        terrain = str(context.get('terrain') or '').strip().lower()
        for term in self._TERRAIN_TERMS.get(terrain, ()):
            if term in blob and term not in feature_blob:
                raise ValueError('narrative_geography_contradiction:terrain')
        return True

    def validate_depth(self, narration, context, mode='fiction', importance='normal'):
        """Prevent one-paragraph scene collapse where the atlas has a real scene."""
        if mode != 'fiction' or importance == 'routine':
            return True
        if not isinstance(context, dict) or not context.get('location_id'):
            return True
        text = str(narration).strip()
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        minimum = {'normal': 300, 'meaningful': 550, 'climax': 900}.get(importance, 300)
        if len(paragraphs) < 2:
            raise ValueError('narrative_too_few_paragraphs')
        if len(text) < minimum:
            raise ValueError('narrative_too_short')
        return True
