from flask import render_template, redirect, request, flash
from flask_jwt_extended import jwt_required
from extensions import db
from models import Exercise
from models.constants import EXERCISE_RANKS
from utils.helpers import get_current_user
from . import dashboard_bp

@dashboard_bp.route('/', methods=['GET', 'POST'])
@jwt_required()
def dashboard():
    user = get_current_user()
    if not user:
        return redirect('/auth')

    # Exercise definitions with icons and descriptions
    daily_routine = [
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

    if request.method == 'POST':
        logged_any = False
        for ex in daily_routine:
            count = int(request.form.get(ex['type'], 0))
            if count > 0:
                multipliers = {
                    'pushup': 0.5,
                    'situp': 0.3,
                    'squat': 0.4,
                    'pullup': 1.0,
                    'burpee': 1.5,
                    'plank': 0.1,
                    'run': 2.0
                }
                points = round(multipliers.get(ex['type'], 0.5) * count)
                exercise = Exercise(
                    user_id=user.id,
                    exercise_type=ex['type'],
                    count=count,
                    intensity=1.0,
                    points=points
                )
                user.exercise_points += points
                db.session.add(exercise)
                logged_any = True

        if logged_any:
            db.session.commit()
            user.calculate_achievements()
            flash('Exercises logged!', 'success')
        else:
            flash('Enter at least one exercise count.', 'warning')

        return redirect('/dashboard')

    # Compute per-exercise totals & ranks
    per_ex_ranks = {}
    for ex in daily_routine:
        total = db.session.query(db.func.sum(Exercise.count)) \
            .filter_by(user_id=user.id, exercise_type=ex['type']) \
            .scalar() or 0

        # Determine rank based on EXERCISE_RANKS table
        for thresh, name in EXERCISE_RANKS[ex['type']]:
            if total >= thresh:
                per_ex_ranks[ex['type']] = {'total': total, 'rank': name}
                break

    return render_template(
        'dashboard.html',
        user=user,
        daily_routine=daily_routine,
        per_ex_ranks=per_ex_ranks
    ) 