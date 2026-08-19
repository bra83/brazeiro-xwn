class FallbackNarrator:
    """Deterministic offline-safe narrator built only from canonical state.

    The fiction path deliberately stays in-world. Provider failure details are
    returned as metadata by ActionPipeline, not dumped into the scene itself.
    """

    def _weather_phrase(self, weather):
        if not isinstance(weather, dict) or not weather:
            return ''
        parts = []
        rain = weather.get('rain')
        if rain:
            labels = {'light':'uma chuva leve', 'moderate':'chuva constante', 'heavy':'chuva pesada', 'storm':'uma tempestade'}
            parts.append(labels.get(str(rain).lower(), f'chuva {rain}'))
        wind = weather.get('wind')
        if wind:
            labels = {'light':'vento leve', 'moderate':'vento firme', 'strong':'vento forte', 'gale':'ventania'}
            parts.append(labels.get(str(wind).lower(), f'vento {wind}'))
        if not parts and weather.get('condition'):
            parts.append(str(weather['condition']))
        return ', '.join(parts)

    def _scene_anchor(self, context):
        name = context.get('location_name') or context.get('location_id') or 'o local atual'
        terrain = context.get('terrain')
        description = (context.get('description') or '').strip()
        features = list(context.get('features') or ())[:5]
        weather = self._weather_phrase(context.get('weather'))

        if description:
            first = f'{name}: {description.rstrip(". ")}.'
        elif terrain:
            first = f'{name} se apresenta como terreno de {terrain}.'
        else:
            first = f'Você permanece em {name}.'
        if weather:
            first += f' O tempo traz {weather}.'
        if features:
            first += ' No que já é visível e confirmado, destacam-se ' + ', '.join(features) + '.'
        return first

    def _mechanical_anchor(self, result):
        resolution = result.get('resolution')
        if not isinstance(resolution, dict):
            return ''
        outcome = resolution.get('outcome') or resolution.get('result')
        effects = result.get('effects_applied') or resolution.get('effects') or []
        labels = {
            'success': 'O que você tentou alcançou o resultado mecânico esperado',
            'failure': 'A tentativa não alcançou o resultado mecânico pretendido',
            'critical_success': 'A tentativa alcançou um sucesso crítico',
            'critical_failure': 'A tentativa terminou em falha crítica',
            'partial': 'A tentativa produziu apenas um resultado parcial',
            'tie': 'A disputa terminou empatada',
        }
        sentence = labels.get(outcome, '') if outcome else ''
        if effects:
            sentence += ('. ' if sentence else '') + 'As consequências já determinadas pelo motor passam a valer a partir deste instante'
        return sentence + ('.' if sentence else '')

    def _rules_fallback(self, context):
        evidence = context.get('evidence') if isinstance(context, dict) else None
        evidence = evidence if isinstance(evidence, list) else []
        rule_texts = [str(e.get('text', '')).strip() for e in evidence if isinstance(e, dict) and e.get('kind') == 'RULE' and e.get('text')]
        if rule_texts:
            return 'A consulta local de regras continua disponível. Evidência recuperada:\n\n' + '\n\n'.join(rule_texts[:3])
        return 'A consulta narrativa avançada não está disponível neste instante, e nenhuma regra foi encontrada localmente para responder com segurança.'

    def render(self, state, text, result, context, reason='provider_unavailable'):
        mode = result.get('mode') or 'fiction'
        phase = result.get('phase') or 'COMPLETED'
        if mode != 'fiction':
            return self._rules_fallback(context)

        first = self._scene_anchor(context)
        action = str(text).strip()
        if action:
            first += f' Sua ação declarada é: “{action}”.'

        if phase == 'WAITING_FOR_ROLL':
            second = (
                'A cena chega exatamente ao ponto em que o resultado ainda é incerto. Nada além desse limite acontece por enquanto: '
                'a posição, o ambiente e as pessoas permanecem como estavam até que a rolagem determine o que muda.'
            )
        else:
            mechanical = self._mechanical_anchor(result)
            second = mechanical or (
                'A cena permanece coerente com o que já estava presente. O ambiente não ganha novos acidentes, criaturas, objetos ou passagens apenas para preencher o silêncio; '
                'o que existe continua sendo aquilo que o Atlas e os acontecimentos anteriores já estabeleceram.'
            )
            if result.get('world_advanced'):
                second += ' O tempo avança na medida já registrada pelo mundo, preservando as consequências que realmente ocorreram.'

        third = (
            'Nada obriga sua próxima decisão. A situação fica aberta a partir daqui, exatamente neste lugar e neste estado, para que você escolha como continuar.'
        )
        return '\n\n'.join((first, second, third))


class ProviderFailurePolicy:
    FALLBACK_CODES = {
        'narrative_geography_contradiction',
        'narrative_too_few_paragraphs',
        'narrative_too_short',
        'invalid_gemini_response',
        'gemini_transport_error',
    }

    def is_fallback_safe(self, exc, recovery=None):
        if recovery is not None:
            try:
                if recovery.classify(exc) in getattr(recovery, 'RETRYABLE', set()):
                    return True
            except Exception:
                pass
        code = str(exc).split(':', 1)[0]
        return code in self.FALLBACK_CODES
