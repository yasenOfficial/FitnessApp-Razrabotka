from flask import render_template, send_from_directory
from utils.helpers import get_current_user
from . import main_bp

@main_bp.route('/')
def home():
    return render_template('home.html', user=get_current_user())

@main_bp.route('/static/<path:p>')
def static_serve(p):
    return send_from_directory('static', p) 