from flask import render_template, send_from_directory, redirect
from utils.helpers import get_current_user
from . import main_bp

@main_bp.route('/')
def index():
    return redirect('/dashboard')

@main_bp.route('/static/<path:p>')
def static_serve(p):
    return send_from_directory('static', p) 