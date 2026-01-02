from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session
from .database import get_db
from fastapi.middleware.cors import CORSMiddleware
import backend.app.routers.auth as auth_module
import backend.app.routers.motors as motors_module
import backend.app.routers.users as users_module
from .database import engine, SessionLocal
from shared.models import Base, User
import os
import sys
import hashlib

# Add shared to path for subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize default admin user
def init_default_admin():
    db = SessionLocal()
    try:
        default_admin = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin_default")
        
        # Check if admin exists
        existing_admin = db.query(User).filter(User.username == default_admin).first()
        if not existing_admin:
            password_hash = hashlib.sha256(admin_password.encode()).hexdigest()
            admin_user = User(
                username=default_admin,
                password_hash=password_hash,
                role="admin",
                protected=True
            )
            db.add(admin_user)
            db.commit()
            print(f"Default admin user '{default_admin}' created")
        else:
            # Ensure existing admin is protected
            if not existing_admin.protected:
                existing_admin.protected = True
                db.commit()
    finally:
        db.close()

init_default_admin()

app = FastAPI(title="Motor Dynamometer API", version="1.0.0")

# CORS for web app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_module.router, prefix="/auth", tags=["auth"])
app.include_router(motors_module.router, prefix="/motors", tags=["motors"])
app.include_router(users_module.router, prefix="/users", tags=["users"])

# Mount static files directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Simple query to test DB connection
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.get("/.well-known/appspecific/com.chrome.devtools.json")
def chrome_devtools_config():
    # Return empty response to suppress Chrome DevTools 404 warnings
    from fastapi.responses import Response
    return Response(status_code=204)

@app.get("/", response_class=HTMLResponse)
def read_root():
    # Check if user is logged in by serving landing page or redirecting
    template_path = os.path.join(os.path.dirname(__file__), "templates", "landing.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/motors-page", response_class=HTMLResponse)
def motors_page():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "motors.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/motor/{motor_id}", response_class=HTMLResponse)
def motor_detail_page(motor_id: str):
    template_path = os.path.join(os.path.dirname(__file__), "templates", "motor_detail.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/manage-users", response_class=HTMLResponse)
def manage_users_page():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "users.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/login-page", response_class=HTMLResponse)
def login_page():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "login.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()