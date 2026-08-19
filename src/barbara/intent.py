import re
from copy import deepcopy


class ActionClassifier:
    """Classifies player input before retrieval, rules, world advancement or narration.

    This layer does not resolve mechanics. It only decides which pipeline is allowed
    to consume the input. Mechanical uncertainty remains the exclusive authority of
    MechanicsAuthority/SystemAdapter.
    """

    RULES_QUERY = 'rules_query'
    DIALOGUE = 'dialogue'
    GAME_ACTION = 'game_action'
    META_COMMAND = 'meta_command'
    UI_COMMAND = 'ui_command'
    CHARACTER_THOUGHT = 'character_thought'

    _RULES = (
        r'^\s*(?:regra|regras|rules?)\b',
        r'^\s*(?:como funciona|como funcionam)\b',
        r'^\s*(?:how does|how do)\b.*\b(?:work|rule|rules)\b',
        r'^\s*(?:d[uú]vida|pergunta)\s+(?:de|sobre)\s+regra\b',
    )
    _META = (
        r'^\s*(?:ooc|meta|fora do jogo)\b',
        r'^\s*(?:planejo|planejamos|quero planejar|vamos planejar)\b',
        r'^\s*(?:i plan|we plan|let.?s plan)\b',
    )
    _UI = (
        r'^\s*/(?:ui|map|mapa|atlas|inventory|invent[aá]rio|sheet|ficha|journal|di[aá]rio)\b',
        r'^\s*(?:abrir|fechar|mostrar|ocultar)\s+(?:o\s+|a\s+)?(?:atlas|invent[aá]rio|ficha|di[aá]rio|menu)\s*$',
    )
    _THOUGHT = (
        r'^\s*(?:penso|considero|reflito|imagino|me pergunto)\b',
        r'^\s*(?:i think|i consider|i wonder|i reflect)\b',
    )
    _DIALOGUE = (
        r'^\s*(?:digo|falo|pergunto|respondo|sussurro|grito)\b',
        r'^\s*(?:i say|i ask|i tell|i answer|i whisper|i shout)\b',
    )

    def _matches(self, patterns, text):
        return any(re.search(pattern, text, re.I) for pattern in patterns)

    def classify(self, text):
        if not isinstance(text, str) or not text.strip():
            raise ValueError('invalid_player_input')
        low = text.strip().lower()
        if self._matches(self._UI, low):
            kind = self.UI_COMMAND
        elif self._matches(self._RULES, low):
            kind = self.RULES_QUERY
        elif self._matches(self._META, low):
            kind = self.META_COMMAND
        elif self._matches(self._THOUGHT, low):
            kind = self.CHARACTER_THOUGHT
        elif self._matches(self._DIALOGUE, low):
            kind = self.DIALOGUE
        else:
            kind = self.GAME_ACTION

        world_advances = kind in {self.GAME_ACTION, self.DIALOGUE}
        rules_only = kind == self.RULES_QUERY
        presentation = {
            'narrative': kind in {self.GAME_ACTION, self.DIALOGUE, self.CHARACTER_THOUGHT},
            'rules': rules_only,
            'help': kind in {self.RULES_QUERY, self.META_COMMAND, self.UI_COMMAND},
            'tts': kind in {self.GAME_ACTION, self.DIALOGUE},
        }
        return {
            'input_type': kind,
            'world_advances': world_advances,
            'rules_only': rules_only,
            'mechanics_allowed': kind == self.GAME_ACTION,
            'presentation': deepcopy(presentation),
        }
