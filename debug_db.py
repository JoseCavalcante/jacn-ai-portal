from db.database import SessionLocal
from db.models import User, Tenant

db = SessionLocal()
print("--- TENANTS ---")
tenants = db.query(Tenant).all()
for t in tenants:
    print(f"ID: {t.id}, Name: {t.name}, Tier: {t.subscription_tier}")

print("\n--- USERS ---")
users = db.query(User).all()
for u in users:
    print(f"ID: {u.id}, Username: {u.username}, Role: {u.role}, Tenant ID: {u.tenant_id}")
db.close()
