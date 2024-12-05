from flask import Blueprint

bp = Blueprint('ward_admin', __name__)

from app.ward_admin import routes 