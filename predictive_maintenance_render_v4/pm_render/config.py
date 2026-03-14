# config.py — Render-ready Configuration

import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'pmapp2024rendersecret')

    # Auto-detect cloud vs local
    if os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT'):
        DATABASE = '/tmp/factory.db'
    else:
        _base = os.path.dirname(os.path.abspath(__file__))
        DATABASE = os.path.join(_base, 'instance', 'factory.db')

    # Flask-Mail
    MAIL_SERVER         = 'smtp.gmail.com'
    MAIL_PORT           = 587
    MAIL_USE_TLS        = True
    MAIL_USERNAME       = os.environ.get('MAIL_USERNAME', 'your_email@gmail.com')
    MAIL_PASSWORD       = os.environ.get('MAIL_PASSWORD', 'your_app_password')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME', 'your_email@gmail.com')
    ALERT_RECIPIENT     = os.environ.get('ALERT_EMAIL',   'maintenance@factory.com')

    # Thresholds
    CRITICAL_FAILURE_PROB = 0.60
    WARNING_FAILURE_PROB  = 0.30

    # Timing
    SIMULATION_INTERVAL_MS = 2000
    DASHBOARD_REFRESH_MS   = 5000
