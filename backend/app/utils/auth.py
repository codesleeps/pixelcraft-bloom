from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from ..config import settings
from .supabase_client import get_supabase_client

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_supabase_token(token: str):
    if not settings.supabase or not settings.supabase.jwt_secret:
        raise HTTPException(status_code=500, detail="JWT secret not configured")
    try:
        payload = jwt.decode(token, settings.supabase.jwt_secret, algorithms=[settings.supabase.jwt_algorithm])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_supabase_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    supabase = get_supabase_client()
    response = supabase.table("user_profiles").select("role, metadata").eq("user_id", user_id).execute()
    if not response.data:
        raise HTTPException(status_code=401, detail="User profile not found")
    profile = response.data[0]
    return {
        "user_id": user_id,
        "role": profile["role"],
        "metadata": profile.get("metadata", {})
    }

def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user