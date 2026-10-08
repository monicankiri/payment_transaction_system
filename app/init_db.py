from app.database import engine, Base
from models.transaction import Transaction

Base.metadata.create_all(bind=engine)