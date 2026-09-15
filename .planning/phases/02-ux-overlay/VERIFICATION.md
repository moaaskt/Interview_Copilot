# Plano de Verificação - Fase 2: Refinamento de UX do Overlay & Auto-scroll Inteligente

## Cenários de Teste

### 1. Auto-scroll Inteligente
- **Cenário A (Acompanhamento Normal)**:
  - Disparar geração de texto longo com vários tokens via `append_ai_token`.
  - O widget deve acompanhar e rolar até o fim automaticamente.
- **Cenário B (Leitura Manual / Scroll Pausado)**:
  - Rolar manualmente a barra de rolagem do `ai_textbox` para cima.
  - Continuar inserindo tokens via `append_ai_token`.
  - A visualização não deve descer involuntariamente para o fim, mantendo a leitura pausada.

### 2. Ciclo de Opacidade
- Clicar no botão de opacidade no cabeçalho ou pressionar `F10`.
- O valor deve alternar sequencialmente: `92% -> 100% -> 75% -> 85% -> 92%`.
- A janela deve atualizar sua transparência visual imediatamente.

### 3. Presets de Ancoragem
- Clicar no botão `🎯` ou pressionar `F8`.
- A janela deve alternar para:
  1. Topo-Centro (imediatamente abaixo da câmera, facilitando contato visual)
  2. Topo-Direito
  3. Topo-Esquerdo
  4. Centro da Tela

### 4. Testes Automatizados
- Executar: `./venv/bin/python -m unittest tests/test_ui_ux_overlay.py`
- Todos os testes devem passar com código de saída 0.
