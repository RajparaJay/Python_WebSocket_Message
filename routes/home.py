from flask import Blueprint, render_template
from flask_login import login_required

home_bp = Blueprint('home', __name__)


@home_bp.route('/')
@login_required
def index():
    """Home page - main chat interface."""
    return render_template('index.html')


@home_bp.route('/privacy')
def privacy():
    """Privacy policy page."""
    return render_template('privacy.html')
