from run import app
from app.seed import seed_all

print("[BOOT] Running pre-flight database seeding...")
with app.app_context():
    seed_all()
print("[BOOT] Pre-flight complete. Starting Gunicorn...")
