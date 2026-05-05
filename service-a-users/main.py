import os
import asyncio
import httpx
from typing import Optional
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(
    title="Scale Cube - Service A (Sharding Engine)",
    description="Orquestrador com Sharding físico de Banco de Dados (Eixo Z)",
    version="2.0.0"
)

# Configurações de Sharding
SHARDS = {
    "default": {
        "host": os.getenv("DB_HOST", "postgres-db"),
        "user": os.getenv("DB_USER", "postgres"),
        "pass": os.getenv("DB_PASS", "password123"),
        "dbname": "users_db_default"
    },
    "premium": {
        "host": os.getenv("DB_HOST_SHARD2", "postgres-db-shard2"),
        "user": os.getenv("DB_USER", "postgres"),
        "pass": os.getenv("DB_PASS", "password123"),
        "dbname": "users_db_premium"
    }
}

SERVICE_B_URL = os.getenv("SERVICE_B_URL", "http://service-b:8000")
SERVICE_C_URL = os.getenv("SERVICE_C_URL", "http://service-c:8000")

client = httpx.AsyncClient(timeout=5.0)

def get_db_conn(tenant: str):
    config = SHARDS.get(tenant, SHARDS["default"])
    try:
        conn = psycopg2.connect(
            host=config["host"],
            database=config["dbname"],
            user=config["user"],
            password=config["pass"],
            cursor_factory=RealDictCursor,
            connect_timeout=2
        )
        return conn, config["host"]
    except:
        return None, None

@app.on_event("startup")
async def startup():
    # Inicializa a tabela em todos os Shards
    for tenant in SHARDS:
        conn, host = get_db_conn(tenant)
        if conn:
            with conn.cursor() as cur:
                cur.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username VARCHAR(50), email VARCHAR(50));")
                conn.commit()
            conn.close()
            print(f"✅ Shard SQL em {host} pronto.")

@app.get("/", include_in_schema=False)
def root():
    return HTMLResponse("<h1>Service A: Sharding Ativo</h1><a href='/docs'>Swagger UI</a>")

class User(BaseModel):
    username: str
    email: str

@app.post("/users", tags=["Sharding Ops"])
async def create_user(user: User, x_tenant_id: Optional[str] = Header(None)):
    # Lógica do Eixo Z: seleciona o banco baseado no Tenant
    tenant_key = "premium" if x_tenant_id == "premium" else "default"
    conn, db_host = get_db_conn(tenant_key)
    
    if not conn:
        raise HTTPException(status_code=503, detail="Erro ao conectar ao Shard SQL")
    
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users (username, email) VALUES (%s, %s) RETURNING id;", (user.username, user.email))
            new_id = cur.fetchone()['id']
            conn.commit()
        
        # Propagação para B (Redis) e C (Mongo)
        await asyncio.gather(
            client.post(f"{SERVICE_B_URL}/session", json={"key": f"u_{new_id}", "value": "active"}),
            client.post(f"{SERVICE_C_URL}/audit", json={"action": "WRITE", "details": f"User {new_id} on {db_host}"}),
            return_exceptions=True
        )
        
        return {"id": new_id, "shard_db": db_host, "tenant": tenant_key}
    finally:
        conn.close()

@app.get("/users", tags=["Sharding Ops"])
async def list_users(x_tenant_id: Optional[str] = Header(None)):
    tenant_key = "premium" if x_tenant_id == "premium" else "default"
    conn, db_host = get_db_conn(tenant_key)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users ORDER BY id DESC LIMIT 10;")
            return {"shard": db_host, "users": cur.fetchall()}
    finally:
        if conn: conn.close()