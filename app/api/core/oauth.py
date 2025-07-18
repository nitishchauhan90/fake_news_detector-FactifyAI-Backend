from fastapi import Depends, HTTPException, status ,Request
from fastapi.security import OAuth2PasswordBearer
from .security import verify_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_token_from_request(request: Request, token: str = Depends(oauth2_scheme)):
    cookie_token = request.cookies.get("clarifyai_token")
    # print("Incoming token via cookie →", cookie_token)
    # print("Incoming token via header →", token)
    if cookie_token:
        return cookie_token
    if token:
        return token
    raise HTTPException(status_code=401, detail="Missing authentication token")

#new
# def get_token_from_request(request: Request):
#     token = request.cookies.get("clarifyai_token")
#     print("Token from cookie:", token)  # Debug check
#     if not token:
#         raise HTTPException(status_code=401, detail="Missing authentication token (cookie)")
#     return token

# def get_token_from_cookie(request: Request) -> str:   ##ye change 
#     token = request.cookies.get("clarifyai_token")
#     if not token:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Missing authentication token",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     return token


def get_current_user(token: str = Depends(get_token_from_request)):
    payload = verify_access_token(token)
    user_id = payload.get("sub")
    # print(user_id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload



# from bson import ObjectId

# def get_current_user_id(request: Request):
#     token = request.cookies.get("clarifyai_token")
#     if not token:
#         raise HTTPException(status_code=401, detail="Missing authentication token")
#     payload = verify_access_token(token)
#     user_id = payload.get("sub")
#     if not isinstance(user_id, str) or not ObjectId.is_valid(user_id):
#         raise HTTPException(status_code=400, detail="Invalid user ID format")
#     return user_id