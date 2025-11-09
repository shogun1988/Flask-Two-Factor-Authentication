from flask import Blueprint, render_template
from flask_login import login_required

core_bp = Blueprint("core", __name__)


@core_bp.route("/")
@login_required
def home():
    return render_template("core/index.html")

@core_bp.route("/contact")
@login_required
def contact():
    return render_template("core/contact.html")