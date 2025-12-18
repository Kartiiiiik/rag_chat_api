from fastapi import APIRouter, Depends, HTTPException, status, Request
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from app.api.v1.deps import get_db
from app.core import security
from app.core.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, FRONTEND_URL
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token
import secrets

router = APIRouter(prefix="/auth", tags=["auth"])

oauth = OAuth()
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@router.post("/signup", response_model=UserResponse)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    
    new_user = User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token = security.create_access_token(subject=user.email)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/google/login")
async def google_login(request: Request):
    return await oauth.google.authorize_redirect(request, GOOGLE_REDIRECT_URI)

@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google authentication failed: {str(e)}")
    
    user_info = token.get('userinfo')
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to fetch user info from Google")
    
    email = user_info.get('email')
    name = user_info.get('name')
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Create user if it doesn't exist
        user = User(
            email=email,
            full_name=name,
            hashed_password=security.get_password_hash(secrets.token_urlsafe(32)), # Random password for OAuth users
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    
    # Secure way: Use a short-lived exchange code instead of the final token in the URL.
    # This prevents the final token from being logged in browser history.
    exchange_token = security.create_access_token(
        subject=user.email, 
        expires_delta=timedelta(minutes=5) # 5 minutes is plenty for the redirect
    )
    
    frontend_url = f"{FRONTEND_URL}/auth/callback" 
    return RedirectResponse(url=f"{frontend_url}?code={exchange_token}")

@router.post("/google/token-exchange", response_model=Token)
async def google_token_exchange(code: str, db: Session = Depends(get_db)):
    """
    Exchange a short-lived OAuth redirection code for a long-lived access token.
    """
    try:
        from app.core.config import SECRET_KEY, ALGORITHM
        from jose import jwt, JWTError
        
        payload = jwt.decode(code, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid exchange code")
            
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        access_token = security.create_access_token(subject=user.email)
        return {"access_token": access_token, "token_type": "bearer"}
        
    except JWTError:
        raise HTTPException(status_code=400, detail="Exchange code expired or invalid")
