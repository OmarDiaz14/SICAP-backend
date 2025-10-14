# cobrador/jwt_utils.py
# cobrador/jwt_utils.py
import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings

def create_access_token(payload: dict, minutes: int | None = None) -> str:
    conf = getattr(settings, "JWT_SETTINGS", {})
    lifetime_min = minutes or conf.get("ACCESS_TOKEN_LIFETIME_MIN", 60)
    alg = conf.get("ALGORITHM", "HS256")

    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=lifetime_min)

    if "sub" in payload and payload["sub"] is not None:
        payload["sub"] = str(payload["sub"])
        
    to_encode = {"exp": exp, "iat": now, **payload}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=alg)

def decode_token(token: str) -> dict:
    conf = getattr(settings, "JWT_SETTINGS", {})
    alg = conf.get("ALGORITHM", "HS256")
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[alg])
