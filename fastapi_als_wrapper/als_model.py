import implicit
import numpy as np
from scipy.sparse import csr_matrix
from tqdm import tqdm
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models import Course, UserCourse, UserStudent, Recommendations
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ALSRecommender:
    def __init__(self, factors=110, iterations=20, regularization=0.01, random_state=42):
        """
        Initialize the ALSRecommender.

        Args:
            factors (int): Number of latent factors.
            iterations (int): Number of ALS iterations.
            regularization (float): Regularization parameter.
            random_state (int): Seed for reproducibility.
        """
        self.factors = factors
        self.iterations = iterations
        self.regularization = regularization
        self.random_state = random_state
        self.model = None
        self.item_catalog = None
        self.item_to_index = None
        self.index_to_item = None
        self.user_to_index = None
        self.index_to_user = None

    def train(self, db: Session):
        """
        Train the ALS model using the training data from the reviews table.

        Args:
            db (Session): SQLAlchemy database session.
        """
        # Query data
        reviews = db.query(UserCourse).all()

        # Create unique sets of users and courses from reviews
        unique_users = set()
        unique_courses = set()
        for review in reviews:
            unique_users.add(review.user_id)
            unique_courses.add(review.course_id)

        # Create mappings
        self.item_catalog = list(unique_courses)
        self.item_to_index = {item: idx for idx, item in enumerate(self.item_catalog)}
        self.index_to_item = {idx: item for idx, item in enumerate(self.item_catalog)}

        self.user_to_index = {user: idx for idx, user in enumerate(unique_users)}
        self.index_to_user = {idx: user for idx, user in enumerate(unique_users)}

        # Create user-item interaction matrix
        user_indices = [self.user_to_index[review.user_id] for review in reviews]
        item_indices = [self.item_to_index[review.course_id] for review in reviews]
        scores = [review.score for review in reviews]

        user_item_matrix = csr_matrix((scores, (user_indices, item_indices)),
                                      shape=(len(unique_users), len(unique_courses)))

        # Initialize and train the ALS model
        self.model = implicit.als.AlternatingLeastSquares(factors=self.factors,
                                                          iterations=self.iterations,
                                                          regularization=self.regularization,
                                                          random_state=self.random_state)
        self.model.fit(user_item_matrix)

    def recommend(self, db: Session, top_k: int = 10):
        """
        Recommend top-k items for all users using the trained ALS model.

        Args:
            db (Session): SQLAlchemy database session.
            top_k (int): The number of items to recommend.
        """
        recommendations = {}
        user_ids = list(self.user_to_index.keys())

        for user_id in tqdm(user_ids):
            # Get the user index
            user_index = self.user_to_index[user_id]

            # Get items the user has already interacted with (from training data)
            user_interacted_items = (
                db.query(UserCourse.course_id)
                .filter(and_(
                    UserCourse.user_id == user_id,
                    UserCourse.source == "Native"
                ))
                .all()
            )
            user_interacted_items = [item.course_id for item in user_interacted_items]

            # Generate recommendations using the ALS model
            recommended_items, _ = self.model.recommend(user_index,
                                                      self.model.user_factors,
                                                      N=top_k + len(user_interacted_items),
                                                      filter_already_liked_items=False)

            # Convert recommended item indices to item IDs
            recommended_items = [self.index_to_item[idx] for idx in recommended_items
                                if self.index_to_item[idx] not in user_interacted_items][:top_k]

            recommendations[user_id] = recommended_items

            # Update recommendations in the database
            existing_recommendation = db.query(Recommendations).filter(Recommendations.user_id == user_id).first()
            if existing_recommendation:
                existing_recommendation.recommended_courses = recommended_items
            else:
                new_recommendation = Recommendations(user_id=user_id, recommended_courses=recommended_items)
                db.add(new_recommendation)

        db.commit()
        logger.info("Recommendations updated successfully.")
