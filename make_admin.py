"""One-off helper: promote a user to admin role."""
from app.database import SessionLocal
from app.services import admin_service

EMAIL = "idris@abu.edu.ng"

db = SessionLocal()
try:
    users = admin_service.list_all_users(db)
    target = next((u for u in users if u.email == EMAIL), None)
    if not target:
        print(f"No user found with email: {EMAIL}")
    else:
        admin_service.set_user_role(db, target.id, "admin")
        print(f"✅ {target.email} is now role='admin'")
finally:
    db.close()