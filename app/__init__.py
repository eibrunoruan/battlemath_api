from flask import Flask, jsonify
from flask_migrate import Migrate
from config import Config
from app.db import db

from app.auth import auth_bp
from app.routes.game import bp as game_bp
from app.routes.clients import bp as clients_bp
from app.routes.match import bp as match_bp

migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(match_bp)

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad Request'}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized'}), 401

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not Found'}), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({'error': 'Internal Server Error'}), 500

    @app.errorhandler(503)
    def service_unavailable(error):
        return jsonify({'error': 'Service Unavailable'}), 503

    return app
