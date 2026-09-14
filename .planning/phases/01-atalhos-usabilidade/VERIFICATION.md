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
