from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserRegisterResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    access_token: str
    refresh_token: str
    token_type: str
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    name: str
    token_type: str

class TokenRefresh(BaseModel):
    refresh_token: str

class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str

class AnalyzeLinkRequest(BaseModel):
    youtube_url: str
    
class AnalyzeFileRequest(BaseModel):
    file: bytes

class ChordsResponse(BaseModel):
    prevChord: str | None
    nextChord: str | None
    start_time: float
    end_time: float
    chord: str
    
class AnalyzeResponse(BaseModel):
    job_id: str
    analysis: dict = {
        "tempo_bpm": float,
        "key": str,
        "chords": list[ChordsResponse]
    }
    _lyrics: str | None = None