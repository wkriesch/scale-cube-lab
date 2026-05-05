import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import redis

app = FastAPI(title="Service B - Session (NoSQL)")

# Configuração do Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

# Conexão Global
r = redis.Redis(host=REDIS_HOST, port=int(REDIS_PORT), decode_responses=True)

class SessionData(BaseModel):
    key: str
    value: str

@app.get("/healthz")
def health_check():
    try:
        r.ping()
        return {"status": "ok", "service": "session-nosql"}
    except redis.ConnectionError:
        raise HTTPException(status_code=503, detail="Redis unavailable")

@app.post("/session")
def set_session(data: SessionData, x_tenant_id: Optional[str] = Header(None)):
    # Eixo Z: Poderíamos usar o tenant_id para prefixar a chave no futuro (ex: tenantA:session123)
    try:
        r.set(data.key, data.value, ex=3600) # Expira em 1 hora
        return {"status": "stored", "key": data.key, "shard_info": x_tenant_id}
    except redis.RedisError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{key}")
def get_session(key: str):
    try:
        val = r.get(key)
        if not val:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"key": key, "value": val}
    except redis.RedisError as e:
        raise HTTPException(status_code=500, detail=str(e))