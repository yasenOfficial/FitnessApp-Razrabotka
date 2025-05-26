from flask import render_template, redirect, request, flash, jsonify
from flask_jwt_extended import jwt_required
from extensions import db
from models import Exercise
from models.constants import EXERCISE_RANKS
from utils.helpers import get_current_user
from datetime import datetime, timedelta
from sqlalchemy import func
from . import dashboard_bp


def get_daily_routine():
    """Return the list of exercises with their metadata."""
    return [
        {
            'type': 'pushup',
            'label': 'Push-ups',
            'icon': 'dumbbell',
            'description': 'Targets chest, shoulders, and triceps'
        },
        {
            'type': 'situp',
            'label': 'Sit-ups',
            'icon': 'child',
            'description': 'Strengthens your core and abs'
        },
        {
            'type': 'squat',
            'label': 'Squats',
            'icon': 'walking',
            'description': 'Builds quads and glutes'
        },
        {
            'type': 'pullup',
            'label': 'Pull-ups',
            'icon': 'person-booth',
            'description': 'Works your back and biceps'
        },
        {
            'type': 'burpee',
            'label': 'Burpees',
            'icon': 'running',
            'description': 'Full-body conditioning'
        },
        {
            'type': 'plank',
            'label': 'Plank (sec)',
            'icon': 'hourglass-start',
            'description': 'Core stabilization and endurance'
        },
        {
            'type': 'run',
            'label': 'Running (min)',
            'icon': 'running',
            'description': 'Cardio, legs, and stamina'
        },
    ]


def get_exercise_multipliers():
    """Return the point multipliers for each exercise type."""
    return {
        'pushup': 0.5,
        'situp': 0.3,
        'squat': 0.4,
        'pullup': 1.0,
        'burpee': 1.5,
        'plank': 0.1,
        'run': 2.0
    }


def validate_exercise_date(date_str, today):
    """Validate the exercise date."""
    try:
        exercise_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if exercise_date > today or exercise_date < today - timedelta(days=2):
            return None, 'Invalid date selected. Please choose a date between today and 2 days ago.'
        return exercise_date, None
    except (ValueError, TypeError):
        return None, 'Invalid date format.'


def process_exercise_submission(user, exercise_type, count, date_str):
    """Process a single exercise submission."""
    today = datetime.now().date()
    exercise_date, error = validate_exercise_date(date_str, today)
    if error:
        return False, error

    multipliers = get_exercise_multipliers()
    points = round(multipliers.get(exercise_type, 0.5) * count)
    
    exercise = Exercise(
        user_id=user.id,
        exercise_type=exercise_type,
        count=count,
        intensity=1.0,
        points=points,
        date_added=datetime.combine(exercise_date, datetime.min.time())
    )
    user.exercise_points += points
    db.session.add(exercise)
    return True, None


def get_exercise_ranks(user, daily_routine):
    """Compute per-exercise totals & ranks."""
    per_ex_ranks = {}
    for ex in daily_routine:
        total = db.session.query(db.func.sum(Exercise.count)) \
            .filter_by(user_id=user.id, exercise_type=ex['type']) \
            .scalar() or 0

        for thresh, name in EXERCISE_RANKS[ex['type']]:
            if total >= thresh:
                per_ex_ranks[ex['type']] = {'total': total, 'rank': name}
                break
    return per_ex_ranks


@dashboard_bp.route('/api/exercise-stats/<exercise_type>')
@jwt_required()
def exercise_stats(exercise_type):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    # Get the last 30 days of data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    # Query exercise data grouped by date
    stats = db.session.query(
        func.date(Exercise.date_added).label('date'),
        func.sum(Exercise.count).label('count')
    ).filter(
        Exercise.user_id == user.id,
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


@dashboard_bp.route('/', methods=['GET', 'POST'])
@jwt_required()
def dashboard():
    user = get_current_user()
    if not user:
        return redirect('/auth/login')

    daily_routine = get_daily_routine()
    today = datetime.now().date()
    available_dates = [today - timedelta(days=i) for i in range(2, -1, -1)]

    if request.method == 'POST':
        logged_any = False
        error = None

        for ex in daily_routine:
            count = int(request.form.get(ex['type'], 0))
            if count > 0:
                date_str = request.form.get(f"{ex['type']}_date")
                success, error = process_exercise_submission(user, ex['type'], count, date_str)
                if not success:
                    flash(error, 'error')
                    return redirect('/dashboard')
                logged_any = True

        if logged_any:
            db.session.commit()
            user.calculate_achievements()
        else:
            flash('Enter at least one exercise count.', 'warning')

        return redirect('/dashboard')

    per_ex_ranks = get_exercise_ranks(user, daily_routine)

    return render_template(
        'dashboard.html',
        user=user,
        daily_routine=daily_routine,
        per_ex_ranks=per_ex_ranks,
        available_dates=available_dates
    )
