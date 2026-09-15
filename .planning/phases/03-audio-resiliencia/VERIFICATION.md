# Plano de Verificação - Fase 3: Feedback Visual de Áudio & Resiliência

## Cenários de Teste

### 1. Indicador de Nível de Áudio (Mini VU-Meter)
- **Silêncio**:
  - Quando nenhum som é emitido, `update_audio_level(0)` deve exibir `🎙 ···` em cor cinza suave (`#585B70`).
- **Fala / Sinal Moderado**:
  - Injetando RMS de 1200, deve exibir `🎙 ▃▅·` em verde (`#A6E3A1`).
- **Pico de Áudio**:
  - Injetando RMS de 3500, deve exibir `🎙 ▃▅█` em azul vibrante (`#89B4FA`).

### 2. Reconexão do WebSocket Deepgram
- Simular desconexão disparando o handler `on_close` no `Transcriber`.
- O estado de conexão deve alternar para `False` e disparar a callback `on_connection_change(False)`.
- A UI deve exibir aviso visual de reconexão.
- Uma nova tentativa de conexão deve ser disparada sem travar a interface.

### 3. Testes Automatizados
- Executar: `./venv/bin/python -m unittest tests/test_audio_resilience.py`
- Executar suíte completa: `./venv/bin/python -m unittest discover tests`
- Todos os testes devem passar com código de saída 0.
