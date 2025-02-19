from flask import render_template, redirect, url_for
from flask_login import current_user
from app.main import bp


@bp.route("/")
@bp.route("/index")
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for("admin.dashboard"))
        elif current_user.is_ward_admin():
            return redirect(url_for("ward_admin.dashboard"))
        elif current_user.is_student:
            return redirect(url_for("student.dashboard"))
    return render_template("main/index.html")
