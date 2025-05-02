import os
from flask_socketio import SocketIO
from app import create_app, db
from app.models import Client, Game, GameStats, Question, Badge

# ── SocketIO / Redis ─────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DEFAULT_MODE = os.getenv("SOCKET_MODE", "eventlet")       # fallback

app = create_app()
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    message_queue=REDIS_URL,
    async_mode=DEFAULT_MODE
)
app.socketio = socketio

# ── Flask shell context ──────────────────────────────────────────
@app.shell_context_processor
def make_shell_context():
    return dict(
        db=db, Client=Client, Game=Game, GameStats=GameStats,
        Question=Question, Badge=Badge
    )

# ── Só roda quando chamado diretamente (python run.py) ───────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=["eventlet", "gevent"],
        default=DEFAULT_MODE,
        help="Backend async: eventlet (padrão) ou gevent."
    )
    parser.add_argument(
        "--workers", type=int, default=1,
        help="Usado apenas quando --mode gevent"
    )
    args = parser.parse_args()

    socketio.async_mode = args.mode          # aplica modo escolhido
    run_opts = dict(debug=True)
    if args.mode == "gevent":
        run_opts["workers"] = args.workers

    socketio.run(app, **run_opts)
