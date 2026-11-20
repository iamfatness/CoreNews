import hashlib
import hmac
import json
import re
import time

from fastapi import Depends, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .records import ResearchRecord

bearer = HTTPBearer(auto_error=False)
SIGNATURE_TTL = 15 * 60


def workspace(response: Response, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str:
    if credentials and len(credentials.credentials) <= 512:
        digest = hashlib.sha256(credentials.credentials.encode()).hexdigest()
        for name, expected in settings.research_workspace_token_hashes.items():
            if hmac.compare_digest(digest, expected):
                response.headers["Cache-Control"] = "no-store"
                return name
    raise HTTPException(401, "Enter a valid research workspace key.", headers={"WWW-Authenticate": "Bearer"})


def _signature(workspace_id: str, record: ResearchRecord, expires: int) -> str:
    secret = settings.research_signing_key
    if secret is None or len(secret.get_secret_value().encode()) < 32:
        raise HTTPException(503, "Research signing is not configured.")
    message = json.dumps([workspace_id, expires, record.model_dump(mode="json")],
                         sort_keys=True, separators=(",", ":")).encode()
    return hmac.new(secret.get_secret_value().encode(), message, hashlib.sha256).hexdigest()


def issue_proof(workspace_id: str, record: ResearchRecord) -> str:
    expires = int(time.time()) + SIGNATURE_TTL
    return f"{expires}.{_signature(workspace_id, record, expires)}"


def valid_proof(workspace_id: str, record: ResearchRecord, proof: str) -> bool:
    if not re.fullmatch(r"[0-9]{1,12}\.[a-f0-9]{64}", proof):
        return False
    expires, signature = proof.split(".", 1)
    deadline = int(expires)
    return deadline >= time.time() and hmac.compare_digest(signature, _signature(workspace_id, record, deadline))
