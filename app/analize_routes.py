import os
import uuid
import subprocess
from fastapi import HTTPException
import librosa
import numpy as np
import json
from fastapi import APIRouter
from app.schemas import AnalyzeLinkRequest, AnalyzeResponse, AnalyzeFileRequest
from app.chords import ALL_CHORDS


router = APIRouter()

# ----------------------------
# MODELO DE REQUEST
# ----------------------------

# ----------------------------
# FUNCIÓN: Descargar audio con yt-dlp
# ----------------------------
def download_audio(youtube_url: str, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "audio.webm")

    cmd = [
        "yt-dlp",
        "--no-check-certificate",
        "--no-playlist",
        "--user-agent", "Mozilla/5.0",
        "-f", "bestaudio",
        "-o", output_path,
        youtube_url,
    ]

    try:
        result = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=408,
            detail="Tiempo de descarga excedido. YouTube no ofrece audio accesible sin protecciones."
        )

    # Si yt-dlp devolvió error
    if result.returncode != 0:
        stderr = result.stderr.decode()
        raise HTTPException(
            status_code=400,
            detail=(
                "No se pudo descargar el audio. El vídeo puede tener copyright o protección.\n"
                f"Detalles: {stderr}"
            )
        )

    # Validar archivo generado
    if not os.path.exists(output_path):
        raise HTTPException(
            status_code=400,
            detail="YouTube no proporcionó ningún archivo de audio sin protección."
        )

    # Validar tamaño > 0 (muy común cuando YT da un stream vacío)
    if os.path.getsize(output_path) < 8000:  # 8 KB mínimo
        raise HTTPException(
            status_code=400,
            detail="Audio inválido o vacío. El vídeo no permite descarga legal."
        )

    return output_path

# ----------------------------
# FUNCIÓN: Convertir a WAV (FFmpeg)
# ----------------------------
def convert_to_wav(input_path: str, output_path: str):
    cmd = [
        "ffmpeg",
        "-i",
        input_path,
        "-ac",
        "1",
        "-ar",
        "44100",
        output_path,
        "-y"
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error convirtiendo a WAV: {e.stderr.decode()}"
        )


# ----------------------------
# FUNCIÓN PRINCIPAL DE ANÁLISIS
# ----------------------------
def analyze_audio(audio_path: str):
    y, sr = librosa.load(audio_path, sr=44100)

    # --- TEMPO ---
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

    # --- TONALIDAD ---
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_mean = np.mean(chroma, axis=1)
    tonalidad = np.argmax(chroma_mean)
    
    print(chroma_mean)

    nota_strings = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    tonalidad_str = nota_strings[tonalidad]

    # --- ACORDES (simplificado usando chroma) ---
    chords = []
    hop_length = 2048
    frame_duration = hop_length / sr

    for i in range(chroma.shape[1]):
        chroma_frame = chroma[:, i]
        root = np.argmax(chroma_frame)
        chords.append({
            "time": round(i * frame_duration, 2),
            "chord": nota_strings[root]
        })

    return {
        "tempo_bpm": float(tempo),
        "key": tonalidad_str,
        "chords": chords
    }


# ----------------------------
# ENDPOINT /analyze/link
# ----------------------------
@router.post("/analyze/link", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeLinkRequest):
    job_id = str(uuid.uuid4())
    job_dir = os.path.join("jobs", job_id)
    os.makedirs(job_dir, exist_ok=True)

    # 1) Descargar audio
    audio_path = download_audio(req.youtube_url, job_dir)

    # 2) Convertir a WAV
    wav_path = os.path.join(job_dir, "audio.wav")
    convert_to_wav(audio_path, wav_path)

    # 3) Analizar audio
    result = analyze_audio(wav_path)

    # 4) Devolver JSON
    return {
        "job_id": job_id,
        "analysis": result
    }
    
# ----------------------------
# ENDPOINT /analyze/file
# ----------------------------
@router.post("/analyze/file", response_model=AnalyzeResponse)
async def analyze_file(req: AnalyzeFileRequest):
    job_id = str(uuid.uuid4())
    job_dir = os.path.join("jobs", job_id)
    os.makedirs(job_dir, exist_ok=True)

    # 1) Guardar archivo subido
    upload_path = os.path.join(job_dir, "upload.webm")
    with open(upload_path, "wb") as f:
        f.write(file)

    # 2) Convertir a WAV
    wav_path = os.path.join(job_dir, "audio.wav")
    convert_to_wav(upload_path, wav_path)

    # 3) Analizar audio
    result = analyze_audio(wav_path)

    # 4) Devolver JSON
    return {
        "job_id": job_id,
        "analysis": result
    }