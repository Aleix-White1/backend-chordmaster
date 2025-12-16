import os
import uuid
import subprocess
from fastapi import HTTPException
import librosa
import numpy as np
import json
import jwt
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.schemas import AnalyzeLinkRequest, AnalyzeResponse
from app.config import JWT_SECRET_KEY
from app.database import get_db, SongHistory
from fastapi.responses import FileResponse, Response
from scipy.ndimage import median_filter, gaussian_filter1d
from scipy.signal import correlate, medfilt
from music21 import key as m21key, chord as m21chord, roman, pitch as m21pitch, stream
from collections import Counter

# --- Constantes ---
TITLE_NOT_FOUND = "Título no encontrado"
AUDIO_FILENAME = "audio.wav"
AUDIO_WEBM = "audio.webm"


def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado. Por favor, inicia sesión de nuevo.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido. No autorizado.")


router = APIRouter()

# --- Constantes para análisis avanzado ---
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Perfiles Krumhansl para detección de tonalidad
KRUMHANSL_MAJOR = np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88])
KRUMHANSL_MINOR = np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17])

# ---------------------------
# 1. Detectar tonalidad usando perfiles Krumhansl
# ---------------------------
def detect_key_krumhansl(chroma):
    """Detecta la tonalidad usando perfiles Krumhansl-Schmuckler"""
    mean_chroma = chroma.mean(axis=1)
    mean_chroma = mean_chroma / (mean_chroma.sum() + 1e-8)
    
    major_scores = []
    minor_scores = []
    for i in range(12):
        major_scores.append(np.dot(np.roll(KRUMHANSL_MAJOR, i), mean_chroma))
        minor_scores.append(np.dot(np.roll(KRUMHANSL_MINOR, i), mean_chroma))
    
    maj_best = int(np.argmax(major_scores))
    min_best = int(np.argmax(minor_scores))
    
    if major_scores[maj_best] >= minor_scores[min_best]:
        return NOTE_NAMES[maj_best], 'major', major_scores[maj_best]
    else:
        return NOTE_NAMES[min_best], 'minor', minor_scores[min_best]


# -------------------------
# Estimación del número de beats por compás
# -------------------------
def estimate_beats_per_bar(y, sr, beats_frames):
    """Estima el número de beats por compás usando autocorrelación"""
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    beat_strengths = []
    for i in range(len(beats_frames)-1):
        s = beats_frames[i]
        e = beats_frames[i+1]
        beat_strengths.append(onset_env[s:e].mean() if e>s else onset_env[s])
    
    beat_strengths = np.array(beat_strengths)
    
    if len(beat_strengths) < 6:
        return 4
    
    ac = correlate(beat_strengths - beat_strengths.mean(), 
                   beat_strengths - beat_strengths.mean(), mode='full')
    mid = len(ac)//2
    ac_segment = ac[mid+1: mid+1+16]
    
    candidates = ac_segment[2:8] if len(ac_segment) >= 8 else ac_segment
    if len(candidates) == 0:
        return 4
    
    best = int(np.argmax(candidates)) + 3
    return best


# -------------------------
# Plantillas de acordes
# -------------------------
def build_chord_templates():
    """Construye plantillas de acordes básicos para detección más robusta."""
    intervals_map = {
        "": [(0, 1.0), (4, 0.95), (7, 0.9)],              # Mayor
        "m": [(0, 1.0), (3, 0.95), (7, 0.9)],             # Menor
        "7": [(0, 1.0), (4, 0.85), (7, 0.8), (10, 0.7)],      # Dominante 7
        "m7": [(0, 1.0), (3, 0.85), (7, 0.8), (10, 0.7)],     # Menor 7
        "maj7": [(0, 1.0), (4, 0.85), (7, 0.8), (11, 0.7)],   # Mayor 7
    }
    
    templates = {}
    for r_idx, root in enumerate(NOTE_NAMES):
        for suf, intervals in intervals_map.items():
            vec = np.zeros(12)
            for semitone, weight in intervals:
                vec[(r_idx + semitone) % 12] = weight
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            label = root + suf
            templates[label] = vec
    
    return templates


# -------------------------
# Detectar nota de bajo dominante en un segmento
# -------------------------
def detect_bass_in_segment(y_segment, sr):
    """Detecta la nota de bajo dominante en un segmento de audio"""
    if len(y_segment) < 1024:
        return None
    
    n_fft = min(4096, len(y_segment))
    chroma = librosa.feature.chroma_cqt(y=y_segment, sr=sr, n_chroma=12, n_octaves=2)
    if chroma.size == 0:
        return None
    bass_profile = chroma.mean(axis=1)
    return int(np.argmax(bass_profile))


