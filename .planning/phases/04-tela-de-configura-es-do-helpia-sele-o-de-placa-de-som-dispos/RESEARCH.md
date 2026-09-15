# Pesquisa Técnica - Fase 4: Tela de Configurações & Quick Prompts de Entrevista

## 1. Contexto & Objetivos
A Fase 4 expande o **Interview Copilot (`helpIA`)** de uma ferramenta com configurações estáticas para uma plataforma totalmente adaptável às necessidades dinâmicas do candidato durante entrevistas técnicas reais:
1. **Seleção de Dispositivo de Áudio**: Permitir que o usuário escolha explicitamente qual placa de som/sink/dispositivo WASAPI capturar, evitando confusão quando múltiplos headsets ou monitores virtuais estão plugados.
2. **Medidor de Nível em Tempo Real**: Exibir um medidor visual dinâmico na tela de configurações (reaproveitando o cálculo de RMS do header) para testar a sensibilidade do áudio antes da entrevista.
3. **Editor de System Prompt & Contexto**: Permitir customizar facilmente a persona, histórico profissional e stack técnica do candidato sem necessidade de alterar o código-fonte.
4. **Estilos de Resposta da IA**: Permitir alternar entre modo "Direta & Concisa" (3–4 frases), "Técnica & Aprofundada" (arquitetura e detalhes) e "STAR" (Situação, Tarefa, Ação, Resultado).
5. **Hotkeys Customizáveis**: Interface para remapear atalhos de teclado conforme o teclado e preferências ergonômicas do usuário.
6. **Quick Prompts de Entrevista**: Botões de acesso rápido com perguntas clássicas de entrevista técnica dev (ex: "Apresentação pessoal", "Arquitetura recente", "Bugs em produção", "SQL vs NoSQL") que injetam a pergunta e disparam a resposta imediatamente.

---

## 2. Análise Técnica dos Componentes

### 2.1. Gerenciador de Configuração (`src/config_manager.py`)
- **Armazenamento**: Arquivo JSON local (`helpia_config.json`) na raiz do projeto, preservado entre reinicializações e gitignorado.
- **Estrutura de Dados**:
  ```json
  {
    "audio": {
      "device_index": null,
      "device_name": "Padrão do Sistema"
    },
    "llm": {
      "response_style": "direta",
      "custom_persona": null
    },
    "hotkeys": {
      "toggle_recording": "<Control-space>",
      "respond_now": "<Control-Return>",
      "clear_session": "<Escape>",
      "cycle_position": "<F8>",
      "cycle_opacity": "<F10>",
      "open_settings": "<F12>"
    },
    "quick_questions": [
      "Fale mais sobre você e sua trajetória profissional",
      "Explique a arquitetura de um projeto recente que você desenvolveu",
      "Como você aborda a investigação e resolução de um bug crítico em produção?",
      "Qual é a sua experiência prática com bancos relacionais (MySQL/PostgreSQL) vs NoSQL?",
      "Qual foi um desafio técnico complexo que você enfrentou e como superou?"
    ]
  }
  ```
- **Fallback Seguro**: Se o arquivo não existir ou estiver corrompido, carrega imediatamente os padrões testados da aplicação.

### 2.2. Enumeração de Dispositivos de Áudio (`src/audio_capture.py`)
- **Windows (WASAPI)**:
  - `pyaudiowpatch.PyAudio()` enumera dispositivos com `isLoopbackDevice` ou hosts WASAPI.
- **Linux (PulseAudio / PipeWire)**:
  - Executa `pactl list short sinks` e `sounddevice.query_devices()`, identificando monitores e dispositivos de entrada válidos.
- **API Exposta**:
  - `AudioCapture.list_devices() -> list[dict]`: Retorna id, nome amigável e indicador de padrão.
  - `AudioCapture.change_device(device_id: int | str, loop: asyncio.AbstractEventLoop)`: Reinicia o stream de captura de forma transparente sem reiniciar a janela principal.

### 2.3. Configuração de Estilos de Resposta no `LLMService`
- **Modos Suportados**:
  1. `direta` (padrão): 3 a 4 frases, ultra-conciso, vocabulário natural e humilde.
  2. `tecnica`: 5 a 7 frases, foco em decisões arquiteturais, trade-offs, escalabilidade, design patterns e robustez.
  3. `star`: Formato estruturado: Situação (1 frase), Tarefa (1 frase), Ação (2 frases), Resultado mensurável (1 frase).
- **Injeção Dinâmica**: `LLMService.set_response_style(style_name: str)` atualiza a diretiva de prompt instantaneamente para a próxima geração.

### 2.4. Tela de Configurações Modal (`SettingsWindow` em `src/ui.py`)
- Construída com `ctk.CTkToplevel` com `attributes("-topmost", True)` e design escuro harmonioso com o HUD principal (`#1E1E2E` / `#11111B` / `#89B4FA`).
- **Abas Organizacionais**:
  - 🎙 **Áudio**: Dropdown de seleção de placa/dispositivo, mini VU-meter dinâmico de teste (`self.test_vu_meter`), botão de salvar/testar.
  - 🧠 **IA & Persona**: Editor de texto do System Prompt do Moacir Neto, seletor de estilo de resposta (`Direta`, `Técnica`, `STAR`), botão "Restaurar Padrão".
  - ⌨ **Atalhos**: Visualizador e editor de teclas mapeadas para cada ação.
  - ⚡ **Perguntas Rápidas**: Gerenciador da lista de quick prompts de entrevista.

### 2.5. Barra / Gaveta de Quick Prompts no HUD
- No HUD principal (`CopilotUI`):
  - Botão `⚙` no header para abrir a tela de configurações.
  - Botão `⚡ Perguntas Rápidas` ou linha expansível com botões de atalho:
    - Clicar em qualquer botão define a transcrição (`✔ [Pergunta Rápida]: ...`) e chama `on_respond_now()` imediatamente.

---

## 3. Testabilidade & Riscos
- **Riscos Identificados**:
  - Alteração de dispositivo de áudio enquanto o stream está ativo pode gerar falha se o dispositivo for desconectado. *Mitigação*: Bloco try/except com rollback para o dispositivo padrão.
  - Conflito de hotkeys com o sistema operacional (ex: atalhos globais de captura do Windows/Linux). *Mitigação*: Validação sintática e salvamento de atalhos válidos no Tkinter.
- **Estratégia de Testes**:
  - Testes unitários do `ConfigManager` (carga, salvamento, fallback).
  - Testes unitários do `LLMService` com estilos de prompt variados.
  - Testes da `SettingsWindow` (abertura, atualização de campos, fechamento sem leak de memória).
  - Teste de disparo de Quick Questions verificando chamada a `respond_now`.
