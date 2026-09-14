# Requisitos do Projeto

## Requisitos Funcionais (RF)
- **RF01 - Atalhos de Teclado**: Suporte a atalhos de teclado configuráveis (ex: `Ctrl+Space` ou tecla dedicada) para alternar gravação (`toggle_recording`), disparar resposta imediata (`respond_now`) e limpar tela (`clear_session`).
- **RF02 - Auto-scroll Inteligente**: A área de resposta da IA e transcrição deve manter a rolagem suave acompanhando a emissão dos tokens em streaming, pausando se o usuário rolar manualmente para cima.
- **RF03 - Controle Rápido de Opacidade**: Permitir ao usuário ajustar a transparência da janela flutuante dinamicamente (ex: slider discreto ou atalho rápido entre 70% e 100%).
- **RF04 - Presets de Posicionamento**: Atalho ou botão discreto para posicionar o HUD rapidamente próximo à webcam (topo-central) ou cantos da tela.
- **RF05 - Indicador Visual de Entrada de Áudio**: Feedback visual sutil (nível de atividade de áudio) na barra superior do HUD para confirmar que o microfone/monitor está recebendo sinal.
- **RF06 - Persistência do Perfil Base**: Manter o System Prompt do candidato Moacir Neto calibrado com 3 a 4 frases, método STAR e foco em produção real.

## Requisitos Não Funcionais (RNF)
- **RNF01 - Latência de Interação**: A resposta a cliques e acionamento de atalhos deve ser imediata (< 50ms).
- **RNF02 - Consumo de Recursos**: O polling do CustomTkinter e cálculo de áudio não devem causar sobrecarga de CPU (> 5% em repouso).
- **RNF03 - Compatibilidade Linux/Wayland & Windows**: O overlay HUD deve manter comportamento estável em ambientes Linux (XWayland / Wayland) e Windows 10/11.
