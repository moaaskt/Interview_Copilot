# Pesquisa Técnica - Fase 3: Feedback Visual de Áudio & Resiliência

## 1. Contexto & Problema
Durante entrevistas técnicas, dois pontos geram alta ansiedade para o candidato:
1. **Incerteza de Captura**: O usuário não sabe se o microfone/monitor está efetivamente captando o som ou se está falando no vácuo até a resposta aparecer.
2. **Queda de Conexão WebSocket**: O Deepgram WebSocket pode ser desconectado por oscilação de rede ou inatividade prolongada. Se isso acontecer, a aplicação precisa se recuperar automaticamente sem intervenção manual.

---

## 2. Decisões Técnicas

### 2.1. Cálculo de RMS e Indicador de Nível de Áudio
- **Entrada**: Chunks PCM 16-bit mono a 16.000 Hz (100ms = 1600 amostras = 3200 bytes).
- **Processamento**:
  - `numpy.frombuffer(data, dtype=np.int16)`
  - `rms = float(np.sqrt(np.mean(samples.astype(np.float32)**2)))`
  - Overhead de CPU: < 0.05ms por chunk de 100ms (10 vezes por segundo), mantendo consumo abaixo de 0.2% da CPU (RNF02).
- **Representação Visual no HUD**:
  - Mini VU-meter em widget label no cabeçalho ou na barra de status:
    - Silêncio (RMS < 150): `🎙 ···` (cor escura/apagada `#585B70`)
    - Nível Baixo (150 <= RMS < 800): `🎙 ▃··` (`#94E2D5`)
    - Nível Médio (800 <= RMS < 2500): `🎙 ▃▅·` (`#A6E3A1`)
    - Nível Alto (RMS >= 2500): `🎙 ▃▅█` (`#89B4FA`)

### 2.2. Resiliência do Transcriber e Reconexão Transparente
- **Detecção de Queda**:
  - Handlers `on_close` e `on_error` no SDK da Deepgram disparam transição de estado `is_connected = False`.
  - Callback `on_connection_change(is_connected: bool)` notifica `main.py` e a UI.
- **Reconexão Automática**:
  - Método assíncrono `ensure_connected()` ou tarefa de monitoramento em background.
  - Backoff exponencial com jitter (ex: 2s -> 4s -> 8s) caso a conexão falhe, até restaurar o WebSocket.
  - O buffer de transcrição e o estado da aplicação permanecem íntegros.

---

## 3. Riscos & Mitigações
- **Risco**: Falso positivo de ruído ambiente constante simulando fala.
  - *Mitigação*: Threshold de corte calibrado para 150 RMS; silêncio ambiente de sala fica tipicamente entre 30 e 90 RMS.
- **Risco**: Loop infinito de reconexão sobrecarregando a CPU caso a API Key expire.
  - *Mitigação*: Backoff exponencial com limite máximo de 10s e log de advertência apropriado.
