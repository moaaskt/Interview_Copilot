# Plano de Execução - Fase 3: Feedback Visual de Áudio & Resiliência

## 🎯 Objetivo
Garantir total confiabilidade e tranquilidade ao usuário durante a entrevista: exibindo um mini VU-meter de atividade de áudio no HUD (para confirmar que o microfone/monitor está captando a fala) e implementando reconexão transparente e automática no WebSocket da Deepgram.

---

## 📝 Tarefas

### Tarefa 1: Implementar Mini VU-Meter de Áudio no `CopilotUI`
- **Arquivo**: [`src/ui.py`](file:///home/moa-dev/projetos/helpIA/src/ui.py)
- **Ações**:
  1. No `header_frame`, adicionar o widget `self.audio_meter_label` entre o status e os botões de ação.
  2. Implementar método `update_audio_level(self, rms: float)`:
     - RMS < 150: `"🎙 ···"` (cor `#585B70`)
     - 150 <= RMS < 800: `"🎙 ▃··"` (cor `#94E2D5`)
     - 800 <= RMS < 2500: `"🎙 ▃▅·"` (cor `#A6E3A1`)
     - RMS >= 2500: `"🎙 ▃▅█"` (cor `#89B4FA`)

### Tarefa 2: Conectar Cálculo de RMS em Tempo Real no `main.py`
- **Arquivo**: [`src/main.py`](file:///home/moa-dev/projetos/helpIA/src/main.py)
- **Ações**:
  1. No método `on_audio_data(self, data: bytes)`:
     - Calcular RMS do chunk recebido utilizando `numpy`.
     - Chamar `self.ui.update_audio_level(rms)`.
  2. Garantir que o cálculo ocorra em < 0.1ms sem bloquear o event loop.

### Tarefa 3: Implementar Reconexão Automática e Status no `Transcriber`
- **Arquivos**: [`src/transcriber.py`](file:///home/moa-dev/projetos/helpIA/src/transcriber.py) e [`src/main.py`](file:///home/moa-dev/projetos/helpIA/src/main.py)
- **Ações**:
  1. Em `Transcriber`, adicionar callback `on_connection_change: Optional[Callable[[bool], None]]`.
  2. Adicionar método assíncrono `reconnect(self)` com backoff exponencial quando a conexão fechar inesperadamente.
  3. No `main.py`, tratar a callback para atualizar o status na UI (`ui.set_status("🔄 Reconectando áudio...", "#F9E2AF")` e restaurar para `● Pronto` quando reconectado).

### Tarefa 4: Criar Testes Automatizados & Validação
- **Arquivo**: [`tests/test_audio_resilience.py`](file:///home/moa-dev/projetos/helpIA/tests/test_audio_resilience.py)
- **Ações**:
  1. Testar renderização do VU-meter para diferentes faixas de RMS.
  2. Testar cálculo de RMS a partir de buffers sintéticos de PCM.
  3. Testar notificação de conexão e lógica de reconexão do `Transcriber`.
  4. Executar bateria completa via `python -m unittest discover tests`.

---

## 🔍 Critérios de Aceitação / Verificação
- [ ] O mini VU-meter exibe feedback visual com alteração de intensidade em tempo real conforme o nível de áudio recebido.
- [ ] Silêncio mantém o indicador discreto (`🎙 ···`), sem poluição visual.
- [ ] Quedas no WebSocket da Deepgram disparam notificação visual e tentativa de reconexão sem quebrar o app.
- [ ] 100% dos testes unitários e de regressão aprovados.
