# Integração do Motor Barbara 1.0

A integração recomendada com apps Android/desktop deve usar `HostBridge` como fronteira estável, mantendo o núcleo desacoplado da UI.

## Fluxo

1. O host mantém o estado da campanha como JSON retornado por `CampaignState.to_json()`.
2. Cada ação envia um objeto com `text`, `request_id` e, quando necessário, `mechanical`, `importance` e `resolution`.
3. `HostBridge.turn()` devolve `state` atualizado e `result` do turno.
4. O host persiste o novo `state` somente após sucesso.
5. Em retry após timeout/process restart, reutilize o mesmo `request_id`; a idempotência persistida impede avanço duplicado.

## Exemplo

```python
from barbara import BarbaraEngine, HostBridge

bridge = HostBridge(BarbaraEngine())
state = bridge.new_campaign('campanha-1','gurps')
out = bridge.turn(state, {'text':'Olho ao redor','request_id':'turno-1'})
state = out['state']
result = out['result']
```

## Contrato para UI

`result.presentation` define os canais que a UI deve usar para narrativa, regras, ajuda e TTS. `result.turn_plan` informa modo e intenção. `result.system_profile` informa adapter e protocolo mecânico. `result.resolution` contém apenas resolução já validada/vinculada ao sistema.

O host não deve editar diretamente `world_flags`, `npcs`, `factions`, `rumors`, `events`, clocks ou ledgers a partir de saída do LLM. Mudanças estruturais continuam sob autoridade do núcleo/adapters.
