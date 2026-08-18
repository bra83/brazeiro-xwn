# Herança direta — Forbidden Lands 3.2 → XWN 3.0

Fonte examinada: `Braseiro_Forbidden_Lands_3.2.0_MESTRE_SEPARADO_REGRAS_AUDITAVEIS_ANDROID_STUDIO(1).zip`, fornecido pelo usuário nesta rodada.

## Código/contratos efetivamente consultados

- `src/services/audioEngineV2.ts`
- `src/services/GeminiClientService.ts`
- `src/services/NarrativeDirectorService.ts`
- `src/services/ForbiddenLandsNarrativeStyleService.ts`
- `src/services/NarrativeQualityGateService.ts`
- `src/services/LivingWorldService.ts`
- `src/services/LivingWorldAutomationService.ts`
- `src/services/SoundscapeService.ts`
- `src/services/MobileRuntimeService.ts`
- `src/services/RuleAuthorityService.ts`
- `src/services/RulesRetrievalService.ts`
- `src/services/TokenImportService.ts`
- `src/services/NpcTokenAutoService.ts`

## Direção do Mestre portada

O XWN 3.0 preserva os princípios encontrados no diretor/quality gate do Forbidden Lands: câmera em camadas, mundo já em movimento, NPCs em atividade, conhecimento limitado, congelamento de ficção para mensagens meta, primeira incerteza significativa, testes só para incerteza com consequência e separação rígida entre ficção e resolução mecânica.

O corpus/dossiês do projeto registra 66h29m58s de actual play analisável como base cumulativa. Esse número pertence ao material de auditoria do projeto; as gravações completas não são incorporadas a este pacote XWN.

## Áudio portado

A implementação web 3.0 replica as características concretas do `audioEngineV2.ts`: Charon, cadeia de modelos TTS Gemini, segmentação 320/680, pré-síntese do próximo trecho, cache, cancelamento por sessão/run id, decode WebAudio/PCM 24 kHz e ducking.

## O que não é uma cópia literal

O XWN é JavaScript/PWA e não copia os plugins Kotlin/Capacitor do aplicativo Android. O contrato funcional foi portado para APIs de navegador. A futura build Android pode reutilizar a ponte nativa separadamente.
