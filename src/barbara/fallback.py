from copy import deepcopy


class FallbackNarrator:
    """Deterministic, offline-safe narration derived only from canonical state.

    It is intentionally conservative: no invented NPC actions, geography, items,
    damage or hidden consequences. Its job is to keep the table playable when an
    LLM is unavailable or its prose violates continuity.
    """

    def _scene_anchor(self, context):
        name = context.get('location_name') or context.get('location_id') or 'o local atual'
        terrain = context.get('terrain')
        description = (context.get('description') or '').strip()
        features = list(context.get('features') or ())[:4]
        bits = [f"Você permanece em {name}."]
        if terrain:
            bits.append(f"O terreno confirmado aqui é {terrain}.")
        if description:
            bits.append(description.rstrip('. ') + '.')
        elif features:
            bits.append('Entre os elementos confirmados da área estão ' + ', '.join(features) + '.')
        return ' '.join(bits)

    def _mechanical_anchor(self, result):
        resolution = result.get('resolution')
        if not isinstance(resolution, dict):
            return ''
        outcome = resolution.get('outcome') or resolution.get('result')
        rolls = resolution.get('rolls') or []
        effects = result.get('effects_applied') or resolution.get('effects') or []
        pieces = []
        if outcome:
            labels = {
                'success': 'A resolução mecânica confirmou sucesso',
                'failure': 'A resolução mecânica confirmou falha',
                'critical_success': 'A resolução mecânica confirmou um sucesso crítico',
                'critical_failure': 'A resolução mecânica confirmou uma falha crítica',
                'partial': 'A resolução mecânica confirmou um resultado parcial',
            }
            pieces.append(labels.get(outcome, f'A resolução mecânica registrou {outcome}'))
        if rolls:
            pieces.append('A rolagem já foi resolvida pelo motor e não será reinterpretada')
        if effects:
            pieces.append(f'{len(effects)} consequência(s) mecânica(s) autorizada(s) foram aplicadas ao estado')
        return '. '.join(pieces) + ('.' if pieces else '')

    def render(self, state, text, result, context, reason='provider_unavailable'):
        mode = result.get('mode') or 'fiction'
        phase = result.get('phase') or 'COMPLETED'
        if mode != 'fiction':
            return (
                'O subsistema narrativo avançado não está disponível neste instante, mas o Motor Barbara permaneceu ativo. '
                'Nenhuma mudança de mundo foi inventada pelo fallback e o estado canônico foi preservado.'
            )

        first = self._scene_anchor(context)
        action = str(text).strip()
        if action:
            first += f' Sua declaração foi: “{action}”'

        if phase == 'WAITING_FOR_ROLL':
            second = (
                'A ação chegou ao primeiro ponto de incerteza mecânica e foi interrompida antes de produzir um resultado. '
                'O mundo não avançou além desse ponto; faça a rolagem solicitada para que o motor continue a mesma ação.'
            )
        else:
            mechanical = self._mechanical_anchor(result)
            second = mechanical or (
                'O estado da cena foi mantido a partir dos fatos já registrados. Nada além do que o motor autorizou foi acrescentado: '
                'nenhum rio, criatura, objeto, dano ou mudança de posição surgiu apenas para preencher a narração.'
            )
            if result.get('world_advanced'):
                second += ' O tempo e as reações do mundo considerados nesta passagem já estão registrados no estado canônico.'

        third = (
            'A cena continua a partir exatamente dessa posição. Você pode agir normalmente; quando o narrador principal voltar, '
            'ele receberá este mesmo estado persistido e não precisará reconstruir ou adivinhar o que aconteceu.'
        )
        return '\n\n'.join((first, second, third))


class ProviderFailurePolicy:
    NARRATIVE_CODES = {
        'invalid_provider_output','unknown_provider_field','provider_state_patch_forbidden',
        'invalid_narration','narrativa_resumida_demais','player_agency_violation',
        'resultado_mecanico_sem_autoridade','perguntas_nao_respondidas',
        'cena_sem_abertura_para_decisao','historia_de_abertura_resumida_demais',
        'historia_substituida_por_relatorio','historia_sem_cena_suficiente',
    }

    def is_provider_failure(self, exc, recovery=None):
        if recovery is not None:
            try:
                if recovery.classify(exc) in getattr(recovery, 'RETRYABLE', set()):
                    return True
            except Exception:
                pass
        code = str(exc).split(':', 1)[0]
        return code in self.NARRATIVE_CODES
