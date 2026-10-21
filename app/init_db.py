from app.database import engine, Base

from models.customer import Customer
from models.business import Business
from models.transaction import Transaction


Base.metadata.create_all(bind=engine)
