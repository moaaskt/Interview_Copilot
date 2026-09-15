# Roadmap do Projeto

## Fase 1: Atalhos de Teclado & Usabilidade Rápida
- **Objetivo**: Permitir controle total da gravação e resposta sem desviar a atenção ou perder foco da janela de entrevista.
- **Entregas**:
  - Atalhos no CustomTkinter / Tk bindings para Gravar/Parar (`<Control-space>` ou `<F9>`), Responder Agora (`<Control-Return>`) e Limpar (`<Control-BackSpace>`).
  - Dicas visuais (tooltips/legendas nos botões com os atalhos correspondentes).
- **Status**: Concluída.

## Fase 2: Refinamento de UX do Overlay & Auto-scroll Inteligente
- **Objetivo**: Tornar a leitura durante a entrevista ultra-confortável, fluida e discreta.
- **Entregas**:
  - Auto-scroll adaptativo nos widgets de texto para tokens da Groq.
  - Controle de opacidade dinâmico (slider sutil ou clique de ciclo 80% -> 90% -> 100%).
  - Presets de ancoragem de janela (ex: centro superior próximo à câmera).
- **Status**: Não iniciada.

## Fase 3: Feedback Visual de Áudio & Resiliência
- **Objetivo**: Garantir segurança total ao usuário de que o áudio está sendo captado antes de falar.
- **Entregas**:
  - Mini VU-meter ou indicador de pulso luminoso baseado no RMS do sinal de áudio.
  - Indicador de estado de conexão WebSocket Deepgram com tentativa de reconexão transparente.
- **Status**: Não iniciada.
