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
    def __init__(self, factors=110, iterations=20, regularization=0.01, random_state=42, negatives_discount=0.8):
        """
        Initialize the ALSRecommender.

        Args:
            factors (int): Number of latent factors.
            iterations (int): Number of ALS iterations.
            regularization (float): Regularization parameter.
            random_state (int): Seed for reproducibility.
            negatives_discount (float): Discount factor for negatively (deleted form favs) interacted items.
        """
        self.factors = factors
        self.iterations = iterations
        self.regularization = regularization
        self.random_state = random_state
        self.negatives_discount = negatives_discount
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
        scores = [review.score if review.score > 0 else 0 for review in reviews]

        user_item_matrix = csr_matrix((scores, (user_indices, item_indices)), shape=(len(unique_users), len(unique_courses)))

        # Initialize and train the ALS model
        self.model = implicit.als.AlternatingLeastSquares(factors=self.factors,
                                                          iterations=self.iterations,
                                                          regularization=self.regularization,
                                                          random_state=self.random_state)
        self.model.fit(user_item_matrix)

    def recommend(self, db: Session, top_k: int = 100, batch_size: int = 3000):
        """
        Recommend top-k items for all users using the trained ALS model.

        Args:
            db (Session): SQLAlchemy database session.
            top_k (int): The number of items to recommend.
            batch_size (int): The number of users to process in each batch.
        """
        # Get the set of current user IDs from the mapper
        current_user_ids = set(self.user_to_index.keys())

        # Query the database for all user IDs with existing recommendations
        existing_user_ids = {
            user_id for user_id, in db.query(Recommendations.user_id).all()
        }

        # Find user IDs that are in the database but not in the current mapper
        users_to_delete = existing_user_ids - current_user_ids

        # Delete recommendations for users not in the current mapper
        db.query(Recommendations).filter(Recommendations.user_id.in_(users_to_delete)).delete(synchronize_session=False)

        user_ids = list(self.user_to_index.keys())
        item_factors = self.model.item_factors

        for start_idx in tqdm(range(0, len(user_ids), batch_size)):
            end_idx = min(start_idx + batch_size, len(user_ids))
            batch_user_ids = user_ids[start_idx:end_idx]
            batch_user_indices = [self.user_to_index[user_id] for user_id in batch_user_ids]
            user_factors = self.model.user_factors[batch_user_indices]

            # Compute scores for the batch
            scores = np.dot(user_factors, item_factors.T)

            for i, user_id in enumerate(batch_user_ids):
                user_index = batch_user_indices[i]

                # Get items the user has already interacted with
                user_interacted_items = (
                    db.query(UserCourse)
                    .filter(and_(
                        UserCourse.user_id == user_id,
                        UserCourse.source == "Native"
                    ))
                    .all()
                )
                user_positively_interacted_items = []
                user_negatively_interacted_items = []
                for item in user_interacted_items:
                    if item.score > 0:
                        user_positively_interacted_items.append(self.item_to_index[item.course_id])
                    elif item.score < 0:
                        user_negatively_interacted_items.append(self.item_to_index[item.course_id])

                # Discount negatively interacted items
                mask = np.zeros(scores.shape[1], dtype=bool)
                mask[user_negatively_interacted_items] = True
                scores[i, mask] *= self.negatives_discount

                # Get top-k recommendations
                tmp_top_k = top_k + len(user_positively_interacted_items)
                top_k_indices = np.argpartition(scores[i], -tmp_top_k)[-tmp_top_k:]
                top_k_items = [self.index_to_item[idx] for idx in top_k_indices if idx not in user_positively_interacted_items]

                # Insert new recommendations into the database
                new_recommendation = Recommendations(user_id=user_id, recommended_courses=top_k_items[:top_k])
                db.add(new_recommendation)

            db.commit()
