# ⚡ Interview Copilot

Assistente inteligente em tempo real para entrevistas técnicas. O **Interview Copilot** captura o áudio do sistema (loopback/monitor de saída do PulseAudio/PipeWire no Linux), realiza transcrição de fala contínua de altíssima precisão via WebSocket da **Deepgram** e gera respostas instantâneas em streaming através da API de ultra-alta velocidade da **Groq (`llama3-8b-8192`)**, exibindo tudo em uma interface overlay flutuante semi-transparente desenvolvida em **CustomTkinter**.

---

## 🚀 Funcionalidades

- **Captura de Áudio Interno (Loopback)**: Escuta diretamente a saída de áudio do sistema (reuniões no Google Meet, Zoom, Teams, Discord, etc.) sem necessidade de microfone externo apontado para caixas de som.
- **Transcrição Live & Baixa Latência**: Integração via WebSocket com modelo Deepgram `nova-2` com suporte a resultados parciais e finalizações de sentença em tempo real.
- **Respostas de IA em Streaming**: Respostas geradas token a token com `llama3-8b-8192` (Groq), otimizadas para leitura rápida (máximo 3 a 4 frases, método STAR e foco prático).
- **Overlay Flutuante & Transparente**: Janela moderna e arrastável que permanece no topo das outras aplicações sem roubar o foco, com opacidade configurável.
- **Arquitetura Assíncrona Não-Bloqueante**: Integração suave entre `asyncio` e o loop de eventos do `CustomTkinter` via thread-safe callbacks.

---

## 🛠️ Stack Tecnológica

| Componente | Tecnologia | Finalidade |
| :--- | :--- | :--- |
| **Linguagem** | Python 3.10+ | Núcleo da aplicação |
| **Áudio** | PyAudio (PortAudio) | Captura de stream PCM 16kHz mono (PulseAudio / PipeWire) |
| **STT (Speech-to-Text)** | Deepgram SDK (`nova-2`) | Transcrição de áudio em tempo real via WebSocket |
| **LLM** | Groq API (`llama3-8b-8192`) | Geração de respostas técnicas contextuais em ultra-alta velocidade |
| **Interface Gráfica** | CustomTkinter | Overlay HUD flutuante, arrastável e semi-transparente |
| **Concorrência** | Asyncio + Threading | Comunicação sem travamentos entre áudio, IA e interface |

---

## 📂 Estrutura do Projeto

```plaintext
helpIA/
├── .env.example          # Modelo das variáveis de ambiente
├── .gitignore            # Regras de exclusão do Git (ignora .env, venv, pycache, etc.)
├── README.md             # Documentação completa do projeto
├── requirements.txt      # Dependências Python do projeto
└── src/
    ├── audio_capture.py  # Captura e detecção de loopback/monitor do sistema
    ├── llm_service.py    # Integração com OpenAI e System Prompt especializado
    ├── main.py           # Orquestrador assíncrono e inicialização
    ├── transcriber.py    # Transcrição em tempo real via Deepgram WebSocket
    └── ui.py             # Interface overlay flutuante CustomTkinter
```

---

## ⚙️ Pré-requisitos e Instalação

### 1. Dependências de Sistema (Linux - Pop!_OS / Ubuntu / Debian)

O PyAudio necessita dos headers de desenvolvimento do PortAudio e bibliotecas do Tkinter instaladas no sistema operacional:

```bash
sudo apt update
sudo apt install -y python3-pyaudio portaudio19-dev python3-tk
```

### 2. Clonar o Repositório e Configurar o Ambiente Virtual

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/helpIA.git
cd helpIA

# Crie e ative o ambiente virtual
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar as Dependências Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🔑 Configuração das Chaves de API (`.env`)

Copie o arquivo de exemplo e crie o seu arquivo `.env`:

```bash
cp .env.example .env
```

Edite o arquivo `.env` inserindo suas chaves de API:

```env
DEEPGRAM_API_KEY=sua_chave_deepgram_aqui
OPENAI_API_KEY=sua_chave_openai_aqui
```

> ⚠️ **Atenção:** O arquivo `.env` contém credenciais privadas e já está configurado no `.gitignore` para nunca ser enviado ao repositório.

---

## ▶️ Como Executar

Com o ambiente virtual ativado e as chaves configuradas:

```bash
python3 src/main.py
```

### Dicas de Uso durante a Entrevista:
1. **Posicionamento**: Arraste a barra superior `⚡ Interview Copilot` para perto da sua câmera ou janela de videoconferência para manter o contato visual.
2. **Transcrição em Tempo Real**: Conforme o entrevistador fala, a transcrição é atualizada em tempo real (indicada por `🎙`).
3. **Geração de Resposta**: Ao final de uma pergunta ou sentença completa (`✔`), o assistente dispara a chamada para a OpenAI e a resposta aparece em streaming token a token.
4. **Fechamento**: Use o botão de fechar no overlay ou encerre com `Ctrl + C` no terminal.

---

## 🛡️ Licença

Este projeto é para uso pessoal e educacional.
