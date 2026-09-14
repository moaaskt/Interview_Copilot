import asyncio
import logging
import math
import os
import sys
import time
from pathlib import Path
from typing import List

import numpy as np
from dotenv import load_dotenv

# Configuração de logging no console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("Diagnostic")

# Carrega chaves do .env na raiz
project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")

try:
    import sounddevice as sd
except ImportError:
    logger.error("Biblioteca 'sounddevice' não encontrada. Instale com: pip install sounddevice")
    sys.exit(1)

try:
    from deepgram import (
        DeepgramClient,
        DeepgramClientOptions,
        LiveTranscriptionEvents,
        LiveOptions,
    )
except ImportError:
    logger.error("Biblioteca 'deepgram-sdk' não encontrada. Instale com: pip install deepgram-sdk")
    sys.exit(1)


def calculate_rms_db(pcm_data: bytes) -> float:
    """Calcula o volume médio em dBFS a partir de bytes int16."""
    if not pcm_data:
        return -96.0
    audio_array = np.frombuffer(pcm_data, dtype=np.int16).astype(np.float32)
    if len(audio_array) == 0:
        return -96.0
    rms = np.sqrt(np.mean(audio_array ** 2))
    if rms <= 0:
        return -96.0
    db = 20 * math.log10(rms / 32767.0)
    return round(db, 2)


def get_pulse_device_index() -> int:
    """Busca o índice do dispositivo pulse / pipewire no sounddevice."""
    devices = sd.query_devices()
    for preferred in ("pulse", "pipewire", "default"):
        for idx, dev in enumerate(devices):
            if preferred in dev.get("name", "").lower() and dev.get("max_input_channels", 0) > 0:
                return idx
    return sd.default.device[0]


