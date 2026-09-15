# Plano de Execução - Fase 4: Tela de Configurações & Quick Prompts de Entrevista

## 🎯 Objetivo
Implementar uma central de configurações completa e ergonômica para o **helpIA**, permitindo ao candidato:
1. Selecionar o dispositivo de áudio/placa de som e testar a captação com um medidor em tempo real.
2. Customizar o System Prompt da IA (persona do candidato) e escolher o estilo de resposta (Direta, Técnica ou STAR).
3. Configurar atalhos de teclado (hotkeys) personalizados.
4. Acessar botões de perguntas rápidas de entrevista dev com disparo imediato da IA.

---

## 📝 Tarefas

### Tarefa 1: Implementar `src/config_manager.py` para Persistência de Preferências
- **Arquivo**: `src/config_manager.py` (Novo)
- **Ações**:
  1. Criar classe `ConfigManager` que gerencia o arquivo `helpia_config.json`.
  2. Implementar schema de configuração padrão (dispositivo selecionado, estilo de resposta, system prompt padrão de Moacir Neto, mapa de hotkeys, lista de perguntas rápidas de entrevista dev).
  3. Métodos: `load_config()`, `save_config()`, `reset_defaults()`, `get(key, default)`, `set(key, value)`.
  4. Adicionar `helpia_config.json` ao `.gitignore` para proteger customizações locais do usuário.

### Tarefa 2: Adicionar Enumeração e Seleção de Dispositivos em `src/audio_capture.py`
- **Arquivo**: `src/audio_capture.py`
- **Ações**:
  1. Implementar método estático/classe `list_available_devices()`:
     - No Windows: enumera dispositivos loopback WASAPI via `pyaudiowpatch`.
     - No Linux: enumera sinks/monitors disponíveis via `pactl` e `sounddevice.query_devices()`.
     - Retorna lista de dicionários `{ "index": int | str, "name": str, "is_default": bool }`.
  2. Permitir passagem de `device_index` opcional no `__init__` e método `set_device(device_index)`.
  3. Suportar reinício limpo do stream de áudio com o novo dispositivo selecionado.

### Tarefa 3: Adicionar Estilos de Resposta e Prompt Dinâmico em `src/llm_service.py`
- **Arquivo**: `src/llm_service.py`
- **Ações**:
  1. Adicionar suporte a múltiplos estilos de resposta:
     - `direta`: 3-4 frases concisas e diretas (padrão atual).
     - `tecnica`: 5-7 frases focadas em arquitetura, escalabilidade e trade-offs técnicos.
     - `star`: Formato estruturado (Situação, Tarefa, Ação, Resultado).
  2. Adicionar método `set_response_style(style: str)`.
  3. Adicionar método `set_system_prompt(custom_prompt: str)` para permitir edição em tempo real do histórico profissional e regras de persona.

### Tarefa 4: Criar `SettingsWindow` (Modal de Configurações) em `src/ui.py`
- **Arquivo**: `src/ui.py`
- **Ações**:
  1. Criar classe `SettingsWindow(ctk.CTkToplevel)` com estilo visual Dark Mode premium:
     - **Aba Áudio**: Dropdown com lista de placas/dispositivos, botão aplicar e medidor VU em tempo real (`🎙 ▃▅█`) sincronizado com o fluxo de áudio para teste de sensibilidade.
     - **Aba IA & Persona**: Seletor de estilo (`ctk.CTkSegmentedButton`: Direta, Técnica, STAR), caixa de texto editável com o System Prompt e botão "Restaurar Padrão".
     - **Aba Atalhos**: Entradas para remapear teclas de atalho de Gravação, Resposta, Limpeza e Janela.
     - **Aba Perguntas Rápidas**: Lista de perguntas com opção de adicionar e remover perguntas customizadas.
  2. Callbacks de salvamento integrando com `ConfigManager`.

### Tarefa 5: Integrar Botão de Configurações `⚙` e Barra de Quick Prompts no HUD
- **Arquivos**: `src/ui.py` e `src/main.py`
- **Ações**:
  1. No header do `CopilotUI`, adicionar botão `⚙` (engrenagem) ao lado dos presets para abrir `SettingsWindow`.
  2. Adicionar atalho global configurável (padrão `<F12>`) para abrir as configurações.
  3. Adicionar barra ou drawer de **Perguntas Rápidas de Entrevista**:
     - Botões rápidos: "Apresentação Pessoal", "Arquitetura Recente", "Bugs em Produção", "SQL vs NoSQL", "Desafio Técnico".
     - Ao clicar em uma pergunta: preenche a caixa de transcrição e dispara imediatamente a geração da IA (`self.respond_now()`).
  4. No `main.py`, conectar eventos da tela de configurações com `audio_capture.set_device`, `llm_service.set_response_style` e `llm_service.set_system_prompt`.

### Tarefa 6: Testes Automatizados & Verificação de Regressão
- **Arquivo**: `tests/test_settings_and_quick_prompts.py` (Novo)
- **Ações**:
  1. Testar persistência, leitura e fallback do `ConfigManager`.
  2. Testar troca de estilos de resposta e alteração de system prompt no `LLMService`.
  3. Testar disparo de perguntas rápidas acionando o pipeline de resposta.
  4. Testar listagem de dispositivos de áudio sem quebrar em plataformas sem hardware.
  5. Executar suíte completa (`python -m unittest discover -s tests -p "test_*.py"`) garantindo 100% de sucesso.

---

## 🔍 Critérios de Aceitação / Verificação
- [x] O usuário consegue abrir a tela de configurações clicando no ícone `⚙` ou pressionando `F12`.
- [x] O dropdown de áudio lista as placas/dispositivos disponíveis e permite selecionar o dispositivo ativo.
- [x] O medidor de nível em tempo real exibe atividade na tela de configurações ao detectar áudio.
- [x] A persona / system prompt pode ser editada livremente na UI e é salva em `helpia_config.json`.
- [x] A seleção de estilo de resposta (Direta vs. Técnica vs. STAR) altera a diretiva de resposta da IA.
- [x] Botões de perguntas rápidas de entrevista dev inserem o texto e disparam a geração da IA instantaneamente.
- [x] Atalhos customizados são persistidos e aplicados à janela.
- [x] A aplicação continua leve, sem travar o event loop do asyncio e com todos os testes passando.
