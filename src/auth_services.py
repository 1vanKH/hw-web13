from datetime import datetime, timedelta
from typing import Optional

import redis
import pickle

from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from config import config
from src.database.db import get_db
import src.repository.users as repository_users


class Auth:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = config.SECRET_KEY_JWT
    ALGORITHM = config.ALGORITHM
    cache = redis.Redis(
        host=config.REDIS_DOMAIN,
        port=config.REDIS_PORT,
        db=0,
        password=config.REDIS_PASSWORD,
    )


    @staticmethod
    def verify_password (plain_password, hashed_password):
        return Auth.pwd_context.verify(plain_password, hashed_password)

  
    @staticmethod
    def get_password_hash(password: str):
        return Auth.pwd_context.hash(password)

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[float] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.now() + timedelta(minutes=15)
        to_encode.update({"iat": datetime.now(), "exp": expire, "scope": "access_token"})
        encoded_access_token = jwt.encode(to_encode, Auth.SECRET_KEY, algorithm=Auth.ALGORITHM)
        return encoded_access_token

    @staticmethod
    def create_refresh_token(data: dict, expires_delta: Optional[float] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.now() + timedelta(days=7)
        to_encode.update({"iat": datetime.now(), "exp": expire, "scope": "refresh_token"})
        encoded_refresh_token = jwt.encode(to_encode, Auth.SECRET_KEY, algorithm=Auth.ALGORITHM)
        return encoded_refresh_token

    @staticmethod
    def decode_refresh_token(refresh_token: str):
        try:
            payload = jwt.decode(refresh_token, Auth.SECRET_KEY, algorithms=[Auth.ALGORITHM])
            if payload['scope'] == 'refresh_token':
                email = payload['sub']
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')

    @staticmethod
    def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Decode JWT
            payload = jwt.decode(token, Auth.SECRET_KEY, algorithms=[Auth.ALGORITHM])
            if payload['scope'] == 'access_token':
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as e:
            raise credentials_exception

        user_hash = str(email)
        user = Auth.cache.get(user_hash)
        if user is None:
            print("User from database")
            user = repository_users.get_user_by_email(email, db)
            if user is None:
                raise credentials_exception
            Auth.cache.set(user_hash, pickle.dumps(user))
            Auth.cache.expire(user_hash, 300)
        else:
            print("User from cache")
            user = pickle.loads(user)
        return user


    @staticmethod
    def create_email_token(data: dict):
        to_encode = data.copy()
        expire = datetime.now() + timedelta(days=7)
        to_encode.update({"iat": datetime.now(), "exp": expire})
        token = jwt.encode(to_encode, Auth.SECRET_KEY, algorithm=Auth.ALGORITHM)
        return token

    @staticmethod
    def get_email_from_token(token: str):
        try:
            payload = jwt.decode(token, Auth.SECRET_KEY, algorithms=[Auth.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Invalid token for email verification")


auth_service = Auth()