async def run_diagnostics():
    print("\n" + "=" * 65)
    print(" 🛠️  DIAGNÓSTICO DO PIPELINE DE ÁUDIO - INTERVIEW COPILOT")
    print("=" * 65)

    pulse_source = os.environ.get("PULSE_SOURCE", "NÃO DEFINIDO")
    api_key = os.getenv("DEEPGRAM_API_KEY")

    print(f"• PULSE_SOURCE atual : {pulse_source}")
    print(f"• DEEPGRAM_API_KEY    : {'DEFINIDA (' + api_key[:6] + '...)' if api_key else 'NÃO ENCONTRADA'}")
    device_idx = get_pulse_device_index()
    device_info = sd.query_devices(device_idx)
    print(f"• Dispositivo Entrada : [{device_idx}] {device_info['name']}")
    print("-" * 65)

    if not api_key:
        print("\n❌ FALHA: DEEPGRAM_API_KEY não foi encontrada no arquivo .env!")
        return

    # =========================================================================
    # TESTE 1: CAPTURA DE ÁUDIO (5 SEGUNDOS)
    # =========================================================================
    print("\n[TESTE 1/3] 🎙️  Iniciando Captura de Áudio (5 segundos)...")
    print("💡 IMPORTANTE: Certifique-se de que há áudio/vídeo tocando agora!")

    captured_chunks: List[bytes] = []
    chunk_size = int(16000 * 0.1)  # 100ms chunks

    def audio_callback(indata, frames, time_info, status):
        if indata is not None:
            captured_chunks.append(bytes(indata))

    try:
        stream = sd.InputStream(
            device=device_idx,
            samplerate=16000,
            channels=1,
            dtype="int16",
            blocksize=chunk_size,
            callback=audio_callback,
        )
        with stream:
            for sec in range(5, 0, -1):
                print(f"  Gravando... {sec}s restantes (chunks recebidos até agora: {len(captured_chunks)})", end="\r")
                await asyncio.sleep(1.0)
            print()
    except Exception as e:
        print(f"\n❌ ERRO ao abrir captura de áudio com sounddevice: {e}")
        return

    num_chunks = len(captured_chunks)
    all_bytes = b"".join(captured_chunks)
    avg_db = calculate_rms_db(all_bytes)

    print(f"✓ Captura de áudio concluída: {num_chunks} chunks recebidos.")
    print(f"✓ Volume médio RMS: {avg_db} dBFS")

    teste1_pass = num_chunks > 30 and avg_db > -60.0
    if avg_db <= -60.0:
        print("⚠️  ALERTA: Volume detectado está próximo do silêncio absoluto (-96 dB a -60 dB).")
        print("    O sounddevice pode estar conectado a um canal mudo ou sem áudio passando.")
    elif teste1_pass:
        print("✅ TESTE 1 APROVADO: Chunks de áudio capturados com volume ativo.")

    # =========================================================================
    # TESTE 2: CONEXÃO E ENVIO PARA DEEPGRAM (5-10 SEGUNDOS)
    # =========================================================================
    print("\n[TESTE 2/3] 📡 Testando Conexão e Transcrição WebSocket com a Deepgram...")
    
    deepgram_messages = []
    deepgram_errors = []

    try:
        config = DeepgramClientOptions(options={"keepalive": "true"})
        client = DeepgramClient(api_key, config)
        connection = client.listen.live.v("1")

        def on_message(self_conn, result, **kwargs):
            sentence = result.channel.alternatives[0].transcript
            if sentence.strip():
                is_final = result.is_final
                deepgram_messages.append((is_final, sentence))
                tag = "FINAL" if is_final else "INTERIM"
                print(f"  [Deepgram {tag}]: {sentence}")

        def on_error(self_conn, error, **kwargs):
            deepgram_errors.append(str(error))
            logger.error(f"Erro Deepgram: {error}")

        connection.on(LiveTranscriptionEvents.Transcript, on_message)
        connection.on(LiveTranscriptionEvents.Error, on_error)

        options = LiveOptions(
            model="nova-2",
            language="pt-BR",
            smart_format=True,
            interim_results=True,
            encoding="linear16",
            channels=1,
            sample_rate=16000,
        )

        if not connection.start(options):
            print("❌ Falha ao iniciar WebSocket com a Deepgram.")
            return

        print("✓ Conexão WebSocket estabelecida! Enviando áudio pré-gravado do Teste 1...")
        for chunk in captured_chunks:
            connection.send(chunk)
            await asyncio.sleep(0.08)

        # Espera 3 segundos para receber respostas remanescentes
        await asyncio.sleep(3.0)
        connection.finish()

    except Exception as e:
        print(f"❌ Exceção no Teste da Deepgram: {e}")

    print(f"✓ Total de mensagens transcritas recebidas: {len(deepgram_messages)}")
    teste2_pass = len(deepgram_messages) > 0
    if teste2_pass:
        print("✅ TESTE 2 APROVADO: A Deepgram respondeu com transcrições.")
    else:
        print("❌ TESTE 2 FALHOU: Nenhuma transcrição recebida da Deepgram.")

    # =========================================================================
    # TESTE 3: FLUXO COMPLETO EM TEMPO REAL (10 SEGUNDOS)
    # =========================================================================
    print("\n[TESTE 3/3] ⚡ Testando Fluxo Completo em Tempo Real (10 segundos)...")
    live_transcripts = []

    try:
        config = DeepgramClientOptions(options={"keepalive": "true"})
        live_client = DeepgramClient(api_key, config)
        live_conn = live_client.listen.live.v("1")

        def on_live_message(self_conn, result, **kwargs):
            text = result.channel.alternatives[0].transcript
            if text.strip():
                live_transcripts.append(text)
                marker = "✔" if result.is_final else "🎙"
                print(f"  {marker} {text}")

        live_conn.on(LiveTranscriptionEvents.Transcript, on_live_message)
        live_conn.start(options)

        def live_audio_callback(indata, frames, time_info, status):
            if indata is not None:
                live_conn.send(bytes(indata))

        live_stream = sd.InputStream(
            device=device_idx,
            samplerate=16000,
            channels=1,
            dtype="int16",
            blocksize=chunk_size,
            callback=live_audio_callback,
        )

        start_time = time.time()
        with live_stream:
            while time.time() - start_time < 10.0:
                await asyncio.sleep(0.5)

        live_conn.finish()
    except Exception as e:
        print(f"❌ Erro no Teste 3: {e}")

    teste3_pass = len(live_transcripts) > 0
    print(f"✓ Transcrições em tempo real capturadas: {len(live_transcripts)}")

    # =========================================================================
    # RELATÓRIO FINAL
    # =========================================================================
    print("\n" + "=" * 65)
    print(" 📊 RELATÓRIO FINAL DE DIAGNÓSTICO")
    print("=" * 65)
    print(f"1. Captura de Áudio (sounddevice/pulse) : {'✅ PASS' if teste1_pass else '❌ FAIL'}")
    print(f"   • Chunks: {num_chunks} | Volume Médio: {avg_db} dBFS")
    print(f"2. Conexão e API Deepgram             : {'✅ PASS' if teste2_pass else '❌ FAIL'}")
    print(f"   • Mensagens de transcrição recebidas: {len(deepgram_messages)}")
    print(f"3. Fluxo Completo em Tempo Real       : {'✅ PASS' if teste3_pass else '❌ FAIL'}")
    print(f"   • Transcrições em live: {len(live_transcripts)}")
    print("-" * 65)

    if not teste1_pass:
        if avg_db <= -60.0:
            print("🚨 DIAGNÓSTICO: O áudio capturado é SILÊNCIO.")
            print("👉 Causa provável: O PULSE_SOURCE especificado não está emitindo o áudio da reprodução atual.")
            print("   Execute no terminal: `pactl list short sinks` enquanto o som toca para verificar qual sink está ativo.")
        else:
            print("🚨 DIAGNÓSTICO: O sounddevice não conseguiu capturar dados suficientes.")
    elif not teste2_pass:
        print("🚨 DIAGNÓSTICO: A captura funciona, mas a Deepgram não gerou texto.")
        print("👉 Causa provável: Formato de áudio incompatível ou fala inaudível no canal capturado.")
    elif not teste3_pass:
        print("🚨 DIAGNÓSTICO: O fluxo em lote funciona, mas o streaming live em tempo real engasgou.")
    else:
        print("🎉 DIAGNÓSTICO: O pipeline completo (Áudio -> Deepgram -> Transcrição) está 100% OPERACIONAL!")
        print("👉 Se a UI principal não exibia, o problema está na passagem de callbacks para o loop do CustomTkinter.")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    asyncio.run(run_diagnostics())
