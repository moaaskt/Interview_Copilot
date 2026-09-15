# Plano de Verificação - Fase 1

## Testes Manuais de Usabilidade
1. **Atalhos de Gravação**:
   - Abrir a aplicação via `python3 src/main.py`.
   - Garantir que a janela esteja focada.
   - Pressionar `Ctrl + Space` ou `F9`. Verificar log `🎙 Gravação iniciada` e alteração visual do botão para `⏹ Parar [Ctrl+Espaço]`.
2. **Atalho de Resposta**:
   - Falar uma pergunta para transcrever via Deepgram.
   - Pressionar `Ctrl + Enter`. Verificar log `Disparando resposta para...` e início do streaming no `ai_textbox`.
3. **Atalho de Limpeza**:
   - Pressionar `Escape`. Verificar se a transcrição e a resposta da IA são limpas da tela.

## Resultados da Verificação
- **Testes Automatizados (`tests/test_ui_shortcuts.py`)**: 6 testes executados e aprovados com 100% de sucesso.
  - `test_handler_toggle_recording_returns_break` ✅
  - `test_handler_respond_now_returns_break` ✅
  - `test_handler_clear_returns_break` ✅
  - `test_button_labels_contain_shortcuts` ✅
  - `test_recording_state_toggles_button_text` ✅
  - `test_global_bindings_registered` ✅
- **Status da Fase**: Concluída e Validada.
