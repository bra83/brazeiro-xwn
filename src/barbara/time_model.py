from dataclasses import dataclass


@dataclass(frozen=True)
class TimeUnit:
    name: str
    seconds: int

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name:
            raise ValueError('invalid_time_unit')
        if not isinstance(self.seconds, int) or isinstance(self.seconds, bool) or self.seconds <= 0:
            raise ValueError('invalid_time_unit_seconds')


@dataclass(frozen=True)
class TimeModel:
    system_id: str
    round: TimeUnit
    exploration_turn: TimeUnit
    travel_turn: TimeUnit

    def seconds_for(self, unit, amount=1):
        if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
            raise ValueError('invalid_time_amount')
        mapping = {'round': self.round, 'exploration': self.exploration_turn, 'travel': self.travel_turn}
        if unit not in mapping:
            raise ValueError('unknown_time_unit')
        return mapping[unit].seconds * amount


_DEFAULTS = {
    'dnd': (6, 600, 3600), 'mystara': (10, 600, 3600), 'mausritter': (6, 600, 3600),
    'forbidden_lands': (6, 900, 21600), 'the_one_ring': (6, 600, 28800), 'gurps': (1, 600, 3600),
    'worlds_without_number': (6, 600, 3600), 'stars_without_number': (6, 600, 3600),
    'cities_without_number': (6, 600, 3600), 'ashes_without_number': (6, 600, 3600),
    'tales_from_the_loop': (6, 600, 3600), 'traveller_2e': (6, 600, 21600),
}


def default_time_model(system_id):
    if system_id not in _DEFAULTS:
        raise KeyError(system_id)
    r, e, t = _DEFAULTS[system_id]
    return TimeModel(system_id, TimeUnit('round', r), TimeUnit('exploration', e), TimeUnit('travel', t))
