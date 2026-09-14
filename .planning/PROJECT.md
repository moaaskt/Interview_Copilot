# Interview Copilot (`helpIA`)

## Visão Geral
O **Interview Copilot** é um assistente inteligente em tempo real para entrevistas técnicas. Ele captura o áudio interno do sistema (reuniões no Google Meet, Zoom, Teams, etc.), realiza transcrição de fala contínua de altíssima precisão via WebSocket da **Deepgram** e gera respostas instantâneas em streaming via API da **Groq** (`qwen/qwen3.8-27b`), exibindo tudo em uma interface overlay flutuante semi-transparente desenvolvida em **CustomTkinter**.

## Perfil Padrão do Candidato
- **Candidato**: Moacir Neto, Desenvolvedor Full Stack Júnior.
- **Formação & Vivência**: SENAI/SC, Doar Digital / Evento Santo (produção PHP CodeIgniter 4, MySQL, Docker, integrações Asaas/WhatsApp), VetOS AI, Rastrecob, WhatsMiau.
- **Diretriz de Resposta**: 3 a 4 frases concisas, método STAR, foco prático e sem alucinações de métricas.

## Metas do Projeto
1. **Excelência em Usabilidade & Overlay UX**:
   - Atalhos de teclado (globais/locais) para iniciar/parar gravação (`🎙`), disparar resposta (`⚡`) e limpar (`🗑`) sem tirar o foco da janela de entrevista.
   - Melhorias visuais e ergonômicas no overlay HUD: controle rápido de opacidade, fixação/posicionamento rápido na tela (canto superior, próximo à webcam).
   - Auto-scroll inteligente e tipografia ultra-legível com alta taxa de contraste para leitura dinâmica sem distrações.
2. **Robustez de Transcrição & Feedback**:
   - Indicadores visuais de volume de áudio em tempo real (VU meter / nível RMS discreto).
   - Estabilidade na reconexão do WebSocket com Deepgram em longas pausas.
3. **Qualidade & Manutenibilidade**:
   - Código modular, desacoplado e documentado.