# -------------------------
# Detectar acorde en un segmento usando plantillas
# -------------------------
def detect_chord_in_segment(chroma_segment, templates, bass_hint=None):
    """Detecta el acorde que mejor coincide con el segmento de chroma"""
    if chroma_segment.size == 0:
        return "N.C.", 0.0
    
    mean_chroma = chroma_segment.mean(axis=1)
    norm = np.linalg.norm(mean_chroma)
    if norm < 1e-6:
        return "N.C.", 0.0
    mean_chroma = mean_chroma / norm
    
    best_chord = "N.C."
    best_score = -1.0
    
    for chord_name, template in templates.items():
        score = np.dot(mean_chroma, template)
        
        if bass_hint is not None:
            root_idx = NOTE_NAMES.index(chord_name.replace('m7','').replace('maj7','').replace('m','').replace('7',''))
            if root_idx == bass_hint:
                score *= 1.15
        
        if score > best_score:
            best_score = score
            best_chord = chord_name
    
    return best_chord, best_score


# -------------------------
# Análisis principal de audio
# -------------------------
def analyze_audio_advanced(audio_path: str):
    """Análisis avanzado de audio con detección de acordes por compás"""
    y, sr = librosa.load(audio_path, sr=22050)
    
    # Tempo y beats
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    if isinstance(tempo, np.ndarray):
        tempo = float(tempo[0])
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    
    # Tonalidad
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    key_root, key_mode, key_confidence = detect_key_krumhansl(chroma)
    
    # Estimar beats por compás
    beats_per_bar = estimate_beats_per_bar(y, sr, beat_frames)
    if beats_per_bar not in [3, 4]:
        beats_per_bar = 4
    
    # Construir plantillas
    templates = build_chord_templates()
    
    # Detectar acordes por compás
    chords_result = []
    num_beats = len(beat_times)
    
    bar_idx = 0
    i = 0
    while i < num_beats:
        bar_start_beat = i
        bar_end_beat = min(i + beats_per_bar, num_beats)
        
        start_time = beat_times[bar_start_beat]
        end_time = beat_times[bar_end_beat - 1] if bar_end_beat > bar_start_beat else start_time
        
        if bar_end_beat < num_beats:
            end_time = beat_times[bar_end_beat]
        else:
            end_time = librosa.get_duration(y=y, sr=sr)
        
        start_frame = librosa.time_to_frames(start_time, sr=sr)
        end_frame = librosa.time_to_frames(end_time, sr=sr)
        
        if end_frame > start_frame and end_frame <= chroma.shape[1]:
            chroma_segment = chroma[:, start_frame:end_frame]
            
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            y_segment = y[start_sample:end_sample]
            bass_hint = detect_bass_in_segment(y_segment, sr)
            
            chord, score = detect_chord_in_segment(chroma_segment, templates, bass_hint)
        else:
            chord = "N.C."
        
        chords_result.append({
            "start_time": round(start_time, 2),
            "end_time": round(end_time, 2),
            "chord": chord,
            "bar": bar_idx + 1
        })
        
        bar_idx += 1
        i += beats_per_bar
    
    # Agregar prevChord y nextChord
    for idx, c in enumerate(chords_result):
        c["prevChord"] = chords_result[idx - 1]["chord"] if idx > 0 else None
        c["nextChord"] = chords_result[idx + 1]["chord"] if idx < len(chords_result) - 1 else None
    
    return {
        "tempo_bpm": round(tempo, 1),
        "key": key_root,
        "mode": key_mode,
        "beats_per_bar": beats_per_bar,
        "chords": chords_result
    }


