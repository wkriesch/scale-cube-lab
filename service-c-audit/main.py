import os
from fastapi import FastAPI
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient # MongoDB Async

app = FastAPI(title="Service C - Audit (MongoDB)")

MONGO_URL = os.getenv("MONGO_URL", "mongodb://admin:password@mongodb:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client.audit_db

class AuditLog(BaseModel):
    action: str
    details: str

@app.post("/audit")
async def log_audit(log: AuditLog):
    await db.logs.insert_one(log.dict())
    return {"status": "logged"}

@app.get("/audit")
async def list_audit():
    cursor = db.logs.find().sort("_id", -1).limit(10)
    logs = await cursor.to_list(length=10)
    for log in logs: log["_id"] = str(log["_id"]) # Converte ID do Mongo
    return logs