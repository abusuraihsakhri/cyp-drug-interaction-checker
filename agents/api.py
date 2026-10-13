"""FastAPI service for CYP catalog lookup and the legacy demonstration supervisor."""
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from cyp_checker import lookup
from .base import AuditLogger, SecurityException
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")
app = FastAPI(title="CYP Drug Role Lookup API", description="Limited catalog lookup; legacy audit endpoints are experimental demonstrations.", version="3.1.0")

class ChatRequest(BaseModel):
    query: str

@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "cyp-drug-interaction-checker", "catalog_records": 25, "version": "3.1.0"}

@app.get("/metrics")
def metrics():
    return {"dossiers_processed_total": len(supervisor.dossier_registry), "audit_blocks_total": len(AuditLogger.get_trail()), "system_status": "NOMINAL"}

@app.get("/api/lookup")
def api_lookup(query: str = Query(min_length=1, max_length=200)):
    return lookup(query)

@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        return supervisor.process_task(payload).to_dict()
    except SecurityException:
        raise HTTPException(status_code=422, detail="Input contains a restricted identifier.") from None

@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        return {"response": supervisor.query_supervisory_chat(req.query)}
    except SecurityException:
        raise HTTPException(status_code=422, detail="Input contains a restricted identifier.") from None

@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}

app.mount("/", StaticFiles(directory=Path(__file__).resolve().parent.parent / "web", html=True), name="web")