# ----------------------------
# FUNCIÓN: Descargar audio con yt-dlp
# ----------------------------
def download_audio(youtube_url: str, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, AUDIO_WEBM)

    # Comando actualizado para compatibilidad con restricciones de YouTube (dic 2025)
    cmd = [
        "yt-dlp",
        "--no-check-certificate",
        "--no-playlist",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "--extractor-args", "youtube:player_client=web",
        "-f", "bestaudio/best",
        "--extract-audio",
        "--audio-format", "best",
        "-o", output_path,
        youtube_url,
    ]

    try:
        result = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=180
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=408,
            detail="Tiempo de descarga excedido. El video es demasiado largo o la conexión es lenta."
        )

    # Si falla, intentar configuración alternativa
    if result.returncode != 0:
        cmd_fallback = [
            "yt-dlp",
            "--no-check-certificate",
            "--no-playlist",
            "-f", "bestaudio/best",
            "--extract-audio",
            "-o", output_path,
            youtube_url,
        ]
        
        try:
            result = subprocess.run(
                cmd_fallback,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=180
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(
                status_code=408,
                detail="Tiempo de descarga excedido."
            )
        
        if result.returncode != 0:
            stderr = result.stderr.decode()
            raise HTTPException(
                status_code=400,
                detail=f"No se pudo descargar el audio. El vídeo puede tener copyright o protección.\nDetalles: {stderr}"
            )

    # Buscar archivo descargado
    possible_extensions = ['.webm', '.m4a', '.mp3', '.opus', '.ogg', '.wav']
    actual_path = None
    
    if os.path.exists(output_path):
        actual_path = output_path
    else:
        base_path = os.path.join(output_dir, "audio")
        for ext in possible_extensions:
            candidate = base_path + ext
            if os.path.exists(candidate):
                actual_path = candidate
                break
    
    if not actual_path:
        for f in os.listdir(output_dir):
            if any(f.endswith(ext) for ext in possible_extensions):
                actual_path = os.path.join(output_dir, f)
                break
    
    if not actual_path:
        raise HTTPException(
            status_code=400,
            detail="YouTube no proporcionó ningún archivo de audio sin protección."
        )

    if os.path.getsize(actual_path) < 8000:
        raise HTTPException(
            status_code=400,
            detail="Audio inválido o vacío. El vídeo no permite descarga legal."
        )

    return actual_path


# ----------------------------
# FUNCIÓN: Convertir a WAV (FFmpeg)
# ----------------------------
def convert_to_wav(input_path: str, output_path: str):
    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-ac", "1",
        "-ar", "22050",
        output_path,
        "-y"
    ]

    try:
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error convirtiendo a WAV: {e.stderr.decode()}"
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="FFmpeg no está instalado. Por favor instala FFmpeg para convertir archivos de audio."
        )


# ----------------------------
# FUNCIÓN: Obtener título de YouTube
# ----------------------------
def get_youtube_title(youtube_url: str) -> str:
    """Extrae el título de un video de YouTube usando yt-dlp"""
    try:
        result = subprocess.run(
            ["yt-dlp", "--get-title", "--no-playlist", youtube_url],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return TITLE_NOT_FOUND
    except Exception:
        return TITLE_NOT_FOUND


# ----------------------------
# ENDPOINT /link y /analyze/link
# ----------------------------
@router.post("/link", response_model=AnalyzeResponse)
@router.post("/analyze/link", response_model=AnalyzeResponse)
async def analyze_link(
    req: AnalyzeLinkRequest,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_db)
):
    # Verificar token
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido: user_id no encontrado")
    
    try:
        job_id = str(uuid.uuid4())
        job_dir = os.path.join("jobs", job_id)
        os.makedirs(job_dir, exist_ok=True)

        # Obtener título
        title = get_youtube_title(req.youtube_url)

        # Descargar audio
        audio_path = download_audio(req.youtube_url, job_dir)

        # Convertir a WAV
        wav_path = os.path.join(job_dir, AUDIO_FILENAME)
        convert_to_wav(audio_path, wav_path)

        # Analizar
        result = analyze_audio_advanced(wav_path)
        
        # Leer archivo WAV para almacenarlo en BD
        with open(wav_path, 'rb') as audio_file:
            audio_data = audio_file.read()

        # Guardar en historial
        song_entry = SongHistory(
            job_id=job_id,
            user_id=user_id,
            title=title,
            source="youtube",
            youtube_url=req.youtube_url,
            tempo_bpm=result["tempo_bpm"],  # Float, no convertir a int
            key_detected=result["key"],
            mode_detected=result["mode"],
            chords_json=json.dumps(result["chords"]),
            audio_data=audio_data
        )
        db.add(song_entry)
        db.commit()

        return {
            "job_id": job_id,
            "analysis": result,
            "title": title
        } 
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando enlace: {str(e)}")


