import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock

from sqlalchemy import func
from sqlalchemy.orm import Session
from src.schemas import ContactCreate, ContactUpdate
from src.database.models import Contact, User
from src.repository.contacts import create_contact, get_contact, get_upcoming_birthdays, delete_contact, update_contact, get_contacts


class TestCrud(unittest.TestCase):
    def setUp(self):
        self.user = User(id=1, username='test_user', password='qwerty', confirmed=True)
        self.session = MagicMock(spec=Session)


    def test_create_contact(self):

        db_mock = MagicMock()
        contact_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone_number": "123456789",
            "birthday": datetime(2000, 1, 1)
        }


        created_contact = create_contact(db_mock, ContactCreate(**contact_data))


        assert created_contact.first_name == contact_data["first_name"]
        assert created_contact.last_name == contact_data["last_name"]
        assert created_contact.email == contact_data["email"]
        assert created_contact.phone_number == contact_data["phone_number"]
        assert created_contact.birthday == contact_data["birthday"]

    def test_get_contacts(self):
        # Arrange
        db_mock = MagicMock()
        contacts_data = [
            {"first_name": "John", "last_name": "Doe", "email": "john@example.com"},
            {"first_name": "Jane", "last_name": "Doe", "email": "jane@example.com"}
        ]
        db_mock.query().all.return_value = [Contact(**data) for data in contacts_data]


        contacts = get_contacts(db_mock)
        assert len(contacts) == len(contacts_data)
        for contact, data in zip(contacts, contacts_data):
            assert contact.first_name == data["first_name"]
            assert contact.last_name == data["last_name"]
            assert contact.email == data["email"]

    def test_get_contact(self):
        # Arrange
        db_mock = MagicMock()
        contact_id = 1
        contact_data = {"id": contact_id, "first_name": "John", "last_name": "Doe", "email": "john@example.com"}
        db_mock.query(Contact).filter(Contact.id == contact_id).first.return_value = Contact(**contact_data)

        # Act
        contact = get_contact(db_mock, contact_id)

        # Assert
        assert contact.id == contact_id
        assert contact.first_name == contact_data["first_name"]
        assert contact.last_name == contact_data["last_name"]
        assert contact.email == contact_data["email"]

    def test_update_contact(self):
        # Arrange
        db_mock = MagicMock()
        contact_id = 1
        contact_update_data = {"first_name": "Updated", "last_name": "Doe", "email": "updated@example.com",
                               "phone_number": "987654321", "birthday": datetime(2000, 1, 1)}
        contact_update = ContactUpdate(**contact_update_data)
        db_mock.query(Contact).filter(Contact.id == contact_id).first.return_value = Contact(id=contact_id,
                                                                                             **contact_update_data)

        # Act
        updated_contact = update_contact(db_mock, contact_id, contact_update)

        # Assert
        assert updated_contact.id == contact_id
        assert updated_contact.first_name == contact_update_data["first_name"]
        assert updated_contact.last_name == contact_update_data["last_name"]
        assert updated_contact.email == contact_update_data["email"]

    def test_delete_contact(self):
        # Arrange
        db_mock = MagicMock()
        contact_id = 1
        db_mock.query(Contact).filter(Contact.id == contact_id).first.return_value = Contact(id=contact_id)

        # Act
        delete_contact(db_mock, contact_id)

        # Assert
        db_mock.delete.assert_called_once()
        db_mock.commit.assert_called_once()

    def test_get_upcoming_birthdays(self):
        # Arrange
        db_mock = MagicMock()
        upcoming_birthdays_data = [
            {"first_name": "John", "last_name": "Doe", "email": "john@example.com",
             "birthday": datetime.today() + timedelta(days=1)},
            {"first_name": "Jane", "last_name": "Doe", "email": "jane@example.com",
             "birthday": datetime.today() + timedelta(days=5)}
        ]
        db_mock.query().filter().all.return_value = [Contact(**data) for data in upcoming_birthdays_data]

        # Act
        upcoming_birthdays = get_upcoming_birthdays(db_mock)

        # Assert
        assert len(upcoming_birthdays) == len(upcoming_birthdays_data)
        for contact, data in zip(upcoming_birthdays, upcoming_birthdays_data):
            assert contact.first_name == data["first_name"]
            assert contact.last_name == data["last_name"]
            assert contact.email == data["email"]
            assert contact.birthday == data["birthday"]


if __name__ == '__main__':
    unittest.main()