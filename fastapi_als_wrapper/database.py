from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

USER = os.getenv('DB_USER')
PASSWORD = os.getenv('DB_PASSWORD')
HOST = os.getenv('DB_HOST')
PORT = os.getenv('DB_PORT')
NAME = os.getenv('DB_NAME')

load_dotenv()

engine = create_engine(url=f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{NAME}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
