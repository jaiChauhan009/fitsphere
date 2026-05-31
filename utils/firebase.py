import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings

_initialized = False
bearer_scheme = HTTPBearer(auto_error=False)


def _init_firebase():
    global _initialized
    if not _initialized and settings.FIREBASE_SERVICE_ACCOUNT_JSON:
        try:
            import json, os
            value = settings.FIREBASE_SERVICE_ACCOUNT_JSON
            if os.path.isfile(value):
                cred = credentials.Certificate(value)
            else:
                cred = credentials.Certificate(json.loads(value))
            firebase_admin.initialize_app(cred)
            _initialized = True
        except Exception:
            pass


async def get_current_firebase_uid(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> str:
    _init_firebase()
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing auth token")
    try:
        decoded = auth.verify_id_token(credentials.credentials)
        return decoded["uid"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def get_optional_uid(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> str | None:
    if not credentials:
        return None
    try:
        _init_firebase()
        decoded = auth.verify_id_token(credentials.credentials)
        return decoded["uid"]
    except Exception:
        return None
