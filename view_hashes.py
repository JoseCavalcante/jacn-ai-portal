from db.database import SessionLocal
from db.models import User

db = SessionLocal()
users = db.query(User).all()
for u in users:
    print(f"User: {u.username}, Hash: {u.password_hash[:20]}...")
db.close()
