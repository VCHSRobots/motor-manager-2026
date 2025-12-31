from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from .database import get_db
from fastapi.middleware.cors import CORSMiddleware
import backend.app.routers.auth as auth_module
import backend.app.routers.motors as motors_module
from .database import engine
from shared.models import Base
import os
import sys

# Add shared to path for subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

# Create tables
# Base.metadata.create_all(bind=engine)

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

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Simple query to test DB connection
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Motor Dynamometer System</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #333; }
            .container { max-width: 800px; margin: 0 auto; }
            .link { display: block; margin: 10px 0; padding: 10px; background: #f0f0f0; text-decoration: none; color: #333; border-radius: 5px; }
            .link:hover { background: #e0e0e0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Motor Dynamometer System</h1>
            <p>Welcome to the Epic Robots Motor Dynamometer data system. This application allows you to manage motors, run tests, and analyze performance data.</p>
            
            <h2>Quick Links</h2>
            <a class="link" href="/docs">API Documentation</a>
            <a class="link" href="/motors">View Motors</a>
            <a class="link" href="/auth/login">Login</a>
            <a class="link" href="/health">Health Check</a>
            
            <h2>Features</h2>
            <ul>
                <li>Motor management and tracking</li>
                <li>Test run data collection</li>
                <li>Performance analysis and comparison</li>
                <li>Secure authentication</li>
            </ul>
        </div>
    </body>
    </html>
    """