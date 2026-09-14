# Plano de Execução - Fase 1: Atalhos de Teclado & Usabilidade Rápida

## 🎯 Objetivo
Implementar controle por teclas de atalho no overlay HUD (`CopilotUI`) para acionamento instantâneo da gravação, resposta da IA e limpeza de tela, acompanhado de dicas visuais nos botões.

## 📝 Tarefas

### Tarefa 1: Implementar Bindings de Teclado no `CopilotUI`
- **Arquivo**: [`src/ui.py`](file:///home/moa-dev/projetos/helpIA/src/ui.py)
- **Ações**:
  1. No método `_setup_ui()` de `CopilotUI`, vincular eventos de teclado via `bind_all`:
     - `<Control-space>` e `<F9>` -> chama `_handle_toggle_recording()`
     - `<Control-Return>` -> chama `_handle_respond_now()`
     - `<Escape>` e `<Control-BackSpace>` -> chama `_handle_clear()`
  2. Garantir que os eventos do Tkinter consumam/retornem `"break"` para evitar comportamento indesejado em caixas de texto.

### Tarefa 2: Atualizar Legendas e Rótulos dos Botões
- **Arquivo**: [`src/ui.py`](file:///home/moa-dev/projetos/helpIA/src/ui.py)
- **Ações**:
  1. Atualizar textos dos botões no `controls_frame`:
     - `record_btn`: `"🎙 Gravar [Ctrl+Espaço]"` / `"⏹ Parar [Ctrl+Espaço]"`
     - `respond_btn`: `"⚡ Responder [Ctrl+Enter]"`
     - `clear_btn`: `"🗑 Limpar [Esc]"`

### Tarefa 3: Verificação & Teste de Integração
- Executar `python3 src/main.py` e testar os atalhos de teclado diretamente na janela HUD.
- Verificar se o acionamento via teclado ativa a transcrição Deepgram e dispara o streaming Groq perfeitamente.

## 🔍 Critérios de Aceitação / Verificação
- [ ] Pressionar `Ctrl+Space` altera o estado do botão de gravação para ativo (`⏹ Parar [Ctrl+Espaço]`) e inicia captura.
- [ ] Pressionar `Ctrl+Return` finaliza a gravação e dispara a chamada LLM Groq.
- [ ] Pressionar `Esc` limpa o conteúdo de transcrição e IA da tela.
- [ ] Os botões exibem claramente os atalhos entre colchetes.
