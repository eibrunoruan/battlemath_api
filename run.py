import os
from dotenv import load_dotenv
from app import create_app, db
from app.models import Client, Game, GameStats, Question, Badge

load_dotenv()

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return dict(
        db=db, Client=Client, Game=Game, GameStats=GameStats,
        Question=Question, Badge=Badge
    )

if __name__ == "__main__":
    print("Banco configurado:", os.getenv("DATABASE_URL"))
    app.run(debug=True, host="0.0.0.0", port=5000)
