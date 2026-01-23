"""
API FastAPI unificada (USFQ + SRI)
"""
import os
import secrets
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Literal
from dotenv import load_dotenv

# Importar extractores
from token_extractor import obtener_tokens as obtener_tokens_usfq
from sri_extractor import obtener_tokens_sri

# Cargar variables de entorno
load_dotenv()

app = FastAPI(
    title="Universal Token Extractor API",
    description="API para extraer tokens de USFQ y SRI",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# Seguridad
# ==========================================

async def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    expected_key = os.getenv("API_KEY", "")
    if not expected_key:
        raise HTTPException(status_code=500, detail="API_KEY no configurada en servidor")
    
    if not x_api_key or not secrets.compare_digest(x_api_key, expected_key):
        raise HTTPException(status_code=403, detail="API Key inválida")
    return True

# ==========================================
# Modelos
# ==========================================

class TokenRequest(BaseModel):
    type: Literal["usfq", "sri"]
    
    # Credenciales (User puede ser email o RUC)
    user: Optional[str] = None
    email: Optional[str] = None # Alias para user (USFQ)
    ruc: Optional[str] = None   # Alias para user (SRI)
    
    password: str

class TokenResponse(BaseModel):
    success: bool
    
    # USFQ Outputs
    d2lSessionVal: Optional[str] = None
    d2lSecureSessionVal: Optional[str] = None
    csrfToken: Optional[str] = None
    
    # SRI Outputs
    cookie_header: Optional[str] = None
    view_state: Optional[str] = None
    
    error: Optional[str] = None

# ==========================================
# Endpoints
# ==========================================

@app.get("/")
async def root():
    return {"status": "running", "service": "Universal Token Extractor", "version": "2.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/obtener-tokens", response_model=TokenResponse)
async def api_obtener_tokens(req: TokenRequest, _: bool = Depends(verify_api_key)):
    """
    Endpoint unificado para obtención de tokens.
    """
    # 1. Normalizar usuario (user / email / ruc)
    username = req.user or req.email or req.ruc
    if not username:
        raise HTTPException(status_code=400, detail="Se requiere user, email o ruc")

    try:
        # 2. Rutear según tipo
        if req.type == "usfq":
            result = await obtener_tokens_usfq(username, req.password)
            return TokenResponse(**result)
            
        elif req.type == "sri":
            result = await obtener_tokens_sri(username, req.password)
            return TokenResponse(**result)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
