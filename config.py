import os

class Config:
    # App configuration
    SECRET_KEY = 'blahblahland_secret_key'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///chat.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'bekbolsunysmanov07@gmail.com'  # Replace with your Gmail address
    MAIL_PASSWORD = 'wdbw xsuu dsaf qkww'     # Replace with your app password
    MAIL_DEFAULT_SENDER = ('BlahBlahLand', 'bekbolsunysmanov07@gmail.com')
    
    # AI API configuration
    OPENROUTER_API_KEY = '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'