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

class ReviewResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    score: float

    class Config:
        orm_mode = True

class RecommendationBase(BaseModel):
    user_id: int
    recommended_courses: List[int] = []

class RecommendationCreate(RecommendationBase):
    pass

class Recommendation(RecommendationBase):
    id: int

    class Config:
        orm_mode = True

@app.get("/n_users/", response_model=int)
def get_n_users(db: Session = Depends(get_db)):
    return db.query(UserStudent).count()

@app.get("/n_courses/", response_model=int)
def get_n_courses(db: Session = Depends(get_db)):
    return db.query(Course).count()

@app.get("/reviews/", response_model=List[ReviewResponse])
def get_reviews(limit: Optional[int] = Query(10, description="Number of reviews to return"), db: Session = Depends(get_db)):
    reviews = db.query(UserCourse).limit(limit).all()
    return reviews

@app.post("/recommendations/", response_model=Recommendation)
def create_recommendation(recommendation: RecommendationCreate, db: Session = Depends(get_db)):
    db_recommendation = Recommendations(**recommendation.dict())
    db.add(db_recommendation)
    db.commit()
    db.refresh(db_recommendation)
    return db_recommendation

@app.get("/recommendations/user/{user_id}", response_model=List[Recommendation])
def read_recommendations_by_user(user_id: int, db: Session = Depends(get_db)):
    recommendations = db.query(Recommendations).filter(Recommendations.user_id == user_id).all()
    if not recommendations:
        raise HTTPException(status_code=404, detail="No recommendations found for this user")
    return recommendations

@app.get("/recommendations/", response_model=List[Recommendation])
def read_all_recommendations(db: Session = Depends(get_db)):
    return db.query(Recommendations).all()

def train_and_recommend(db: Session, top_k: int = 100):
    logger.info("Starting ALS model training and recommendation generation.")
    try:
        als_recommender.train(db)
        als_recommender.recommend(db, top_k)
    except Exception as e:
        logger.error(f"Error during ALS model training or recommendation generation: {e}")

schedule.every().day.at("00:00").do(lambda: train_and_recommend(next(get_db()), top_k=100))

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
    train_and_recommend(db, top_k=100)