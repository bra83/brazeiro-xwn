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
    _SCOPES = {'player_state','scene','facts','world_flags','npcs','factions','sites','clocks'}
    _ALLOWED = set(_SET_EFFECTS) | {
        'location_set','resource_delta','condition_add','condition_remove','clock_advance'
    }

    def _path_parts(self, path):
        if not isinstance(path, str) or not path or path.startswith('.') or '..' in path:
            raise ValueError('invalid_effect_path')
        parts = path.split('.')
        if any(not part or part.startswith('_') for part in parts):
            raise ValueError('invalid_effect_path')
        return parts

    def _validate_entity(self, entity_id):
        if not isinstance(entity_id, str) or not entity_id:
            raise ValueError('invalid_effect_entity')

    def _validate_set_effect(self, effect, entity_scoped):
        required = {'type', 'path', 'value'} | ({'entity_id'} if entity_scoped else set())
        if set(effect) != required:
            raise ValueError('invalid_effect_fields')
        self._path_parts(effect['path'])
        if entity_scoped:
            self._validate_entity(effect['entity_id'])

    def _validate_resource_delta(self, effect):
        allowed = {'type','scope','path','delta','entity_id','minimum','maximum'}
        if set(effect) - allowed or not {'type','scope','path','delta'} <= set(effect):
            raise ValueError('invalid_effect_fields')
        if effect['scope'] not in self._SCOPES:
            raise ValueError('invalid_effect_scope')
        self._path_parts(effect['path'])
        if effect['scope'] in {'npcs','factions','sites'}:
            self._validate_entity(effect.get('entity_id'))
        elif 'entity_id' in effect:
            raise ValueError('invalid_effect_entity')
        if not isinstance(effect['delta'], (int,float)) or isinstance(effect['delta'], bool):
            raise ValueError('invalid_effect_delta')
        for key in ('minimum','maximum'):
            if key in effect and (not isinstance(effect[key], (int,float)) or isinstance(effect[key], bool)):
                raise ValueError('invalid_effect_bound')
        if 'minimum' in effect and 'maximum' in effect and effect['minimum'] > effect['maximum']:
            raise ValueError('invalid_effect_bounds')

    def _validate_condition(self, effect):
        allowed = {'type','scope','condition','entity_id'}
        if set(effect) - allowed or not {'type','scope','condition'} <= set(effect):
            raise ValueError('invalid_effect_fields')
        if effect['scope'] not in {'player_state','npcs'}:
            raise ValueError('invalid_effect_scope')
        if not isinstance(effect['condition'], str) or not effect['condition']:
            raise ValueError('invalid_effect_condition')
        if effect['scope'] == 'npcs':
            self._validate_entity(effect.get('entity_id'))
        elif 'entity_id' in effect:
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
            elif effect_type in self._SET_EFFECTS:
                _, entity_scoped = self._SET_EFFECTS[effect_type]
                self._validate_set_effect(effect, entity_scoped)
            elif effect_type == 'resource_delta':
                self._validate_resource_delta(effect)
            elif effect_type in {'condition_add','condition_remove'}:
                self._validate_condition(effect)
            elif effect_type == 'clock_advance':
                if set(effect) != {'type','clock_id','amount'}:
                    raise ValueError('invalid_effect_fields')
                if not isinstance(effect['clock_id'], str) or not effect['clock_id']:
                    raise ValueError('invalid_clock_id')
                if not isinstance(effect['amount'], (int,float)) or isinstance(effect['amount'], bool):
                    raise ValueError('invalid_effect_delta')
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

    def _get_nested_parent(self, target, path):
        current = target
        parts = self._path_parts(path)
        for part in parts[:-1]:
            current = current.get(part)
            if not isinstance(current, dict):
                raise ValueError('effect_path_type_conflict')
        return current, parts[-1]

    def _scope_target(self, state, scope, entity_id=None):
        root = getattr(state, scope)
        if scope in {'npcs','factions','sites'}:
            entity = root.get(entity_id)
            if entity is None:
                raise ValueError('effect_entity_not_found')
            if not isinstance(entity, dict):
                raise ValueError('effect_entity_type_conflict')
            return entity
        return root

    def _apply_resource_delta(self, state, effect):
        target = self._scope_target(state, effect['scope'], effect.get('entity_id'))
        parent, leaf = self._get_nested_parent(target, effect['path'])
        if leaf not in parent:
            raise ValueError('effect_resource_not_found')
        old = parent[leaf]
        if not isinstance(old, (int,float)) or isinstance(old, bool):
            raise ValueError('effect_resource_not_numeric')
        value = old + effect['delta']
        if 'minimum' in effect:
            value = max(effect['minimum'], value)
        if 'maximum' in effect:
            value = min(effect['maximum'], value)
        parent[leaf] = value

    def _conditions(self, state, effect):
        target = self._scope_target(state, effect['scope'], effect.get('entity_id'))
        conditions = target.setdefault('conditions', [])
        if not isinstance(conditions, list):
            raise ValueError('effect_conditions_not_list')
        return conditions

    def _apply_one(self, state, effect):
        effect_type = effect['type']
        if effect_type == 'location_set':
            state.location = effect['location']
            return
        if effect_type == 'resource_delta':
            self._apply_resource_delta(state, effect)
            return
        if effect_type == 'condition_add':
            conditions = self._conditions(state, effect)
            if effect['condition'] not in conditions:
                conditions.append(effect['condition'])
            return
        if effect_type == 'condition_remove':
            conditions = self._conditions(state, effect)
            while effect['condition'] in conditions:
                conditions.remove(effect['condition'])
            return
        if effect_type == 'clock_advance':
            current = state.clocks.get(effect['clock_id'], 0)
            if not isinstance(current, (int,float)) or isinstance(current, bool):
                raise ValueError('invalid_clock_value')
            state.clocks[effect['clock_id']] = current + effect['amount']
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
