import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Database Configuration
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWD = os.getenv("DB_PASSWD")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWD}@{DB_HOST}/{DB_NAME}"

# Create engine and session
engine = create_engine(DATABASE_URI, echo=False, pool_size=10, max_overflow=20)
Session = scoped_session(sessionmaker(bind=engine))
session = Session()

# Base model for ORM
Base = declarative_base()
