from fastapi import (APIRouter, HTTPException, Depends, status, Response,
                     Request, BackgroundTasks, Security, UploadFile, File)
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from fastapi_limiter.depends import RateLimiter
from src.auth_services import Auth
from src.schemas import TokenSchema, UserSchema, UserResponse, RequestEmail
from src.repository.users import (get_user_by_email, create_user,
                                  get_user_by_email, update_token, update_avatar_url)
from src.database.db import get_db

import pickle
from config import config
import cloudinary
import cloudinary.uploader
from src.database.models import User
from src.send_email import send_email


router = APIRouter(prefix='/auth', tags=['auth'])
get_refresh_token = HTTPBearer()
cloudinary.config(
    cloud_name=config.CLD_NAME,
    api_key=config.CLD_API_KEY,
    api_secret=config.CLD_API_SECRET,
    secure=True,
)

@router.post("/signup/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(body: UserSchema, bt: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    if get_user_by_email(body.email, db):
        print(1)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",

        )
    body.password = Auth.get_password_hash(body.password)
    db_user = create_user(body, db)
    bt.add_task(send_email, db_user.email, db_user.username, str(request.base_url))
    return db_user



@router.post("/login/", response_model=TokenSchema)
def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = get_user_by_email(body.username, db)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not db_user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not confirmed",
        )

    if not Auth.verify_password(body.password, db_user.password):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = Auth.create_access_token(data={'sub': db_user.email})
    refresh_token = Auth.create_refresh_token(data={'sub': db_user.email})
    update_token(db_user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get("/refresh_token/", response_model=TokenSchema)
def refresh_token(credentials: HTTPAuthorizationCredentials = Security(get_refresh_token),
                           db: Session = Depends(get_db)):
    token = credentials.credentials
    email = Auth.decode_refresh_token()
    user = get_user_by_email(email, db)
    if user.refresh_token != token:
        update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    access_token = Auth.create_access_token(data={'sub': email})
    refresh_token = Auth.create_refresh_token(data={'sub': email})
    update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.get('/confirmed_email/{token}')
def confirmed_email(token: str, db: Session = Depends(get_db)):
    email = Auth.get_email_from_token(token)
    user = get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email')
def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                  db: Session = Depends(get_db)):
    user = get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, str(request.base_url))
    return {"message": "Check your email for confirmation."}


@router.get('/{username}')
def request_email(username: str, response: Response, db: Session = Depends(get_db)):
    print('--------------------------------')
    print(f'{username} зберігаємо що він відкрив email в БД')
    print('--------------------------------')
    return FileResponse("static/open_check.png", media_type="image/png", content_disposition_type="inline")

@router.get('/me', response_model=UserResponse, dependencies=[Depends(RateLimiter(times=1, seconds=20))],
)
def get_current_user(user: User = Depends(Auth.get_current_user)):
    return user

@router.patch(
    "/avatar",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=1, seconds=20))],
)

def get_current_user(
    file: UploadFile = File(),
    user: User = Depends(Auth.get_current_user),
    db: Session = Depends(get_db),
):
    public_id = f"HW11/{user.email}"
    res = cloudinary.uploader.upload(file.file, public_id=public_id, owerite=True)
    print(res)
    res_url = cloudinary.CloudinaryImage(public_id).build_url(
        width=250, height=250, crop="fill", version=res.get("version")
    )
    user = update_avatar_url(user.email, res_url, db)
    Auth.cache.set(user.email, pickle.dumps(user))
    Auth.cache.expire(user.email, 300)
    return user