from datetime import datetime
from app import db

client_badges = db.Table('client_badges',
    db.Column('client_id', db.Integer, db.ForeignKey('client.id'), primary_key=True),
    db.Column('badge_id', db.Integer, db.ForeignKey('badge.id'), primary_key=True)
)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(100), default='static/icons/default.png')
    username = db.Column(db.String(100), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password = db.Column(db.String(512), nullable=False)
    points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)

    badges = db.relationship('Badge', secondary=client_badges, backref='clients', lazy='dynamic')
    games_as_player1 = db.relationship('Game', foreign_keys='Game.player_1_id', backref='player_1', lazy=True)
    games_as_player2 = db.relationship('Game', foreign_keys='Game.player_2_id', backref='player_2', lazy=True)
    wins = db.relationship('Game', foreign_keys='Game.winner_id', backref='winner', lazy=True)
    stats = db.relationship('GameStats', backref='player', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'username': self.username,
            'email': self.email,
            'points': self.points,
            'created_at': self.created_at.isoformat(),
            'badges': [badge.to_dict() for badge in self.badges]
        }

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    icon = db.Column(db.String(255), default='static/badges/default.png')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon
        }

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_1_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    player_2_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=True)
    winner_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=True)
    status = db.Column(db.String(20), default='waiting')
    categories = db.Column(db.String(200), nullable=False)
    total_time = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    stats = db.relationship('GameStats', backref='game', lazy=True)

class GameStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)

    correct_answers = db.Column(db.Integer, default=0)
    wrong_answers = db.Column(db.Integer, default=0)
    time_played = db.Column(db.Integer, default=0)
    result = db.Column(db.String(10))

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    text = db.Column(db.String(255), nullable=False)
    option_a = db.Column(db.String(100), nullable=False)
    option_b = db.Column(db.String(100), nullable=False)
    option_c = db.Column(db.String(100), nullable=False)
    option_d = db.Column(db.String(100), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)  # A, B, C, or D
