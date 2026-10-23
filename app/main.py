import uuid
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from models.customer import Customer
from models.business import Business
from models.transaction import Transaction, TransactionStatus
from schemas import transaction
from schemas import transaction
from schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionStatusUpdate,
)

ALLOWED_STATUS_TRANSITIONS = {
    TransactionStatus.PENDING: {
        TransactionStatus.SUCCESSFUL,
        TransactionStatus.FAILED,
    },
    TransactionStatus.SUCCESSFUL: {
        TransactionStatus.REVERSED,
    },
    TransactionStatus.FAILED: set(),
    TransactionStatus.REVERSED: set(),
}


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

# retrieve a transaction by its ID
@app.get("/transactions/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    # 1. Retrieve the transaction from the database.
    transaction = db.get(Transaction, transaction_id)

    # 2. If the transaction does not exist, raise a 404 error.
    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )
    # 3. Return the transaction.
    return transaction

# retrieve a list of transactions with optional filtering by status, limit, and offset
@app.get("/transactions", response_model=list[TransactionResponse])
def get_transactions(
    status: TransactionStatus | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    # 1. Build the base query for transactions.
    query = db.query(Transaction)

    # 2. Filter transactions by status if provided.
    if status is not None:
        query = query.filter(Transaction.status == status)

    transactions = (
        query
        .order_by(Transaction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # 3. Return the list of transactions.
    return transactions

@app.patch(
    "/transactions/{transaction_id}/status",
    response_model=TransactionResponse
)
def update_transaction_status(
    transaction_id: uuid.UUID,
    status_update: TransactionStatusUpdate,
    db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id
    ).first()

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    allowed_statuses = ALLOWED_STATUS_TRANSITIONS[transaction.status]

    if status_update.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot change status from {transaction.status.value} "
                f"to {status_update.status.value}"
        )
    ) 

    transaction.status = status_update.status

    db.commit()
    db.refresh(transaction)

    return transaction
