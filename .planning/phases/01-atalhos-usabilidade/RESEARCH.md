# Pesquisa Técnica: Atalhos de Teclado no CustomTkinter / Tkinter

## Contexto & Desafios
O `CopilotUI` é uma janela HUD flutuante com `overrideredirect(True)`. 
Para vincular atalhos de teclado no Tkinter/CustomTkinter:
1. **Tk Bindings**: `bind_all("<Control-space>", ...)` ou `bind("<Control-Return>", ...)` na instância raiz do `CopilotUI` (que herda de `ctk.CTk`).
2. **Foco e Atalhos Globais vs Locais**:
   - `bind_all` do Tkinter captura combinações de teclas quando a janela do Copilot possui o foco da aplicação.
   - Em reuniões de entrevista (Google Meet no navegador), o usuário pode clicar no navegador para usar o chat ou vídeo, perdendo o foco estrito do Tkinter.
   - **Solução Combinada**: Implementar eventos nativos do Tkinter (`bind_all`) como padrão nativo leve e seguro, com tratamento inteligente para manter o foco ou aceitar combinações diretas sem travar.

## Mapeamento de Atalhos
- `Control+Space` ou `F9`: Alternar Gravação (`toggle_recording`).
- `Control+Return`: Disparar resposta imediata da IA (`respond_now`).
- `Control+BackSpace` ou `Escape`: Limpar sessão (`clear_session`).

## Legendas & Dicas Visuais na UI
- Atualizar os textos dos botões na barra de controles do `CopilotUI` para deixar explícitos os atalhos:
  - `🎙 Gravar [Ctrl+Espaço]`
  - `⚡ Responder [Ctrl+Enter]`
  - `🗑 Limpar [Esc]`
