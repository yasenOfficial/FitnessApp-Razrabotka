from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func
from models import Exercise, User
from extensions import db
from . import api_v1

EXERCISE_MULTIPLIERS = {
    'pushup': 0.5,
    'situp': 0.3,
    'squat': 0.4,
    'pullup': 1.0,
    'burpee': 1.5,
    'plank': 0.1,
    'run': 2.0
}

@api_v1.route('/exercises', methods=['GET'])
@jwt_required()
def list_exercises():
    user_id = get_jwt_identity()
    query = Exercise.query.filter_by(user_id=user_id)
    
    # Apply filters
    exercise_type = request.args.get('type')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    if exercise_type:
        query = query.filter_by(exercise_type=exercise_type)
    if from_date:
        query = query.filter(Exercise.date_added >= datetime.strptime(from_date, '%Y-%m-%d'))
    if to_date:
        query = query.filter(Exercise.date_added <= datetime.strptime(to_date, '%Y-%m-%d'))
    
    exercises = query.order_by(Exercise.date_added.desc()).all()
    
    return jsonify([{
        'id': ex.id,
        'type': ex.exercise_type,
        'count': ex.count,
        'intensity': ex.intensity,
        'points': ex.points,
        'date': ex.date_added.isoformat()
    } for ex in exercises])

@api_v1.route('/exercises', methods=['POST'])
@jwt_required()
def create_exercise():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not all(k in data for k in ('type', 'count', 'date')):
        return jsonify({'code': 400, 'message': 'Missing required fields'}), 400
    
    if data['type'] not in EXERCISE_MULTIPLIERS:
        return jsonify({'code': 400, 'message': 'Invalid exercise type'}), 400
    
    try:
        exercise_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        if exercise_date > datetime.now().date() or exercise_date < datetime.now().date() - timedelta(days=2):
            return jsonify({'code': 400, 'message': 'Date must be between today and 2 days ago'}), 400
    except ValueError:
        return jsonify({'code': 400, 'message': 'Invalid date format'}), 400
    
    points = round(EXERCISE_MULTIPLIERS[data['type']] * data['count'])
    exercise = Exercise(
        user_id=user_id,
        exercise_type=data['type'],
        count=data['count'],
        intensity=data.get('intensity', 1.0),
        points=points,
        date_added=datetime.combine(exercise_date, datetime.min.time())
    )
    
    user = User.query.get(user_id)
    user.exercise_points += points
    
    db.session.add(exercise)
    db.session.commit()
    
    return jsonify({
        'id': exercise.id,
        'type': exercise.exercise_type,
        'count': exercise.count,
        'intensity': exercise.intensity,
        'points': exercise.points,
        'date': exercise.date_added.isoformat()
    }), 201

@api_v1.route('/exercises/<exercise_type>/stats', methods=['GET'])
@jwt_required()
def get_exercise_stats(exercise_type):
    if exercise_type not in EXERCISE_MULTIPLIERS:
        return jsonify({'code': 400, 'message': 'Invalid exercise type'}), 400
    
    user_id = get_jwt_identity()
    days = int(request.args.get('days', 30))
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    stats = db.session.query(
        func.date(Exercise.date_added).label('date'),
        func.sum(Exercise.count).label('count')
    ).filter(
        Exercise.user_id == user_id,
        Exercise.exercise_type == exercise_type,
        Exercise.date_added >= start_date,
        Exercise.date_added <= end_date
    ).group_by(
        func.date(Exercise.date_added)
    ).order_by(
        func.date(Exercise.date_added)
    ).all()
    
    # Create a complete date range with zeros for missing dates
    date_range = []
    counts = []
    current_date = start_date.date()
    stats_dict = {stat.date: stat.count for stat in stats}
    
    while current_date <= end_date.date():
        date_range.append(current_date.strftime('%Y-%m-%d'))
        counts.append(stats_dict.get(current_date, 0))
        current_date += timedelta(days=1)
    
    return jsonify({
        'dates': date_range,
        'counts': counts
    }) 