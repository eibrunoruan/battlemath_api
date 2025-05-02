import random
from typing import List, Dict, Optional
from sqlalchemy.sql import func
from app import db
from app.models import Question, Game, GameStats, Client

def generate_question(categories: List[str]) -> Optional[dict]:
    question = (
        Question.query
        .filter(Question.category.in_(categories))
        .order_by(func.random())
        .first()
    )
    if not question:
        return None

    return {
        'id': question.id,
        'category': question.category,
        'text': question.text,
        'options': {
            'A': question.option_a,
            'B': question.option_b,
            'C': question.option_c,
            'D': question.option_d
        }
    }


def validate_answer(question_id: int, selected_option: str) -> bool:
    question = Question.query.get(question_id)
    if not question:
        return False
    return selected_option.upper() == question.correct_option.upper()

_POINTS = {'win': 31, 'lose': -21, 'draw': 10}


def apply_points(player: Client, result: str) -> None:
    player.points += _POINTS.get(result, 0)


def finalize_game(
    game: Game,
    stats_list: List[Dict],
    total_time: int,
    winner_id: Optional[int] = None,
    loser_id: Optional[int] = None,
    categories: Optional[List[str]] = None
) -> None:
    game.status = 'finished'
    game.total_time = total_time
    if categories:
        game.categories = ','.join(categories)
    if winner_id:
        game.winner_id = winner_id
    elif loser_id:
        game.winner_id = next((s['player_id'] for s in stats_list
                               if s['player_id'] != loser_id), None)

    for s in stats_list:
        gs = GameStats(
            game_id=game.id,
            player_id=s['player_id'],
            correct_answers=s['correct_answers'],
            wrong_answers=s['wrong_answers'],
            time_played=s['time_played'],
            result=s['result']
        )
        db.session.add(gs)

        player = Client.query.get(s['player_id'])
        apply_points(player, s['result'])

    db.session.commit()
