from flask import render_template, redirect, make_response
from flask_jwt_extended import jwt_required, create_access_token
from utils.helpers import get_current_user
from . import achievements_bp


@achievements_bp.route('/')
@jwt_required()
def achievements():
    user = get_current_user()
    if not user:
        return redirect('/auth/login')

    # Calculate achievements and progress
    user.calculate_achievements()

    # Define achievement tiers and their point requirements
    achievement_tiers = {
        'Beginner': 100,
        'Intermediate': 500,
        'Advanced': 1000,
        'Expert': 5000,
        'Master': 10000
    }

    # Calculate current tier and progress
    current_points = user.exercise_points
    current_tier = None
    next_tier = None
    progress = 0

    # Find current and next tier
    previous_threshold = 0
    for tier, threshold in achievement_tiers.items():
        if current_points < threshold:
            next_tier = {'name': tier, 'threshold': threshold}
            if current_tier:
                # Calculate progress to next tier
                tier_difference = threshold - previous_threshold
                points_progress = current_points - previous_threshold
                progress = (points_progress / tier_difference) * 100
            break
        current_tier = {'name': tier, 'threshold': threshold}
        previous_threshold = threshold

    # If user has reached the highest tier
    if not next_tier:
        progress = 100

    achievements_data = [
        {
            'name': a.name,
            'description': a.description,
            'unlocked_at': a.unlocked_at,
            'threshold': achievement_tiers.get(a.name, 0)
        }
        for a in user.achievements
    ]

    response = make_response(render_template(
        'achievements.html',
        user=user,
        achievements=achievements_data,
        current_tier=current_tier,
        next_tier=next_tier,
        progress=progress
    ))
    new_token = create_access_token(identity=user.id)
    response.set_cookie(
        'access_token_cookie',
        new_token,
        httponly=True,
        secure=True,
        samesite='Lax',
        max_age=900  # 15 minutes
    )
    return response
