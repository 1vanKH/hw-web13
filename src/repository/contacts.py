from datetime import date, timedelta
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.database.models import Contact
from src.schemas import ContactCreate, ContactUpdate

def create_contact(db: Session, contact: ContactCreate):
    db_contact = Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def get_contacts(db: Session, q: str = None):
    query = db.query(Contact)
    if q:
        query = query.filter(
            Contact.first_name.ilike(f"%{q}%") |
            Contact.last_name.ilike(f"%{q}%") |
            Contact.email.ilike(f"%{q}%")
        )
    return query.all()

def get_contact(db: Session, contact_id: int):
    return db.query(Contact).filter(Contact.id == contact_id).first()

def update_contact(db: Session, contact_id: int, contact: ContactUpdate):
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    for key, value in contact.dict(exclude_unset=True).items():
        setattr(db_contact, key, value)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def delete_contact(db: Session, contact_id: int):
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    db.delete(db_contact)
    db.commit()

def get_upcoming_birthdays(db: Session):
    today = date.today()
    week_later = today + timedelta(days=7)
    return db.query(Contact).filter(
        func.date_trunc('day', Contact.birthday) >= today,
        func.date_trunc('day', Contact.birthday) <= week_later
    ).all()