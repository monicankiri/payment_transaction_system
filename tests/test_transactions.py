from decimal import Decimal
from models.customer import Customer
from models.business import Business
from models.transaction import TransactionStatus


# Test the root endpoint
def test_read_root(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Payment Transaction System API is running"
    }

def test_create_transaction(client):
    # Arrange: create a customer and business
    from tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as db:
        customer = Customer(
            name="Test Customer",
            email="customer@example.com",
        )

        business = Business(
            name="Test Business",
            email="business@example.com",
        )

        db.add_all([customer, business])
        db.commit()

        db.refresh(customer)
        db.refresh(business)

        customer_id = customer.id
        business_id = business.id

    # Act: send a request to the API
    response = client.post(
        "/transactions",
        json={
            "customer_id": str(customer_id),
            "business_id": str(business_id),
            "amount": "2500.00",
            "currency": "NGN",
        },
    )

    # Assert: verify the API response
    assert response.status_code == 201

    data = response.json()

    assert data["customer_id"] == str(customer_id)
    assert data["business_id"] == str(business_id)
    assert Decimal(data["amount"]) == Decimal("2500.00")
    assert data["currency"] == "NGN"
    assert data["status"] == TransactionStatus.PENDING.value
    assert data["reference"].startswith("TXN-")


def test_create_transaction_with_missing_customer(client):
    from uuid import uuid4

    from models.business import Business
    from conftest import TestingSessionLocal

    with TestingSessionLocal() as db:
        business = Business(
            name="Test Business",
            email="missing-customer-business@example.com",
        )
        db.add(business)
        db.commit()
        db.refresh(business)

        business_id = business.id

    response = client.post(
        "/transactions",
        json={
            "customer_id": str(uuid4()),
            "business_id": str(business_id),
            "amount": "2500.00",
            "currency": "NGN",
        },
    )

    assert response.status_code == 404


def test_create_transaction_with_zero_amount(client):
    from conftest import TestingSessionLocal
    from models.customer import Customer
    from models.business import Business

    with TestingSessionLocal() as db:
        customer = Customer(
            name="Test Customer",
            email="zero-amount-customer@example.com",
        )
        business = Business(
            name="Test Business",
            email="zero-amount-business@example.com",
        )

        db.add_all([customer, business])
        db.commit()
        db.refresh(customer)
        db.refresh(business)

        customer_id = customer.id
        business_id = business.id

    response = client.post(
        "/transactions",
        json={
            "customer_id": str(customer_id),
            "business_id": str(business_id),
            "amount": "0.00",
            "currency": "NGN",
        },
    )

    assert response.status_code == 422
    
