from app import create_app, db, socketio
from app.models import Client, Game, GameStats, Question, Badge

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'Client': Client,
        'Game': Game,
        'GameStats': GameStats,
        'Question': Question,
        'Badge': Badge
    }

if __name__ == '__main__':
    socketio.run(app, debug=True)
