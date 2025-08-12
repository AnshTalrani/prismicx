from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from src.services.stt_service_whisper import WhisperSTTService
from src.services.tts_service_kokoro import KokoroTTSService
import io

router = APIRouter()

# Whisper STT endpoint
@router.post("/stt/whisper", summary="Transcribe audio using Whisper")
async def transcribe_audio(file: UploadFile = File(...)):
    if file.content_type not in ["audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3"]:
        raise HTTPException(status_code=400, detail="Invalid audio file type.")
    audio_bytes = await file.read()
    stt_service = WhisperSTTService()
    text = await stt_service.transcribe(audio_bytes)
    return {"text": text}

# Kokoro TTS endpoint
@router.post("/tts/kokoro", summary="Synthesize speech using Kokoro")
async def synthesize_speech(text: str):
    tts_service = KokoroTTSService()
    audio_bytes = await tts_service.synthesize(text)
    return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/wav")
