import asyncio
from datetime import date, timedelta
import random
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

from backend.database import async_session_maker
from backend.models import Business, User, Client, Transaction, Invoice

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_data():
    async with async_session_maker() as session:
        # 1. Create a Test Business
        business = Business(
            name="Neev Test Business Ltd",
            gstin="27AAAAA1111A1Z1",
            pan="AAAAA1111A",
            business_type="Private Limited",
            onboarding_date=date.today() - timedelta(days=90),
            data_sources_connected=["tally", "gst", "bank"],
            quality_score=85,
            safety_threshold_inr=50000.0,
        )
        session.add(business)
        await session.flush()  # to populate business.id

        # 2. Create a Test User
        hashed_password = pwd_context.hash("password123")
        user = User(
            business_id=business.id,
            email="test@neevfinance.com",
            hashed_password=hashed_password,
            full_name="Test Business Owner",
        )
        session.add(user)

        # 3. Create Clients
        clients_data = [
            {"name": "Tata Consultancy Services Ltd", "gstin": "27AAAAT1111A1Z2", "rev_share": 35.0, "delay": 5},
            {"name": "Reliance Industries Ltd", "gstin": "27AAAAR1111A1Z3", "rev_share": 25.0, "delay": 12},
            {"name": "Infosys Technologies", "gstin": "27AAABI1111A1Z4", "rev_share": 15.0, "delay": 8},
            {"name": "Acme Widgets India", "gstin": "27AAAAC1111A1Z5", "rev_share": 10.0, "delay": 20},
            {"name": "Local Retailer Store", "gstin": None, "rev_share": 15.0, "delay": 2},
        ]
        
        clients = []
        for c in clients_data:
            client = Client(
                business_id=business.id,
                canonical_name=c["name"],
                gstin=c["gstin"],
                is_listed_company=c["name"].endswith("Ltd") or "Technologies" in c["name"],
                bse_code="500000" if c["name"].startswith("Tata") else None,
                total_revenue_share=c["rev_share"],
                avg_payment_delay_days=c["delay"],
                aliases=[c["name"], c["name"].replace(" Ltd", "").replace(" Technologies", "")],
            )
            session.add(client)
            clients.append(client)
        
        await session.flush()

        # 4. Generate ~90 Days of transactions & invoices
        start_date = date.today() - timedelta(days=90)
        
        # We start with some initial balance
        # For simplicity, we seed transactions directly.
        categories_in = ["Sales Revenue", "GST Refund", "Interest Income"]
        categories_out = ["Salary", "Rent", "Office Supplies", "Vendor Payment", "Electricity", "Internet"]

        current_date = start_date
        while current_date <= date.today():
            # Daily random transactions
            # 1. Salary on 1st of month
            if current_date.day == 1:
                t = Transaction(
                    business_id=business.id,
                    date=current_date,
                    amount=150000.0,
                    direction="out",
                    category="Salary",
                    source="bank",
                    raw_description="Monthly salary payout",
                )
                session.add(t)

            # 2. Rent on 5th of month
            if current_date.day == 5:
                t = Transaction(
                    business_id=business.id,
                    date=current_date,
                    amount=35000.0,
                    direction="out",
                    category="Rent",
                    source="bank",
                    raw_description="Office rent transfer",
                )
                session.add(t)

            # 3. Regular Sales / Inflow (Random days)
            if random.random() < 0.4:
                # Random client pays
                client = random.choice(clients)
                amount = round(random.uniform(10000, 150000), 2)
                t = Transaction(
                    business_id=business.id,
                    date=current_date,
                    amount=amount,
                    direction="in",
                    category="Sales Revenue",
                    counterparty_id=client.id,
                    source=random.choice(["tally", "gst", "bank"]),
                    raw_description=f"Payment received from {client.canonical_name}",
                )
                session.add(t)

                # Also add a corresponding invoice
                issue_date = current_date - timedelta(days=random.randint(15, 45))
                invoice = Invoice(
                    business_id=business.id,
                    client_id=client.id,
                    amount=amount,
                    issue_date=issue_date,
                    due_date=issue_date + timedelta(days=30),
                    paid_date=current_date,
                    status="paid",
                    days_overdue=max(0, (current_date - (issue_date + timedelta(days=30))).days),
                )
                session.add(invoice)

            # 4. Regular Vendor Outflow (Random days)
            if random.random() < 0.3:
                amount = round(random.uniform(5000, 40000), 2)
                t = Transaction(
                    business_id=business.id,
                    date=current_date,
                    amount=amount,
                    direction="out",
                    category="Vendor Payment",
                    source=random.choice(["tally", "bank"]),
                    raw_description=f"Vendor payment reference #{random.randint(1000, 9999)}",
                )
                session.add(t)

            # 5. Small expenses
            if random.random() < 0.5:
                amount = round(random.uniform(200, 3000), 2)
                t = Transaction(
                    business_id=business.id,
                    date=current_date,
                    amount=amount,
                    direction="out",
                    category=random.choice(["Office Supplies", "Electricity", "Internet"]),
                    source="bank",
                    raw_description="Debit card txn",
                )
                session.add(t)

            current_date += timedelta(days=1)

        # 5. Add a few pending and overdue invoices at the end
        for i in range(5):
            client = random.choice(clients)
            amount = round(random.uniform(20000, 100000), 2)
            issue_date = date.today() - timedelta(days=random.randint(5, 45))
            due_date = issue_date + timedelta(days=30)
            
            is_overdue = due_date < date.today()
            status = "overdue" if is_overdue else "pending"
            days_overdue = (date.today() - due_date).days if is_overdue else None

            invoice = Invoice(
                business_id=business.id,
                client_id=client.id,
                amount=amount,
                issue_date=issue_date,
                due_date=due_date,
                paid_date=None,
                status=status,
                days_overdue=days_overdue,
            )
            session.add(invoice)

        await session.commit()
        print("Database seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed_data())
