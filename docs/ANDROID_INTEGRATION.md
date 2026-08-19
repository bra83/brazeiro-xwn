# Integração Android do Motor Barbara 1.0

## Estratégia escolhida

O repositório `brazeiro-xwn` é a fonte de verdade do motor. Os outros projetos **não copiam o código-fonte do Barbara** para dentro de cada app.

Cada app Android integra uma **wheel versionada/pinada** do Motor Barbara e chama uma fronteira JSON estável. Para projetos Android Studio, a rota recomendada é empacotar a wheel junto com um runtime Python embarcado (por exemplo, Chaquopy) e chamar `barbara.android` a partir de Kotlin/Java.

Isso evita quatro problemas: divergência de cópias do motor, necessidade de um servidor próprio, dependência do GitHub em tempo de jogo e reimplementação parcial do Barbara em Kotlin.

## Fluxo de distribuição

1. O Motor Barbara é desenvolvido e testado neste repositório.
2. A CI gera `motor_barbara-1.0.0-py3-none-any.whl`.
3. Cada projeto de jogo fixa **uma versão exata** da wheel. Nunca instala `main` diretamente em produção.
4. No build do app, a wheel é incorporada ao APK/AAB pelo runtime Python do projeto.
5. Em execução, Kotlin/Java conversa apenas com `barbara.android` por JSON.
6. Atualizar o motor em um projeto significa trocar a wheel pinada e rodar a suíte de integração daquele app.

O app não precisa de rede para carregar o motor, estado, regras já ingeridas ou Mundo Vivo. Rede só é necessária para serviços externos usados pelo projeto, como Gemini.

## Estado e RAG

Cada campanha mantém seu JSON de estado no armazenamento privado do app. O RAG usa um SQLite privado do app, um banco por projeto/perfil quando conveniente. O caminho é passado a `barbara.android.configure(rag_db_path=...)`.

Nunca coloque `GEMINI_API_KEY` dentro do repositório. A chave entra por configuração segura do app/build e é passada em runtime a `configure`.

## Contrato Kotlin -> Python

Inicialização lógica:

```text
configure(api_key=..., model="gemini-3.5-flash-lite", rag_db_path=".../barbara-rag.sqlite3")
```

Criação de campanha:

```text
new_campaign("campanha-123", "gurps") -> state_json
```

Turno:

```json
{
  "text": "Examino a porta",
  "request_id": "uuid-estavel-do-turno",
  "mechanical": false,
  "importance": "normal"
}
```

Retorno:

```json
{
  "state": "{...json canônico atualizado...}",
  "result": {
    "tick": 1,
    "presentation": {},
    "turn_plan": {},
    "system_profile": {}
  }
}
```

O host grava `state` **somente depois** de receber sucesso. Reenvio do mesmo `request_id` é seguro e idempotente.

## Migração dos projetos existentes

A substituição deve ser feita projeto por projeto, sem apagar a camada antiga no primeiro commit:

1. adicionar runtime Python + wheel pinada;
2. criar um `BarbaraRepository`/`BarbaraGateway` Kotlin que chama somente a API JSON;
3. mapear o save atual do projeto para `CampaignState`;
4. colocar o Barbara atrás de uma feature flag local;
5. rodar as mesmas cenas no fluxo antigo e no Barbara, comparando regras, estado e UI;
6. corrigir qualquer adapter/mapeamento específico do projeto;
7. tornar Barbara o padrão;
8. remover o motor antigo só depois da paridade daquele app ficar verde.

## Ordem sugerida

Começar pelo projeto com estrutura de mestre mais completa e mais testes de regressão, pois ele serve de referência para os demais. Depois migrar os projetos que compartilham família mecânica: Mystara/D&D, XWN, Year Zero, e então os sistemas específicos.

## Regra importante

GitHub é a **origem e distribuição de build**, não uma dependência de runtime. O jogador não baixa arquivos do GitHub durante a partida. A versão aprovada do motor vai dentro do próprio app.
