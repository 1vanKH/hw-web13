from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from libgravatar import Gravatar

from src.database.db import get_db
from src.database.models import User
from src.schemas import UserSchema


def get_user_by_email(email: str, db: Session = Depends(get_db)):
    stmt = select(User).filter_by(email=email)
    user = db.execute(stmt)
    user = user.scalar_one_or_none()
    return user


def create_user(body: UserSchema, db: Session = Depends(get_db)):
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as err:
        print(err)

    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def update_token(user: User, token: str | None, db: Session):
    user.refresh_token = token
    db.commit()


def confirmed_email(email: str, db: Session) -> None:
    user = get_user_by_email(email, db)
    user.confirmed = True
    db.commit()


def update_avatar_url(email: str, url: str | None, db: Session) -> User:
    user = get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    db.refresh(user)
    return user