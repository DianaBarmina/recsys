from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from als_model import ALSRecommender
from models import Course, UserCourse, UserStudent, Recommendations
from database import SessionLocal, engine
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import implicit
import numpy as np
from scipy.sparse import coo_matrix, csr_matrix
import schedule
import time
import logging
import threading


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
als_recommender = ALSRecommender()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def train_and_recommend(db: Session, top_k: Optional[int] = None):
    logger.info("Starting ALS model training and recommendation generation.")
    try:
        als_recommender.train(db)
        als_recommender.recommend(db, top_k)
    except Exception as e:
        logger.error(f"Error during ALS model training or recommendation generation: {e}")

schedule.every(1).minutes.do(lambda: train_and_recommend(next(get_db()), top_k=None))

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.start()

@app.on_event("startup")
def startup_event():
    logger.info("Application startup: Training ALS model.")
    db = next(get_db())
    train_and_recommend(db, top_k=None)
