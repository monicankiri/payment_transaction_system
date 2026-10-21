
import uuid

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from models.customer import Customer
from models.business import Business
from models.transaction import Transaction
from schemas.transaction import TransactionCreate, TransactionResponse


app = FastAPI()


@app.get("/")
def read_root():
    return {
        "message": "Payment Transaction System API is running"
    }


@app.post("/transactions", response_model=TransactionResponse, status_code=201)
def create_transaction(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db)
):
    # 1. Check whether the customer exists.
    customer = db.get(Customer, transaction_data.customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    # 2. Check whether the business exists.
    business = db.get(Business, transaction_data.business_id)

    if business is None:
        raise HTTPException(
            status_code=404,
            detail="Business not found"
        )

    # 3. Generate a unique transaction reference.
    reference = f"TXN-{uuid.uuid4().hex[:12].upper()}"

    # 4. Create the transaction object.
    new_transaction = Transaction(
        reference=reference,
        customer_id=transaction_data.customer_id,
        business_id=transaction_data.business_id,
        amount=transaction_data.amount,
        currency=transaction_data.currency
    )

    # 5. Save the transaction.
    try:
        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to create transaction"
        )

    # 6. Return the saved transaction.
    return new_transaction