def test_get_transaction_by_id(client):
    from conftest import TestingSessionLocal
    from models.customer import Customer
    from models.business import Business
    from models.transaction import Transaction

    # Arrange: create the customer, business, and transaction.
    with TestingSessionLocal() as db:
        customer = Customer(
            name="Retrieval Test Customer",
            email="retrieval-customer@example.com",
        )
        business = Business(
            name="Retrieval Test Business",
            email="retrieval-business@example.com",
        )

        db.add_all([customer, business])
        db.commit()
        db.refresh(customer)
        db.refresh(business)

        transaction = Transaction(
            reference="TXN-RETRIEVAL001",
            customer_id=customer.id,
            business_id=business.id,
            amount=2500.00,
            currency="NGN",
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        transaction_id = transaction.id

    # Act: request the transaction using its ID.
    response = client.get(f"/transactions/{transaction_id}")

    # Assert: verify that the correct transaction is returned.
    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(transaction_id)
    assert data["reference"] == "TXN-RETRIEVAL001"
    assert data["currency"] == "NGN"
    assert data["status"] == "PENDING"


def test_get_nonexistent_transaction(client):
    from uuid import uuid4

    nonexistent_id = uuid4()

    response = client.get(f"/transactions/{nonexistent_id}")

    assert response.status_code == 404

def test_list_transactions(client):
    from conftest import TestingSessionLocal
    from models.customer import Customer
    from models.business import Business
    from models.transaction import Transaction

    with TestingSessionLocal() as db:
        customer = Customer(
            name="List Test Customer",
            email="list-customer@example.com",
        )
        business = Business(
            name="List Test Business",
            email="list-business@example.com",
        )

        db.add_all([customer, business])
        db.commit()
        db.refresh(customer)
        db.refresh(business)

        transactions = [
            Transaction(
                reference="TXN-LIST000001",
                customer_id=customer.id,
                business_id=business.id,
                amount=1000.00,
                currency="NGN",
            ),
            Transaction(
                reference="TXN-LIST000002",
                customer_id=customer.id,
                business_id=business.id,
                amount=2000.00,
                currency="NGN",
            ),
        ]

        db.add_all(transactions)
        db.commit()

    response = client.get("/transactions")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert {item["reference"] for item in data} == {
        "TXN-LIST000001",
        "TXN-LIST000002",
    }

def test_filter_transactions_by_status(client):
    from conftest import TestingSessionLocal
    from models.customer import Customer
    from models.business import Business
    from models.transaction import Transaction, TransactionStatus

    with TestingSessionLocal() as db:
        customer = Customer(
            name="Filter Test Customer",
            email="filter-customer@example.com",
        )
        business = Business(
            name="Filter Test Business",
            email="filter-business@example.com",
        )

        db.add_all([customer, business])
        db.commit()
        db.refresh(customer)
        db.refresh(business)

        transactions = [
            Transaction(
                reference="TXN-FILTER0001",
                customer_id=customer.id,
                business_id=business.id,
                amount=1000.00,
                currency="NGN",
                status=TransactionStatus.PENDING,
            ),
            Transaction(
                reference="TXN-FILTER0002",
                customer_id=customer.id,
                business_id=business.id,
                amount=2000.00,
                currency="NGN",
                status=TransactionStatus.SUCCESSFUL,
            ),
        ]

        db.add_all(transactions)
        db.commit()

    response = client.get("/transactions?status=SUCCESSFUL")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["reference"] == "TXN-FILTER0002"
    assert data[0]["status"] == "SUCCESSFUL"

def test_list_transactions_with_pagination(client):
    from conftest import TestingSessionLocal
    from models.customer import Customer
    from models.business import Business
    from models.transaction import Transaction

    with TestingSessionLocal() as db:
        customer = Customer(
            name="Pagination Test Customer",
            email="pagination-customer@example.com",
        )
        business = Business(
            name="Pagination Test Business",
            email="pagination-business@example.com",
        )

        db.add_all([customer, business])
        db.commit()
        db.refresh(customer)
        db.refresh(business)

        transactions = [
            Transaction(
                reference=f"TXN-PAGE{i:06d}",
                customer_id=customer.id,
                business_id=business.id,
                amount=1000 + i,
                currency="NGN",
            )
            for i in range(1, 5)
        ]

        db.add_all(transactions)
        db.commit()

    response = client.get("/transactions?limit=2&offset=0")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    
def test_list_transactions_with_offset(client):
    from conftest import TestingSessionLocal
    from models.customer import Customer
    from models.business import Business
    from models.transaction import Transaction

    with TestingSessionLocal() as db:
        customer = Customer(
            name="Offset Test Customer",
            email="offset-customer@example.com",
        )
        business = Business(
            name="Offset Test Business",
            email="offset-business@example.com",
        )

        db.add_all([customer, business])
        db.commit()
        db.refresh(customer)
        db.refresh(business)

        transactions = [
            Transaction(
                reference=f"TXN-OFFSET{i:06d}",
                customer_id=customer.id,
                business_id=business.id,
                amount=1000 + i,
                currency="NGN",
            )
            for i in range(1, 5)
        ]

        db.add_all(transactions)
        db.commit()

    response = client.get("/transactions?limit=2&offset=2")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert {
        item["reference"] for item in data
    } == {
        "TXN-OFFSET000001",
        "TXN-OFFSET000002",
    }

def test_update_transaction_status_to_successful(client):
    from conftest import TestingSessionLocal
    from models.customer import Customer
    from models.business import Business
    from models.transaction import Transaction, TransactionStatus

    # Arrange: create the customer, business, and pending transaction.
    with TestingSessionLocal() as db:
        customer = Customer(
            name="Status Test Customer",
            email="status-customer@example.com",
        )
        business = Business(
            name="Status Test Business",
            email="status-business@example.com",
        )

        db.add_all([customer, business])
        db.commit()
        db.refresh(customer)
        db.refresh(business)

        transaction = Transaction(
            reference="TXN-STATUS0001",
            customer_id=customer.id,
            business_id=business.id,
            amount=5000.00,
            currency="NGN",
            status=TransactionStatus.PENDING,
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        transaction_id = transaction.id

    # Act: request the status update.
    response = client.patch(
        f"/transactions/{transaction_id}/status",
        json={"status": "SUCCESSFUL"},
    )

    # Assert: verify the update succeeded.
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == str(transaction_id)
    assert data["status"] == "SUCCESSFUL"

def test_reject_invalid_status_transition(client):
    from conftest import TestingSessionLocal
    from models.customer import Customer
    from models.business import Business
    from models.transaction import Transaction, TransactionStatus

    # Arrange: create a failed transaction.
    with TestingSessionLocal() as db:
        customer = Customer(
            name="Invalid Transition Customer",
            email="invalid-transition-customer@example.com",
        )
        business = Business(
            name="Invalid Transition Business",
            email="invalid-transition-business@example.com",
        )

        db.add_all([customer, business])
        db.commit()
        db.refresh(customer)
        db.refresh(business)

        transaction = Transaction(
            reference="TXN-INVALID0001",
            customer_id=customer.id,
            business_id=business.id,
            amount=3000.00,
            currency="NGN",
            status=TransactionStatus.FAILED,
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        transaction_id = transaction.id

    # Act: attempt an invalid transition.
    response = client.patch(
        f"/transactions/{transaction_id}/status",
        json={"status": "SUCCESSFUL"},
    )

    # Assert: the API rejects the transition.
    assert response.status_code == 400

def test_reject_successful_to_failed_transition(client):
    from conftest import TestingSessionLocal
    from models.customer import Customer
    from models.business import Business
    from models.transaction import Transaction, TransactionStatus

    with TestingSessionLocal() as db:
        customer = Customer(
            name="Transition Test Customer",
            email="success-failed-customer@example.com",
        )
        business = Business(
            name="Transition Test Business",
            email="success-failed-business@example.com",
        )

        db.add_all([customer, business])
        db.commit()
        db.refresh(customer)
        db.refresh(business)

        transaction = Transaction(
            reference="TXN-SUCCESSFAILED01",
            customer_id=customer.id,
            business_id=business.id,
            amount=4000.00,
            currency="NGN",
            status=TransactionStatus.SUCCESSFUL,
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        transaction_id = transaction.id

    response = client.patch(
        f"/transactions/{transaction_id}/status",
        json={"status": "FAILED"},
    )

    assert response.status_code == 400
def test_update_successful_transaction_to_reversed(client):
    from conftest import TestingSessionLocal
    from models.customer import Customer
    from models.business import Business
    from models.transaction import Transaction, TransactionStatus

    customer = Customer(
        name="Reversal Test Customer",
        email="reversal-customer@example.com",
    )
    business = Business(
        name="Reversal Test Business",
        email="reversal-business@example.com",
    )

    with TestingSessionLocal() as db:
        db.add_all([customer, business])
        db.commit()
        db.refresh(customer)
        db.refresh(business)

        transaction = Transaction(
            reference="TXN-REVERSALTEST01",
            customer_id=customer.id,
            business_id=business.id,
            amount=5000.00,
            currency="NGN",
            status=TransactionStatus.SUCCESSFUL,
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        transaction_id = transaction.id

    response = client.patch(
        f"/transactions/{transaction_id}/status",
        json={"status": "REVERSED"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "REVERSED"
    
def test_update_nonexistent_transaction(client):
    from uuid import uuid4

    transaction_id = uuid4()

    response = client.patch(
        f"/transactions/{transaction_id}/status",
        json={"status": "SUCCESSFUL"},
    )

    assert response.status_code == 404        











