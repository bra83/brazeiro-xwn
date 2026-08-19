from copy import deepcopy


class EffectResolver:
    """Applies only engine-authorized, typed effects to a campaign draft.

    LLM/provider outputs never enter this API. The caller is responsible for
    passing effects only after MechanicsAuthority and the active system adapter
    have validated the resolution envelope.
    """

    MAX_EFFECTS = 128
    _SET_EFFECTS = {
        'player_state_set': ('player_state', False),
        'scene_state_set': ('scene', False),
        'note_set': ('notes', False),
        'fact_set': ('facts', False),
        'world_flag_set': ('world_flags', False),
        'npc_state_set': ('npcs', True),
        'faction_state_set': ('factions', True),
        'site_state_set': ('sites', True),
    }
    _ALLOWED = set(_SET_EFFECTS) | {'location_set'}

    def _path_parts(self, path):
        if not isinstance(path, str) or not path or path.startswith('.') or '..' in path:
            raise ValueError('invalid_effect_path')
        parts = path.split('.')
        if any(not part or part.startswith('_') for part in parts):
            raise ValueError('invalid_effect_path')
        return parts

    def _validate_set_effect(self, effect, entity_scoped):
        required = {'type', 'path', 'value'} | ({'entity_id'} if entity_scoped else set())
        if set(effect) != required:
            raise ValueError('invalid_effect_fields')
        self._path_parts(effect['path'])
        if entity_scoped and (not isinstance(effect['entity_id'], str) or not effect['entity_id']):
            raise ValueError('invalid_effect_entity')

    def validate(self, effects):
        if effects is None:
            return []
        if not isinstance(effects, list) or len(effects) > self.MAX_EFFECTS:
            raise ValueError('invalid_effects')
        out = []
        for effect in effects:
            if not isinstance(effect, dict):
                raise ValueError('invalid_effect')
            effect_type = effect.get('type')
            if effect_type not in self._ALLOWED:
                raise ValueError('unsupported_effect_type')
            if effect_type == 'location_set':
                if set(effect) != {'type', 'location'}:
                    raise ValueError('invalid_effect_fields')
                if not isinstance(effect['location'], str):
                    raise ValueError('invalid_effect_location')
            else:
                _, entity_scoped = self._SET_EFFECTS[effect_type]
                self._validate_set_effect(effect, entity_scoped)
            out.append(deepcopy(effect))
        return out

    def _set_nested(self, target, path, value):
        current = target
        parts = self._path_parts(path)
        for part in parts[:-1]:
            old = current.get(part)
            if old is None:
                current[part] = {}
                old = current[part]
            if not isinstance(old, dict):
                raise ValueError('effect_path_type_conflict')
            current = old
        current[parts[-1]] = deepcopy(value)

    def _apply_one(self, state, effect):
        effect_type = effect['type']
        if effect_type == 'location_set':
            state.location = effect['location']
            return
        root_name, entity_scoped = self._SET_EFFECTS[effect_type]
        root = getattr(state, root_name)
        if entity_scoped:
            entity_id = effect['entity_id']
            entity = root.get(entity_id)
            if entity is None:
                root[entity_id] = {}
                entity = root[entity_id]
            if not isinstance(entity, dict):
                raise ValueError('effect_entity_type_conflict')
            self._set_nested(entity, effect['path'], effect['value'])
        else:
            self._set_nested(root, effect['path'], effect['value'])

    def apply(self, state, effects, request_id, state_version):
        validated = self.validate(effects)
        for index, effect in enumerate(validated):
            self._apply_one(state, effect)
            state.event_log.append({
                'event_id': f'{request_id}:effect:{index}',
                'type': effect['type'],
                'request_id': request_id,
                'tick': state.tick,
                'state_version': state_version,
                'payload': deepcopy(effect),
            })
        state.validate()
        return validated
