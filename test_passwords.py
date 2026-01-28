from service.auth_service import verificar_login
from db.database import SessionLocal
from db.models import User

users = ['ailton', 'dorival', 'jacn', 'jose']
common_pwds = ['admin', '123456', 'ailton', 'dorival', 'jacn', 'jose', '123', 'admin123']

for u in users:
    print(f"Testing user: {u}")
    for p in common_pwds:
        user_obj = verificar_login(u, p)
        if user_obj:
            print(f"  [SUCCESS] Match found: {u} / {p}")
            break
    else:
        print(f"  [FAILED] No common password matched for {u}")
