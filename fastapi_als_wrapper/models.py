from sqlalchemy import (
    Column, Integer, Float, String, ForeignKey, DateTime, Boolean, Text, Table, CheckConstraint, Enum
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime


Base = declarative_base()


class UserStudent(Base):
    __tablename__ = 'recs_api_userstudent'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(150), unique=True, nullable=False)
    email = Column(String(254), unique=True, nullable=False)
    password = Column(String(128), nullable=False)
    courses = relationship('Course', secondary='recs_api_usercourse', back_populates='users')


class Course(Base):
    __tablename__ = 'recs_api_course'

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform_id = Column(Integer, nullable=False)
    platform_course_id = Column(Integer, nullable=True)
    title = Column(String(255), nullable=False)
    language = Column(String(255), nullable=True)
    workload = Column(String(255), nullable=True)
    canonical_url = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    became_published_at = Column(DateTime, nullable=False)
    time_to_complete = Column(Integer, nullable=True)
    is_paid = Column(Boolean, nullable=False)
    category = Column(String(255), nullable=True)
    date_added = Column(DateTime, default=datetime.utcnow)

    users = relationship('UserStudent', secondary='recs_api_usercourse', back_populates='courses')
    
    
class UserCourse(Base):
    __tablename__ = 'recs_api_usercourse'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('recs_api_userstudent.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('recs_api_course.id'), nullable=False)
    source = Column(Enum('Native', 'External', name='source_enum'), nullable=False)
    date_added = Column(DateTime, default=datetime.utcnow)
    score = Column(Float, default=1)

    __table_args__ = (
        CheckConstraint(
            "source IN ('Native', 'External')",
            name='valid_source_check',
        ),
    )
    

class Recommendations(Base):
    __tablename__ = "recs_api_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('recs_api_userstudent.id'), nullable=False)
    recommended_courses = Column(ARRAY(Integer), default=[])
