from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_premium = db.Column(db.Boolean, default=False)
    
    # 관계
    algorithms = db.relationship('Algorithm', backref='user', lazy=True)
    ratings = db.relationship('Rating', backref='user', lazy=True)

class Algorithm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)  # easy, medium, hard
    code = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    time_complexity = db.Column(db.String(100))
    space_complexity = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    ratings = db.relationship('Rating', backref='algorithm', lazy=True, cascade='all, delete-orphan')

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    algorithm_id = db.Column(db.Integer, db.ForeignKey('algorithm.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 점수
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 복합 유니크 제약조건 (한 사용자는 한 알고리즘에 하나의 평점만)
    __table_args__ = (db.UniqueConstraint('user_id', 'algorithm_id'),)

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_type = db.Column(db.String(50), nullable=False)  # basic, premium
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    stripe_subscription_id = db.Column(db.String(200))
    
    # 관계
    user = db.relationship('User', backref='subscriptions')