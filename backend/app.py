from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import bcrypt
import openai
from ai_service import AICodeGenerator
from models import db, User, Algorithm, Rating
import json

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///coding_tutor.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-string')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

db.init_app(app)
jwt = JWTManager(app)
CORS(app)

# AI 코드 생성기 초기화
ai_generator = AICodeGenerator(os.getenv('OPENAI_API_KEY'))

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': '사용자명이 이미 존재합니다'}), 400
            
        if User.query.filter_by(email=email).first():
            return jsonify({'error': '이메일이 이미 존재합니다'}), 400
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user = User(username=username, email=email, password=hashed_password)
        
        db.session.add(user)
        db.session.commit()
        
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': '회원가입이 완료되었습니다',
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password):
            access_token = create_access_token(identity=user.id)
            return jsonify({
                'message': '로그인 성공',
                'access_token': access_token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }), 200
        
        return jsonify({'error': '잘못된 사용자명 또는 비밀번호입니다'}), 401
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-algorithm', methods=['POST'])
@jwt_required()
def generate_algorithm():
    try:
        data = request.get_json()
        problem_description = data.get('problem_description')
        language = data.get('language', 'python')
        difficulty = data.get('difficulty', 'medium')
        
        user_id = get_jwt_identity()
        
        # AI로 알고리즘 생성
        result = ai_generator.generate_algorithm(problem_description, language, difficulty)
        
        # 데이터베이스에 저장
        algorithm = Algorithm(
            user_id=user_id,
            title=result['title'],
            description=problem_description,
            language=language,
            difficulty=difficulty,
            code=result['code'],
            explanation=result['explanation'],
            time_complexity=result['time_complexity'],
            space_complexity=result['space_complexity']
        )
        
        db.session.add(algorithm)
        db.session.commit()
        
        return jsonify({
            'algorithm': {
                'id': algorithm.id,
                'title': algorithm.title,
                'description': algorithm.description,
                'language': algorithm.language,
                'difficulty': algorithm.difficulty,
                'code': algorithm.code,
                'explanation': algorithm.explanation,
                'time_complexity': algorithm.time_complexity,
                'space_complexity': algorithm.space_complexity,
                'created_at': algorithm.created_at.isoformat(),
                'average_rating': 0,
                'rating_count': 0
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/algorithms', methods=['GET'])
def get_algorithms():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        language = request.args.get('language')
        difficulty = request.args.get('difficulty')
        sort_by = request.args.get('sort_by', 'created_at')
        
        query = Algorithm.query
        
        if language:
            query = query.filter_by(language=language)
        if difficulty:
            query = query.filter_by(difficulty=difficulty)
            
        if sort_by == 'rating':
            # 평점 순으로 정렬
            query = query.outerjoin(Rating).group_by(Algorithm.id).order_by(
                db.func.coalesce(db.func.avg(Rating.rating), 0).desc()
            )
        else:
            query = query.order_by(Algorithm.created_at.desc())
        
        algorithms = query.paginate(page=page, per_page=per_page, error_out=False)
        
        result = []
        for algo in algorithms.items:
            ratings = Rating.query.filter_by(algorithm_id=algo.id).all()
            avg_rating = sum(r.rating for r in ratings) / len(ratings) if ratings else 0
            
            result.append({
                'id': algo.id,
                'title': algo.title,
                'description': algo.description,
                'language': algo.language,
                'difficulty': algo.difficulty,
                'code': algo.code,
                'explanation': algo.explanation,
                'time_complexity': algo.time_complexity,
                'space_complexity': algo.space_complexity,
                'created_at': algo.created_at.isoformat(),
                'author': algo.user.username,
                'average_rating': round(avg_rating, 1),
                'rating_count': len(ratings)
            })
        
        return jsonify({
            'algorithms': result,
            'total': algorithms.total,
            'pages': algorithms.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/algorithms/<int:algorithm_id>/rate', methods=['POST'])
@jwt_required()
def rate_algorithm(algorithm_id):
    try:
        data = request.get_json()
        rating_value = data.get('rating')
        comment = data.get('comment', '')
        
        if not (1 <= rating_value <= 5):
            return jsonify({'error': '평점은 1-5 사이여야 합니다'}), 400
        
        user_id = get_jwt_identity()
        
        # 기존 평점 확인
        existing_rating = Rating.query.filter_by(
            user_id=user_id, 
            algorithm_id=algorithm_id
        ).first()
        
        if existing_rating:
            existing_rating.rating = rating_value
            existing_rating.comment = comment
        else:
            rating = Rating(
                user_id=user_id,
                algorithm_id=algorithm_id,
                rating=rating_value,
                comment=comment
            )
            db.session.add(rating)
        
        db.session.commit()
        
        return jsonify({'message': '평점이 등록되었습니다'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rankings', methods=['GET'])
def get_rankings():
    try:
        # 평점 기반 랭킹
        algorithms = db.session.query(
            Algorithm,
            db.func.coalesce(db.func.avg(Rating.rating), 0).label('avg_rating'),
            db.func.count(Rating.id).label('rating_count')
        ).outerjoin(Rating).group_by(Algorithm.id).order_by(
            db.text('avg_rating DESC, rating_count DESC')
        ).limit(50).all()
        
        rankings = []
        for i, (algo, avg_rating, rating_count) in enumerate(algorithms, 1):
            if rating_count > 0:  # 평점이 있는 알고리즘만
                rankings.append({
                    'rank': i,
                    'id': algo.id,
                    'title': algo.title,
                    'language': algo.language,
                    'difficulty': algo.difficulty,
                    'author': algo.user.username,
                    'average_rating': round(float(avg_rating), 1),
                    'rating_count': rating_count,
                    'created_at': algo.created_at.isoformat()
                })
        
        return jsonify({'rankings': rankings}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/my-algorithms', methods=['GET'])
@jwt_required()
def get_my_algorithms():
    try:
        user_id = get_jwt_identity()
        algorithms = Algorithm.query.filter_by(user_id=user_id).order_by(
            Algorithm.created_at.desc()
        ).all()
        
        result = []
        for algo in algorithms:
            ratings = Rating.query.filter_by(algorithm_id=algo.id).all()
            avg_rating = sum(r.rating for r in ratings) / len(ratings) if ratings else 0
            
            result.append({
                'id': algo.id,
                'title': algo.title,
                'description': algo.description,
                'language': algo.language,
                'difficulty': algo.difficulty,
                'code': algo.code,
                'explanation': algo.explanation,
                'time_complexity': algo.time_complexity,
                'space_complexity': algo.space_complexity,
                'created_at': algo.created_at.isoformat(),
                'average_rating': round(avg_rating, 1),
                'rating_count': len(ratings)
            })
        
        return jsonify({'algorithms': result}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)