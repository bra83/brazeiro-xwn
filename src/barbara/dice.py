from __future__ import annotations

import random
import secrets
from copy import deepcopy


class RandomSource:
    """Injectable RNG boundary used by the deterministic dice runtime."""

    def randint(self, low: int, high: int) -> int:
        raise NotImplementedError


class SecureRandomSource(RandomSource):
    def __init__(self):
        self._rng = secrets.SystemRandom()

    def randint(self, low: int, high: int) -> int:
        return self._rng.randint(low, high)


class SeededRandomSource(RandomSource):
    def __init__(self, seed):
        self.seed = seed
        self._rng = random.Random(seed)

    def randint(self, low: int, high: int) -> int:
        return self._rng.randint(low, high)


class SequenceRandomSource(RandomSource):
    """Exact RNG for unit tests and replay debugging."""

    def __init__(self, values):
        self.values = list(values)
        self.index = 0

    def randint(self, low: int, high: int) -> int:
        if self.index >= len(self.values):
            raise ValueError('rng_sequence_exhausted')
        value = self.values[self.index]
        self.index += 1
        if not isinstance(value, int) or isinstance(value, bool) or not low <= value <= high:
            raise ValueError('rng_sequence_value_out_of_range')
        return value


class DiceEngine:
    """System-agnostic Dice AST evaluator.

    The engine knows arithmetic and random dice operations, but not what a
    success, critical, armor class or skill means in any RPG. System modules
    compile their rules into this safe AST and interpret the resulting values.
    """

    MAX_DEPTH = 32
    MAX_DICE = 200
    MAX_SIDES = 100000
    COMPARATORS = {'>=', '>', '<=', '<', '==', '!='}

    def __init__(self, random_source=None):
        self.random_source = random_source or SecureRandomSource()

    def _number(self, value, code='invalid_dice_number'):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(code)
        return value

    def _integer(self, value, code='invalid_dice_integer'):
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(code)
        return value

    def _compare(self, left, right, operator):
        if operator not in self.COMPARATORS:
            raise ValueError('invalid_dice_comparator')
        return {
            '>=': left >= right,
            '>': left > right,
            '<=': left <= right,
            '<': left < right,
            '==': left == right,
            '!=': left != right,
        }[operator]

    def _eval(self, expr, trace, depth):
        if depth > self.MAX_DEPTH:
            raise ValueError('dice_ast_too_deep')
        if isinstance(expr, (int, float)) and not isinstance(expr, bool):
            return expr
        if not isinstance(expr, dict):
            raise ValueError('invalid_dice_expression')
        op = expr.get('op')
        if not isinstance(op, str):
            raise ValueError('invalid_dice_operation')

        if op == 'const':
            return self._number(expr.get('value'))

        if op == 'die':
            if set(expr) - {'op', 'sides', 'id'}:
                raise ValueError('invalid_die_fields')
            sides = self._integer(expr.get('sides'), 'invalid_die_sides')
            if sides < 2 or sides > self.MAX_SIDES:
                raise ValueError('invalid_die_sides')
            value = self.random_source.randint(1, sides)
            trace.append({'op': 'die', 'id': expr.get('id'), 'sides': sides, 'value': value})
            return value

        if op == 'dice':
            if set(expr) - {'op', 'count', 'sides', 'id'}:
                raise ValueError('invalid_dice_fields')
            count = self._integer(expr.get('count'), 'invalid_dice_count')
            sides = self._integer(expr.get('sides'), 'invalid_die_sides')
            if not 1 <= count <= self.MAX_DICE or not 2 <= sides <= self.MAX_SIDES:
                raise ValueError('invalid_dice_shape')
            values = []
            for index in range(count):
                value = self.random_source.randint(1, sides)
                trace.append({'op': 'die', 'id': f"{expr.get('id') or 'dice'}:{index}", 'sides': sides, 'value': value})
                values.append(value)
            return values

        if op in {'sum', 'add'}:
            args = expr.get('args')
            if not isinstance(args, list) or not args:
                raise ValueError('invalid_dice_args')
            values = [self._eval(arg, trace, depth + 1) for arg in args]
            total = 0
            for value in values:
                if isinstance(value, list):
                    total += sum(self._number(x) for x in value)
                else:
                    total += self._number(value)
            return total

        if op == 'subtract':
            left = self._number(self._eval(expr.get('left'), trace, depth + 1))
            right = self._number(self._eval(expr.get('right'), trace, depth + 1))
            return left - right

        if op in {'keep_highest', 'keep_lowest'}:
            values = self._eval(expr.get('expr'), trace, depth + 1)
            count = self._integer(expr.get('count', 1), 'invalid_keep_count')
            if not isinstance(values, list) or not values or not 1 <= count <= len(values):
                raise ValueError('invalid_keep_expression')
            ordered = sorted((self._number(v) for v in values), reverse=(op == 'keep_highest'))
            kept = ordered[:count]
            trace.append({'op': op, 'input': list(values), 'kept': list(kept)})
            return kept

        if op == 'count_successes':
            values = self._eval(expr.get('expr'), trace, depth + 1)
            threshold = self._number(expr.get('threshold'))
            comparator = expr.get('comparator', '>=')
            if not isinstance(values, list):
                raise ValueError('invalid_success_pool')
            successes = sum(1 for value in values if self._compare(self._number(value), threshold, comparator))
            trace.append({'op': 'count_successes', 'threshold': threshold, 'comparator': comparator, 'successes': successes})
            return successes

        if op == 'compare':
            left = self._number(self._eval(expr.get('left'), trace, depth + 1))
            right = self._number(self._eval(expr.get('right'), trace, depth + 1))
            comparator = expr.get('comparator')
            success = self._compare(left, right, comparator)
            margin = left - right
            result = {'success': success, 'left': left, 'right': right, 'comparator': comparator, 'margin': margin}
            trace.append({'op': 'compare', **deepcopy(result)})
            return result

        raise ValueError('unsupported_dice_operation')

    def evaluate(self, expression):
        trace = []
        value = self._eval(deepcopy(expression), trace, 0)
        return {'value': deepcopy(value), 'trace': trace, 'expression': deepcopy(expression)}
