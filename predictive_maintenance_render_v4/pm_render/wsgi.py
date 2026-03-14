# wsgi.py — WSGI entry point for Railway deployment
from app import app

if __name__ == "__main__":
    app.run()
