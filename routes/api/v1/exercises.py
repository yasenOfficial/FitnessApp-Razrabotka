from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func
from models import Exercise, User
from extensions import db
from . import api_v1
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EXERCISE_MULTIPLIERS = {
    "pushup": 0.5,
    "situp": 0.3,
    "squat": 0.4,
    "pullup": 1.0,
    "burpee": 1.5,
    "plank": 0.1,
    "run": 2.0,
}


def validate_exercise_type(exercise_type):
    """Validate exercise type and return error response if invalid."""
    if exercise_type not in EXERCISE_MULTIPLIERS:
        return jsonify({"code": 400, "message": "Invalid exercise type"}), 400
    return None


def validate_exercise_date(date_str):
    """Validate exercise date and return error response if invalid."""
    try:
        exercise_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        two_days_ago = today - timedelta(days=2)
        if exercise_date > today or exercise_date < two_days_ago:
            return (
                jsonify(
                    {
                        "code": 400,
                        "message": "Date must be between today and 2 days ago",
                    }
                ),
                400,
            )
        return exercise_date
    except ValueError:
        return jsonify({"code": 400, "message": "Invalid date format"}), 400


def serialize_exercise(exercise):
    """Serialize exercise object to dictionary."""
    return {
        "id": exercise.id,
        "type": exercise.exercise_type,
        "count": exercise.count,
        "intensity": exercise.intensity,
        "points": exercise.points,
        "date": exercise.date_added.isoformat(),
    }


def calculate_points(exercise_type, count):
    """Calculate points for an exercise."""
    return round(EXERCISE_MULTIPLIERS[exercise_type] * count)


@api_v1.route("/exercises", methods=["GET"])
@jwt_required()
def list_exercises():
    user_id = get_jwt_identity()
    query = Exercise.query.filter_by(user_id=user_id)

    # Apply filters
    exercise_type = request.args.get("type")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    if exercise_type:
        error_response = validate_exercise_type(exercise_type)
        if error_response:
            return error_response
        query = query.filter_by(exercise_type=exercise_type)

    if from_date:
        query = query.filter(
            Exercise.date_added >= datetime.strptime(from_date, "%Y-%m-%d")
        )
    if to_date:
        query = query.filter(
            Exercise.date_added <= datetime.strptime(to_date, "%Y-%m-%d")
        )

    exercises = query.order_by(Exercise.date_added.desc()).all()
    return jsonify([serialize_exercise(ex) for ex in exercises])


@api_v1.route("/exercises", methods=["POST"])
@jwt_required()
def create_exercise():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # logger.info(f"Received exercise submission: {data}")

    if not all(k in data for k in ("type", "count", "date")):
        logger.error("Missing required fields in submission")
        return jsonify({"code": 400, "message": "Missing required fields"}), 400

    error_response = validate_exercise_type(data["type"])
    if error_response:
        # logger.error(f"Invalid exercise type: {data['type']}")
        return error_response

    exercise_date = validate_exercise_date(data["date"])
    if isinstance(exercise_date, tuple):  # Error response
        # logger.error(f"Invalid date: {data['date']}")
        return exercise_date

    points = calculate_points(data["type"], data["count"])
    exercise = Exercise(
        user_id=user_id,
        exercise_type=data["type"],
        count=data["count"],
        intensity=data.get("intensity", 1.0),
        points=points,
        date_added=datetime.combine(exercise_date, datetime.min.time()),
    )

    user = User.query.get(user_id)
    user.exercise_points += points

    db.session.add(exercise)
    db.session.commit()
    
    # logger.info(
    #     f"Successfully saved exercise: type={data['type']}, "
    #     f"count={data['count']}, date={data['date']}, points={points}"
    # )
    return jsonify(serialize_exercise(exercise)), 201


@api_v1.route("/exercises/<exercise_type>/stats", methods=["GET"])
@jwt_required()
def get_exercise_stats(exercise_type):
    # logger.info(f"Fetching stats for exercise type: {exercise_type}")
    
    error_response = validate_exercise_type(exercise_type)
    if error_response:
        # logger.error(f"Invalid exercise type: {exercise_type}")
        return error_response

    user_id = get_jwt_identity()
    days = int(request.args.get("days", 30))

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # logger.info(f"Querying exercises from {start_date} to {end_date}")

    # Get exercise stats from database
    stats = (
        db.session.query(
            func.date(Exercise.date_added).label("date"),
            func.sum(Exercise.count).label("count"),
        )
        .filter(
            Exercise.user_id == user_id,
            Exercise.exercise_type == exercise_type,
            Exercise.date_added >= start_date,
            Exercise.date_added <= end_date,
        )
        .group_by(func.date(Exercise.date_added))
        .order_by(func.date(Exercise.date_added))
        .all()
    )
    
    # logger.info(f"Raw stats from database: {[(str(s.date), s.count) for s in stats]}")

    # Fill in missing dates with zero counts
    date_range = []
    counts = []
    current_date = start_date.date()
    
    # Create dictionary with string dates (they're already strings from the query)
    stats_dict = {str(stat.date): stat.count for stat in stats}
    
    # logger.info("Processing stats:")
    # logger.info(f"Stats dictionary with formatted dates: {stats_dict}")

    while current_date <= end_date.date():
        date_str = current_date.strftime("%Y-%m-%d")
        count = stats_dict.get(date_str, 0)
        found_in_dict = date_str in stats_dict
        logger.info(f"Processing date {date_str}: found in dict: {found_in_dict}, count = {count}")
        date_range.append(date_str)
        counts.append(count)
        current_date += timedelta(days=1)

    # logger.info("Final processed data:")
    # logger.info(f"Dates: {date_range}")
    # logger.info(f"Counts: {counts}")
    # logger.info(f"Non-zero counts: {[c for c in counts if c != 0]}")

    return jsonify({"dates": date_range, "counts": counts})