# ----------------------------
# ENDPOINT /file y /analyze/file
# ----------------------------
@router.post("/file", response_model=AnalyzeResponse)
@router.post("/analyze/file", response_model=AnalyzeResponse)
async def analyze_file(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_db)
):
    # Verificar token
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido: user_id no encontrado")
    
    try:
        job_id = str(uuid.uuid4())
        job_dir = os.path.join("jobs", job_id)
        os.makedirs(job_dir, exist_ok=True)

        # Guardar archivo subido
        upload_path = os.path.join(job_dir, f"upload_{file.filename}")
        content = await file.read()
        
        with open(upload_path, "wb") as f:
            f.write(content)

        # Convertir a WAV
        wav_path = os.path.join(job_dir, AUDIO_FILENAME)
        convert_to_wav(upload_path, wav_path)

        # Analizar
        result = analyze_audio_advanced(wav_path)
        
        # Leer archivo WAV para almacenarlo en BD
        with open(wav_path, 'rb') as audio_file:
            audio_data = audio_file.read()

        # Obtener título del archivo
        title = file.filename or "Archivo subido"
        
        # Guardar en historial
        song_entry = SongHistory(
            job_id=job_id,
            user_id=user_id,
            title=title,
            source="file",
            youtube_url=None,
            tempo_bpm=result["tempo_bpm"],
            key_detected=result["key"],
            mode_detected=result["mode"],
            chords_json=json.dumps(result["chords"]),
            audio_data=audio_data
        )
        db.add(song_entry)
        db.commit()

        return {
            "job_id": job_id,
            "analysis": result,
            "title": title
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")


# ----------------------------
# ENDPOINT /history - Historial de canciones
# ----------------------------
@router.get("/history")
async def get_history(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_db)
):
    # Verificar token
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido: user_id no encontrado")
    
    songs = db.query(SongHistory).filter(SongHistory.user_id == user_id).order_by(SongHistory.analyzed_at.desc()).all()
    
    return [
        {
            "id": song.id,
            "job_id": song.job_id,
            "title": song.title,
            "youtube_url": song.youtube_url,
            "tempo_bpm": song.tempo_bpm,
            "key": song.key_detected,
            "mode": song.mode_detected,
            "analyzed_at": song.analyzed_at.isoformat() if song.analyzed_at else None,
            "chords": song.chords_json if song.chords_json else []
        }
        for song in songs
    ]


# ----------------------------
# ENDPOINT /history/{song_id} - Detalle de canción
# ----------------------------
@router.get("/history/{song_id}")
async def get_song_detail(
    song_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido: user_id no encontrado")
    
    song = db.query(SongHistory).filter(
        SongHistory.id == song_id,
        SongHistory.user_id == user_id
    ).first()
    
    if not song:
        raise HTTPException(status_code=404, detail="Canción no encontrada")
    
    return {
        "id": song.id,
        "title": song.title,
        "youtube_url": song.youtube_url,
        "tempo_bpm": song.tempo_bpm,
        "key": song.key_detected,
        "mode": song.mode_detected,
        "analyzed_at": song.analyzed_at.isoformat() if song.analyzed_at else None,
        "chords": json.loads(song.chords_json) if song.chords_json else []
    }


# ----------------------------
# ENDPOINT DELETE /history/{song_id} - Eliminar canción del historial
# ----------------------------
@router.delete("/history/{song_id}")
async def delete_song(
    song_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido: user_id no encontrado")
    
    song = db.query(SongHistory).filter(
        SongHistory.id == song_id,
        SongHistory.user_id == user_id
    ).first()
    
    if not song:
        raise HTTPException(status_code=404, detail="Canción no encontrada")
    
    db.delete(song)
    db.commit()
    
    return {"message": "Canción eliminada del historial"}


# --- Endpoint para servir el audio analizado por job_id ---
@router.get("/audio/{job_id}")
async def get_analyzed_audio(
    job_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
):
    """Devuelve el archivo WAV analizado para el job_id dado"""
    print(f"🎵 Solicitando audio para job_id: {job_id}")
    
    # Verificar autenticación JWT
    if not credentials:
        print(f"❌ Sin token de autenticación para job_id: {job_id}")
        raise HTTPException(status_code=401, detail="Token de autenticación requerido")
    
    token = credentials.credentials
    try:
        payload = verify_token(token)
        user_id = payload.get("user_id")
        print(f"✅ Usuario autenticado: {user_id} para job_id: {job_id}")
    except Exception as e:
        print(f"❌ Error verificando token: {e}")
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido: user_id no encontrado")
    
    # Verificar que el usuario tiene acceso a este job_id
    song = db.query(SongHistory).filter(
        SongHistory.job_id == job_id,
        SongHistory.user_id == user_id
    ).first()
    
    if not song:
        print(f"❌ No hay acceso al job_id {job_id} para usuario {user_id}")
        raise HTTPException(status_code=403, detail="No tienes acceso a este audio o el análisis no existe")
    
    print(f"✅ Acceso confirmado para job_id: {job_id}, título: {song.title}")
    
    # Verificar que el audio existe en la base de datos
    if not song.audio_data:
        print(f"❌ No hay datos de audio almacenados para job_id: {job_id}")
        raise HTTPException(status_code=404, detail=f"Archivo de audio no encontrado para el análisis: {job_id}")
    
    print(f"✅ Sirviendo audio desde BD para job_id: {job_id}, tamaño: {len(song.audio_data)} bytes")
    
    # Devolver el audio como respuesta binaria
    return Response(
        content=song.audio_data,
        media_type="audio/wav",
        headers={"Content-Disposition": f"inline; filename=\"{job_id}.wav\""}
    )
