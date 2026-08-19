from copy import deepcopy
import math


class VisibilityEngine:
    """Keeps physical lighting, current visibility and discovery as separate layers."""

    def add_light(self, state, light_id, *, location=None, x=0.0, y=0.0, radius=6.0, duration_ticks=None, active=True):
        if not isinstance(light_id, str) or not light_id: raise ValueError('invalid_light_id')
        if not isinstance(radius, (int, float)) or isinstance(radius, bool) or radius <= 0: raise ValueError('invalid_light_radius')
        if duration_ticks is not None and (not isinstance(duration_ticks, int) or isinstance(duration_ticks, bool) or duration_ticks < 1): raise ValueError('invalid_light_duration')
        loc = location if location is not None else state.location
        lights = state.world_flags.setdefault('light_sources', {})
        lights[light_id] = {'location': loc, 'x': float(x), 'y': float(y), 'radius': float(radius), 'created_tick': state.tick, 'duration_ticks': duration_ticks, 'active': bool(active)}
        return deepcopy(lights[light_id])

    def active_lights(self, state, location=None):
        loc = state.location if location is None else location; out = {}
        for lid, light in state.world_flags.get('light_sources', {}).items():
            if not isinstance(light, dict) or not light.get('active', True) or light.get('location') != loc: continue
            duration = light.get('duration_ticks')
            if duration is not None and state.tick >= int(light.get('created_tick', 0)) + int(duration): continue
            out[lid] = deepcopy(light)
        return out

    def visible_now(self, state, object_id, *, location=None, x=None, y=None, base_visible=True):
        loc = state.location if location is None else location; site = state.sites.get(loc, {}) if loc else {}
        darkness = str(site.get('lighting', '')).lower() in {'dark', 'darkness', 'escuro', 'escuridão', 'escuridao'} or bool(site.get('darkness'))
        if not darkness: return bool(base_visible)
        if x is None or y is None: return False
        for light in self.active_lights(state, loc).values():
            if math.hypot(float(x)-float(light.get('x',0)), float(y)-float(light.get('y',0))) <= float(light.get('radius',0)): return bool(base_visible)
        return False

    def discover(self, state, object_id, *, location=None, evidence='observed'):
        if not isinstance(object_id, str) or not object_id: raise ValueError('invalid_discovery_id')
        loc = state.location if location is None else location; discovered = state.discovery.setdefault('objects', {}); key=f'{loc}:{object_id}'
        discovered[key]={'location':loc,'object_id':object_id,'discovered_tick':state.tick,'evidence':str(evidence)}
        return deepcopy(discovered[key])

    def is_discovered(self, state, object_id, *, location=None):
        loc = state.location if location is None else location
        return f'{loc}:{object_id}' in state.discovery.get('objects', {})
