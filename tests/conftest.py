import os

from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

from models.customer import Customer
from models.business import Business
from models.transaction import Transaction


load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is not configured.")

if "payment_transaction_test_db" not in TEST_DATABASE_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL must point to payment_transaction_test_db."
    )

test_engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def setup_test_database():
    Base.metadata.create_all(bind=test_engine)