# Pesquisa Técnica - Fase 2: Refinamento de UX do Overlay & Auto-scroll Inteligente

## 1. Contexto & Desafios de UX em Entrevistas
Durante uma entrevista ao vivo, o usuário não pode parecer estar lendo uma tela lateral ou lutando contra a interface. Três fricções críticas foram identificadas:
1. **Perda de Posição de Leitura**: Quando a resposta da IA é longa e o auto-scroll puxa a tela para baixo enquanto o candidato lê as primeiras frases.
2. **Visibilidade do HUD**: Telas com fundos claros ou múltiplos monitores exigem ajuste rápido de opacidade para não ofuscar nem ficar invisível.
3. **Contato Visual com a Câmera**: Manter o HUD colado ao topo central, logo abaixo da lente da webcam, cria a ilusão natural de contato visual direto com os entrevistadores.

---

## 2. Soluções Técnicas & Decisões de Implementação

### 2.1. Auto-scroll Adaptativo
- **Widget**: `ctk.CTkTextbox` envolve um `tkinter.Text` acessível via `self.ai_textbox._textbox`.
- **Mecanismo de Detecção**:
  - `yview()` retorna uma tupla `(top_fraction, bottom_fraction)`.
  - Se `bottom_fraction >= 0.98`, o cursor está no fim da visualização -> executa `see("end")`.
  - Se `bottom_fraction < 0.98`, o usuário rolou para cima manualmente -> não força o scroll, preservando o ponto de leitura do usuário.
  - Ao iniciar nova resposta (`clear_ai_response`), o estado é resetado para ativo.

### 2.2. Controle Rápido de Opacidade
- **API Tkinter**: `self.attributes("-alpha", alpha)`
- **Valores Pré-definidos**: Ciclo entre `[0.92, 1.00, 0.75, 0.85]`.
  - `92%`: Equilibrado e discreto (padrão atual).
  - `100%`: Máxima legibilidade em fundos complexos.
  - `75%`: Modo "fantasma" discreto.
  - `85%`: Modo sutil.
- **Controle na UI**: Botão compacto no cabeçalho (ex: `👓 92%` ou `👁 92%`) e atalho `<F10>` para ciclar instantaneamente.

### 2.3. Presets de Ancoragem (Posicionamento Rápido)
- **Cálculo de Coordenadas**:
  - `sw = self.winfo_screenwidth()`
  - `sh = self.winfo_screenheight()`
  - `w = 520`, `h = 390`
- **Presets**:
  - `topo-centro` (Webcam): `x = (sw - w) // 2`, `y = 20`
  - `topo-direito`: `x = sw - w - 20`, `y = 20`
  - `topo-esquerdo`: `x = 20`, `y = 20`
  - `centro`: `x = (sw - w) // 2`, `y = (sh - h) // 2`
- **Controle na UI**: Botão de ancoragem `🎯` no cabeçalho e atalho `<F8>` para ciclar os presets.

---

## 3. Riscos & Mitigações
- **Risco**: Falha em `_textbox.yview()` se o widget estiver vazio.
  - *Mitigação*: Testar se há linhas de texto ou verificar com `try/except` seguro, padrão de fallback para `see("end")`.
- **Risco**: Mudança de resolução dinâmica ou multi-monitor.
  - *Mitigação*: Sempre calcular com base em `winfo_screenwidth()` no momento da invocação.
