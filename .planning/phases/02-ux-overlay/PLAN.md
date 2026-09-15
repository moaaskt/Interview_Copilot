# Plano de Execução - Fase 2: Refinamento de UX do Overlay & Auto-scroll Inteligente

## 🎯 Objetivo
Aprimorar a experiência visual e conforto de leitura durante entrevistas ao vivo, implementando auto-scroll adaptativo (não sequestra o scroll do usuário), controle dinâmico de opacidade (ciclo de transparência) e presets de posicionamento rápido da janela HUD (com ênfase no contato visual com a webcam).

---

## 📝 Tarefas

### Tarefa 1: Implementar Auto-scroll Adaptativo
- **Arquivo**: [`src/ui.py`](file:///home/moa-dev/projetos/helpIA/src/ui.py)
- **Ações**:
  1. No método `append_ai_token(self, token: str)`, verificar a posição atual do scroll via `yview()` do widget interno de texto.
  2. Apenas invocar `see("end")` se a visualização já estiver no final (`bottom_fraction >= 0.98`).
  3. No método `clear_ai_response(self)`, redefinir o estado para garantir que novas respostas sempre comecem com auto-scroll ativo.

### Tarefa 2: Adicionar Controle Rápido de Opacidade
- **Arquivo**: [`src/ui.py`](file:///home/moa-dev/projetos/helpIA/src/ui.py)
- **Ações**:
  1. Adicionar lista de níveis de opacidade: `[0.92, 1.0, 0.75, 0.85]`.
  2. Criar método `cycle_opacity(self, event=None)` que aplica `self.attributes("-alpha", ...)` e atualiza o rótulo do botão.
  3. Adicionar botão compacto no `header_frame` exibindo o percentual atual (ex: `👓 92%`).
  4. Vincular tecla de atalho global `<F10>` para ciclar opacidade.

### Tarefa 3: Presets de Ancoragem Rápida da Janela
- **Arquivo**: [`src/ui.py`](file:///home/moa-dev/projetos/helpIA/src/ui.py)
- **Ações**:
  1. Implementar método `cycle_window_position(self, event=None)` que calcula dimensões da tela (`winfo_screenwidth()`, `winfo_screenheight()`) e posiciona a janela nos seguintes presets:
     - **Topo-Centro** (alinhado à webcam: `y=20`, `x=(sw-w)//2`)
     - **Topo-Direito**: `y=20`, `x=sw-w-20`
     - **Topo-Esquerdo**: `y=20`, `x=20`
     - **Centro**: `y=(sh-h)//2`, `x=(sw-w)//2`
  2. Adicionar botão `🎯` no `header_frame` e vincular atalho `<F8>`.

### Tarefa 4: Suíte de Testes Automatizados & Verificação
- **Arquivo**: [`tests/test_ui_ux_overlay.py`](file:///home/moa-dev/projetos/helpIA/tests/test_ui_ux_overlay.py)
- **Ações**:
  1. Testar ciclo de opacidade (valores válidos aplicados).
  2. Testar lógica de auto-scroll (seguindo tokens quando no fundo, pausando quando no topo).
  3. Testar ciclo de posicionamento da janela (geometria calculada corretamente).
  4. Executar bateria com `python -m unittest tests/test_ui_ux_overlay.py`.

---

## 🔍 Critérios de Aceitação / Verificação
- [x] Auto-scroll rola automaticamente para tokens novos apenas se o usuário estiver no fim da caixa.
- [x] O botão de opacidade no cabeçalho exibe a porcentagem e clica/atrito com `<F10>` altera o canal alfa.
- [x] O botão de ancoragem `🎯` e atalho `<F8>` reposicionam a janela dinamicamente nos 4 presets de tela.
- [x] Bateria de testes unitários aprovada com 100% de sucesso.
