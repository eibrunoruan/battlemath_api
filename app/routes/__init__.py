from flask import Blueprint

bp = Blueprint('main', __name__)

from app.routes import badges
from app.routes import clients
from app.routes import match
