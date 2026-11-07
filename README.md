# ⚡ Interview Copilot (`helpIA`)

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Plataforma-Windows%2011%20%7C%20Linux-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Deepgram](https://img.shields.io/badge/STT-Deepgram%20Nova--2-13EF93?style=for-the-badge)
![Groq](https://img.shields.io/badge/LLM-Groq%20%2B%20Gemini%20Fallback-F55036?style=for-the-badge)
![UI](https://img.shields.io/badge/UI-CustomTkinter%20HUD-89B4FA?style=for-the-badge)

Assistente inteligente em tempo real. O **Interview Copilot (`helpIA`)** captura diretamente o áudio interno do sistema (saída de som de chamadas no Google Meet, Zoom, Teams, Discord, etc.), transcreve a fala com baixíssima latência via **Deepgram WebSocket (`nova-2`)** e gera respostas estruturadas em streaming através da **Groq Cloud** (com fallback automático e preventivo para o **Google Gemini**), exibindo tudo em uma interface **HUD Overlay** flutuante, furtiva e sempre no topo.

---

## 🌟 Principais Funcionalidades

### 🎧 Captura de Áudio Multiplataforma & Resiliente
- **Loopback Interno Nativo**: Escuta diretamente a saída de áudio do sistema (sem depender de microfone externo captando caixas de som).
  - **Windows**: Usa `PyAudioWPatch` com **WASAPI Loopback**, **Keep-Alive Silencioso** (mantém drivers e headsets USB/wireless acordados em momentos de silêncio) e detecção inteligente multi-dispositivo (alterna sozinho caso o navegador toque em outra saída de som).
  - **Linux**: Usa `sounddevice` integrado ao **PipeWire / PulseAudio**, detectando automaticamente o sink em estado `RUNNING` via `pactl`.
- **Buffer Circular de Pré-Roll (5 segundos)**: Retém continuamente os últimos segundos de áudio em memória. Quando você clica em **Gravar**, o áudio imediatamente anterior é injetado na transcrição para que o início da pergunta do recrutador nunca seja cortado.

### 🗣️ Transcrição em Tempo Real & Vocabulário Técnico
- **Deepgram `nova-2` via WebSocket**: Resultados parciais (*interim*) e finais instantâneos com formatação inteligente (`smart_format`) e reconexão automática com *exponential backoff*.
- **Boost de Vocabulário Técnico (Keyterm Boosting)**: Dicionário pré-configurado e personalizável com pesos para tecnologias (`PHP`, `CodeIgniter 4`, `React`, `Next.js`, `Node.js`, `Docker`, `PostgreSQL`, `Redis`, `AWS`, `STAR`, etc.), evitando erros de grafia em termos de engenharia de software.

### 🧠 Inteligência Artificial Dual-Engine & Gestão de TPM
- **Respostas em Streaming Ultra-Rápido**: Integração primária com a **Groq Cloud** (`qwen/qwen3.8-27b`, `llama-3.3-70b-versatile`, `llama3-8b-8192`).
- **Rastreador de Tokens (TPM) & Fallback Proativo para Gemini**:
  - Barra de progresso em tempo real no HUD mostrando o consumo de Tokens Por Minuto (TPM) na janela deslizante de 60 segundos.
  - Se o uso atingir **90% da cota** ou ocorrer erro de *rate limit* (`HTTP 413` / `429`), o sistema desvia automaticamente e sem interrupções para a API do **Google Gemini** (`gemini-flash-lite-latest`).
- **3 Estilos de Resposta & Persona Customizável**:
  - `⚡ Direta`: 3 a 4 frases objetivas, naturais e fáceis de ler rapidamente.
  - `🔬 Técnica`: 5 a 7 frases aprofundadas (arquitetura, *trade-offs*, banco de dados, concorrência).
  - `⭐ Método STAR`: Estruturada rigorosamente em **S**ituação, **T**arefa, **A**ção e **R**esultado.

### 🎯 Detecção Inteligente de Perguntas (Smart Question Detector)
- Motor determinístico que analisa a transcrição em tempo real (pontuação interrogativa, aberturas interrogativas em PT/EN e padrões clássicos de recrutadores como *"Me fale sobre..."*, *"Explique como..."*, *"Qual foi um desafio..."*).
- Destaca visualmente no HUD quando uma pergunta é detectada e suporta **Auto-Trigger após silêncio** (opcional).

### 🖥️ Interface HUD Overlay Furtiva & Ergonômica
- **Stealth & Opacidade Dinâmica (`F10`)**: 4 perfis de transparência (`92%`, `100%`, `75%`, `85%`) com alto contraste para leitura confortável.
- **Presets de Ancoragem Rápida (`F8`)**: Posicione a janela instantaneamente no `Topo-Centro` (abaixo da webcam para manter contato visual), `Topo-Direita`, `Topo-Esquerda` ou `Centro`.
- **Arrasto 1:1 e Redimensionamento Livre**: Arraste pelo cabeçalho sem *lag* e redimensione livremente pelo canto inferior direito (`⇲`).
- **Atalhos Globais em Background (`pynput`)**: Controle gravação, geração de resposta e limpeza de sessão mesmo quando o foco estiver no navegador (Google Meet / Zoom) ou na IDE.
- **Barra de Perguntas Rápidas (*Quick Prompts*)**: Botões de 1 clique para perguntas clássicas de entrevista (*Sobre Mim*, *Arquitetura*, *Bugs*, *Bancos*, *Desafio*), totalmente editáveis.

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologia | Papel no Sistema |
| :--- | :--- | :--- |
| **Linguagem** | Python 3.10+ | Núcleo da aplicação e concorrência `asyncio` + `threading` |
| **Áudio (Windows)** | `PyAudioWPatch` (WASAPI) | Captura loopback nativa + stream keep-alive + auto-switch |
| **Áudio (Linux)** | `sounddevice` + `pactl` | Captura via monitor de saída do PipeWire / PulseAudio |
| **Processamento DSP** | `NumPy` | Cálculo de volume RMS (VU-Meter), downmix mono e reamostragem 16kHz |
| **Speech-to-Text** | `deepgram-sdk` (`nova-2`) | Transcrição contínua via WebSocket com vocabulário técnico |
| **LLM Primário** | `openai` (SDK p/ Groq API) | Streaming de respostas em baixa latência |
| **LLM Fallback** | `google-generativeai` (Gemini) | Contingência proativa/reativa contra limites de TPM |
| **Interface Gráfica** | `CustomTkinter` + `Tkinter` | HUD Overlay flutuante e janela modal de configurações |
| **Atalhos Globais** | `pynput` | Captura de teclas em nível de sistema operacional |

---

## 📂 Estrutura do Projeto

```plaintext
helpIA/
├── .env.example              # Modelo das variáveis de ambiente e chaves de API
├── helpia_config.json        # Configurações persistidas do usuário (gerado automaticamente)
├── requirements.txt          # Dependências Python multiplataforma (Windows e Linux)
├── README.md                 # Documentação completa do projeto
├── src/
│   ├── main.py               # Orquestrador principal (CopilotApp) e loop asyncio + UI
│   ├── audio_capture.py      # Captura de áudio multiplataforma (WASAPI / PulseAudio)
│   ├── audio_buffer.py       # Buffer circular thread-safe de Pré-Roll (PreRollAudioBuffer)
│   ├── transcriber.py        # Cliente WebSocket Deepgram com reconexão e keywords
│   ├── llm_service.py        # Integração Groq + Gemini Fallback, estilos e TokenTracker
│   ├── question_detector.py  # Motor heurístico de identificação de perguntas (PT/EN)
│   ├── ui.py                 # Interface HUD Overlay principal (CopilotUI)
│   ├── settings_window.py    # Painel modal de configurações com 4 abas (SettingsWindow)
│   ├── config_manager.py     # Gerenciador de estado e persistência (helpia_config.json)
│   ├── hotkey_manager.py     # Listener global de atalhos de teclado via pynput
│   └── diagnostic.py         # Ferramenta CLI de diagnóstico de áudio e Deepgram (Linux/Geral)
└── tests/                    # Suíte de testes automatizados (pytest / unittest)
```

---

## ⚙️ Pré-requisitos e Instalação

### 1. Preparação do Sistema Operacional

#### 🪟 No Windows (Windows 10 / 11)
Não é necessária nenhuma instalação de driver externo (como VB-Cable). O projeto instala automaticamente o `PyAudioWPatch`, que acessa o **WASAPI Loopback** nativo do Windows.
- Certifique-se apenas de ter o **Python 3.10+** instalado (com a opção *"Add Python to PATH"* e suporte a *tcl/tk* marcados no instalador).

#### 🐧 No Linux (Ubuntu / Pop!_OS / Debian / Mint)
Instale os cabeçalhos do PortAudio, suporte ao Tkinter e utilitários do PulseAudio/PipeWire:
```bash
sudo apt update
sudo apt install -y python3-pyaudio portaudio19-dev python3-tk pulseaudio-utils libportaudio2
```

---

### 2. Clonar o Repositório e Criar o Ambiente Virtual

```bash
git clone https://github.com/seu-usuario/helpIA.git
cd helpIA
```

**No Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**No Linux (Bash/Zsh):**
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Instalar as Dependências Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```
> 💡 *O arquivo `requirements.txt` possui marcadores de plataforma (`sys_platform`) e instalará automaticamente o `pyaudiowpatch` no Windows e o `pyaudio` no Linux.*

---

## 🔐 Configuração de Variáveis de Ambiente (`.env`)

Crie um arquivo `.env` na raiz do projeto copiando o modelo `.env.example`:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**Linux:**
```bash
cp .env.example .env
```

Abra o arquivo `.env` e preencha suas credenciais. Abaixo estão **todas as variáveis suportadas** (obrigatórias e opcionais):

```env
# ====================================================================
# 1. CHAVES OBRIGATÓRIAS
# ====================================================================
# Chave da Deepgram para transcrição de voz em tempo real (Speech-to-Text)
# Obtenha em: https://console.deepgram.com/
DEEPGRAM_API_KEY=sua_chave_deepgram_aqui

# Chave da Groq Cloud para geração de respostas ultra-rápidas (LLM Primário)
# Obtenha em: https://console.groq.com/keys
GROQ_API_KEY=sua_chave_groq_aqui

# ====================================================================
# 2. CHAVES E PARÂMETROS OPCIONAIS (ALTAMENTE RECOMENDADOS)
# ====================================================================
# Chave do Google Gemini para Fallback Automático quando o limite de TPM da Groq atingir 90%
# Obtenha em: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=sua_chave_gemini_aqui

# Modelo da Groq a ser utilizado (Padrão: qwen/qwen3.8-27b)
# Outras opções: llama-3.3-70b-versatile, llama3-8b-8192, mixtral-8x7b-32768
GROQ_MODEL=qwen/qwen3.8-27b

# Limite customizado de Tokens Por Minuto (TPM) da sua conta Groq (Padrão: 7000 para Qwen)
GROQ_TPM_LIMIT=7000

# Modelo do Gemini utilizado no fallback (Padrão: gemini-flash-lite-latest)
GEMINI_MODEL=gemini-flash-lite-latest

# [Apenas Linux] Forçar manualmente um monitor do PulseAudio/PipeWire caso deseje
# Exemplo: PULSE_SOURCE=alsa_output.pci-0000_00_1f.3.analog-stereo.monitor
# PULSE_SOURCE=
```

---

## ▶️ Como Executar e Usar

Com o ambiente virtual ativo e o `.env` configurado, inicie o aplicativo:

```bash
python src/main.py
```

### 🎮 Fluxo de Uso durante uma Entrevista

1. **Posicione o HUD**:
   - Pressione **`F8`** (ou clique no ícone `🎯` no topo da janela) para ancorar o overlay no **Topo-Centro** da tela, logo abaixo da sua webcam. Assim, você lê os tópicos mantendo contato visual natural com o entrevistador.
   - Ajuste a transparência com **`F10`** (ou botão `👓 92%`) e redimensione puxando o canto inferior direito (`⇲`) se desejar mais espaço.

2. **Verifique o Áudio (Mini VU-Meter)**:
   - No cabeçalho do HUD há um indicador **`🎙 ···`**. Quando o entrevistador falar, as barras devem oscilar (`🎙 ▃▅█`), confirmando que o áudio interno está sendo captado.

3. **Grave a Pergunta (`Ctrl + Espaço` ou `F9`)**:
   - Assim que o entrevistador começar a fazer uma pergunta (ou mesmo até **5 segundos depois** que ele começou, graças ao **Pré-Roll**!), pressione **`Ctrl + Espaço`** (ou clique em `🎙 Gravar`).
   - A fala aparecerá em tempo real na caixa **Pergunta Transcrita**.
   - Se o detector identificar uma pergunta, o rótulo mudará para **`🎯 Pergunta Detectada!`** em dourado.

4. **Gere a Resposta (`Ctrl + Enter`)**:
   - Pressione **`Ctrl + Enter`** (ou clique em `⚡ Responder`).
   - A gravação é encerrada automaticamente e a IA escreve a resposta em streaming na caixa **Sugestão da IA** em questão de milissegundos.
   - *Dica*: Você também pode digitar ou editar o texto diretamente na caixa de transcrição antes de apertar `Ctrl + Enter`, ou clicar em qualquer botão da barra **`⚡ Rápidas:`** para disparar respostas prontas instantaneamente.

5. **Limpe para a Próxima Rodada (`Esc` ou `Ctrl + Backspace`)**:
   - Pressione **`Esc`** (ou clique em `🗑 Limpar`) para zerar a tela e o buffer para a próxima pergunta.

---

## ⌨️ Tabela de Atalhos Globais de Teclado

Todos os atalhos abaixo funcionam **globalmente** (mesmo com o navegador ou outra janela em foco) e podem ser remapeados na interface gráfica:

| Ação | Atalho Principal | Atalho Alternativo | Botão no HUD |
| :--- | :---: | :---: | :---: |
| **Iniciar / Parar Gravação** | `Ctrl + Espaço` | `F9` | `🎙 Gravar` / `⏹ Parar` |
| **Responder Agora (Disparar IA)** | `Ctrl + Enter` | — | `⚡ Responder` |
| **Limpar Sessão / Resetar** | `Esc` | `Ctrl + Backspace` | `🗑 Limpar` |
| **Alternar Posição na Tela (Presets)** | `F8` | — | `🎯` |
| **Alternar Opacidade (Stealth Mode)** | `F10` | — | `👓 92%` |
| **Abrir Painel de Configurações** | `F12` | — | `⚙` |

---

## 🛠️ Painel de Configurações (`F12` ou `⚙`) & `helpia_config.json`

Ao pressionar **`F12`** ou clicar na engrenagem **`⚙`** no canto superior direito do HUD, você abre o **Painel de Configurações** dividido em 4 abas. Todas as alterações são salvas imediatamente no arquivo `helpia_config.json` na raiz do projeto:

### 1. Aba `🎙 Áudio`
- **Placa de Som / Dispositivo de Entrada**: Escolha entre `Padrão do Sistema` (recomendado, pois monitora automaticamente todos os loopbacks ativos no Windows) ou fixe um dispositivo de saída específico (`[Loopback] Alto-falantes / Headphones`).
- **Medidor de Nível em Tempo Real (VU-Meter)**: Barra gráfica ao vivo para testar se o som da chamada está chegando com bom volume antes da entrevista começar.
- **`🎙 Usar pré-roll ao iniciar gravação`**: Ativa/desativa o envio dos 5 segundos anteriores ao clique em Gravar.
- **`🎯 Detecção automática de perguntas`**: Ativa/desativa o destaque visual de perguntas identificadas na transcrição.

### 2. Aba `🧠 IA & Persona`
- **Estilo de Resposta da IA**: Alterne com 1 clique entre `⚡ Direta (3-4 frases)`, `🔬 Técnica (Aprofundada)` e `⭐ Método STAR`.
- **Contexto & Perfil do Candidato (System Prompt)**: Edite livremente o seu currículo, stack principal, experiências profissionais e projetos para que a IA responda sempre em primeira pessoa (`"Eu atuei..."`, `"Na minha experiência..."`) com os seus dados reais. Possui botão `↺ Restaurar Padrão`.

### 3. Aba `⌨ Atalhos`
- Clique em qualquer campo e pressione a combinação de teclas desejada no teclado para redefinir os atalhos globais instantaneamente.

### 4. Aba `⚡ Perguntas Rápidas`
- Configure os botões de acesso rápido que ficam no HUD principal, informando **uma pergunta por linha** no formato:
  ```text
  Nome do Botão | Pergunta completa que será enviada para a IA
  ```
- Exemplo:
  ```text
  Sobre Mim | Fale mais sobre você e sua trajetória profissional
  Arquitetura | Explique a arquitetura de um projeto recente que você desenvolveu
  ```

---

### ⚙️ Ajustes Avançados no `helpia_config.json`

Além do que está visível no painel gráfico, você pode editar diretamente o arquivo `helpia_config.json` para ajustes finos de engenharia:

```json
{
  "audio": {
    "device_index": null,
    "device_name": "Padrão do Sistema",
    "pre_roll_seconds": 5.0,
    "pre_roll_enabled": true
  },
  "transcription": {
    "language": "pt-BR",
    "endpointing_ms": 350,
    "custom_keywords": [
      "NestJS:3",
      "Supabase:2",
      "Kubernetes:2"
    ]
  },
  "llm": {
    "response_style": "direta",
    "custom_persona": null,
    "model": "qwen/qwen3.8-27b"
  },
  "question_detection": {
    "enabled": true,
    "auto_trigger_on_silence": false,
    "silence_delay_ms": 1200
  }
}
```

- **`audio.pre_roll_seconds`**: Altera a janela de tempo (em segundos) do buffer circular de pré-gravação (padrão: `5.0`).
- **`transcription.language`**: Idioma da entrevista no Deepgram (ex: `"pt-BR"`, `"en-US"`, `"es"`).
- **`transcription.endpointing_ms`**: Tempo de pausa em milissegundos para o Deepgram considerar uma frase como finalizada (padrão: `350`).
- **`transcription.custom_keywords`**: Lista de termos técnicos adicionais com peso de reforço (`"Termo:Peso"`) mesclados ao dicionário padrão.
- **`question_detection.auto_trigger_on_silence`**: Se alterado para `true`, o `helpIA` **não espera você apertar `Ctrl + Enter`** — assim que uma pergunta é detectada na fala final e ocorre um silêncio de `silence_delay_ms` (padrão `1200` ms), ele para a gravação e dispara a resposta da IA sozinho!

---

## 🔍 Diagnóstico e Solução de Problemas (Troubleshooting)

### 1. Script de Diagnóstico de Áudio e Deepgram
Caso a transcrição não esteja aparecendo, execute o utilitário de diagnóstico embutido (com algum vídeo ou áudio tocando no computador):
```bash
python src/diagnostic.py
```
Ele realizará 3 testes automatizados:
1. **Captura de Áudio (5s)**: Verifica quantos chunks de áudio foram recebidos e mede o volume médio em `dBFS`.
2. **Conexão WebSocket Deepgram**: Envia o áudio capturado e valida o retorno da transcrição.
3. **Streaming Live (10s)**: Testa o pipeline em tempo real de ponta a ponta.

### 2. Problemas Comuns
- **O VU-Meter (`🎙 ···`) não se mexe quando há som tocando**:
  - Abra as Configurações (`F12`), vá na aba **🎙 Áudio**, clique em **🔄 Atualizar Dispositivos**, selecione explicitamente o dispositivo `[Loopback]` correspondente ao seu fone de ouvido/caixa de som atual e clique em **💾 Salvar Dispositivo**.
  - No Linux, verifique no terminal qual sink está ativo com `pactl list short sinks` enquanto um áudio toca.
- **Aviso `⚠ Trocando para Gemini (limite TPM)...`**:
  - Comportamento normal de proteção! Significa que você realizou muitas requisições seguidas na Groq e atingiu 90% da cota de tokens por minuto. O aplicativo continuará respondendo normalmente usando o Gemini até a janela de 60 segundos da Groq esvaziar (acompanhe pela barra `⚡ TPM` no HUD).

---

## 🧪 Executando os Testes Automatizados

O projeto conta com uma suíte completa de testes unitários e de integração cobrindo buffer circular de pré-roll, resiliência de áudio, detector de perguntas, vocabulário do Deepgram e atalhos da interface:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 🛡️ Licença

Este projeto é destinado a uso pessoal, estudo de arquitetura assíncrona em tempo real e preparação para entrevistas técnicas.
