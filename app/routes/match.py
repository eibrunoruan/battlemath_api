from flask import Blueprint, request, jsonify
from app import db
from app.auth import token_required
from app.models import Game, Client
from app.routes import game
from app.services import game_logic
import time

bp = Blueprint('match', __name__, url_prefix='/match')

active_matches = {}

@bp.route('/join', methods=['POST'])
@token_required
def join_game(current_user):
    data = request.get_json() or {}
    game_id = data.get('game_id')

    if not game_id:
        return jsonify({'error': 'game_id is required'}), 400

    game = Game.query.get(game_id)
    if not game or game.status != 'waiting':
        return jsonify({'error': 'Invalid or already started game'}), 400

    game.player_2_id = current_user.id
    game.status = 'in_progress'
    db.session.commit()

    active_matches[game_id] = {
        'users': {
            game.player_1_id: {'time_left': 60, 'correct': 0, 'wrong': 0},
            game.player_2_id: {'time_left': 60, 'correct': 0, 'wrong': 0}
        },
        'start_time': time.time(),
        'categories': game.categories.split(',') if game.categories else [],
        'last_active': {
            game.player_1_id: time.time(),
            game.player_2_id: time.time()
        }
    }

    return jsonify({'message': 'Joined game', 'game_id': game_id}), 200

@bp.route('/start', methods=['POST'])
@token_required
def start_game(current_user):
    data = request.get_json() or {}
    game_id = data.get('game_id')
    categories = data.get('categories', [])

    if game_id not in active_matches:
        return jsonify({'error': 'Game not found'}), 404

    match = active_matches[game_id]
    match['categories'] = categories
    match['start_time'] = time.time()

    return jsonify({'message': 'Game started'}), 200

@bp.route('/question', methods=['GET'])
@token_required
def request_question(current_user):
    game_id = request.args.get('game_id')
    if game_id not in active_matches:
        return jsonify({'error': 'Game not found'}), 404

    match = active_matches[game_id]
    question = game_logic.generate_question(match.get('categories', []))
    if question:
        return jsonify(question), 200
    return jsonify({'error': 'No question available'}), 400

@bp.route('/answer', methods=['POST'])
@token_required
def answer_question(current_user):
    data = request.get_json() or {}
    game_id = data.get('game_id')
    question_id = data.get('question_id')
    answer = data.get('answer')

    if not all([game_id, question_id, answer]):
        return jsonify({'error': 'Incomplete answer data'}), 400

    if game_id not in active_matches:
        return jsonify({'error': 'Game not active'}), 404

    match = active_matches[game_id]
    user_data = match['users'].get(current_user.id)

    if not user_data:
        return jsonify({'error': 'User not part of the match'}), 403

    if time.time() - match['last_active'][current_user.id] > 15:
        user_data['time_left'] -= 1
        user_data['wrong'] += 1

    match['last_active'][current_user.id] = time.time()

    correct = game_logic.validate_answer(question_id, answer)

    if correct:
        user_data['time_left'] += 2
        user_data['correct'] += 1

        # Penaliza o oponente
        opponent_id = game.player_1_id if current_user.id == game.player_2_id else game.player_2_id
        opponent_data = match['users'].get(opponent_id)
        if opponent_data:
            opponent_data['time_left'] -= 2
    else:
        user_data['time_left'] -= 1
        user_data['wrong'] += 1

    if user_data['time_left'] <= 0:
        return jsonify({'message': 'Game over. You ran out of time.'}), 400

    return jsonify({
        'time_left': user_data['time_left'],
        'correct': user_data['correct'],
        'wrong': user_data['wrong']
    }), 200

@bp.route('/finish', methods=['POST'])
@token_required
def manual_finish(current_user):
    data = request.get_json() or {}
    game_id = data.get('game_id')
    loser_id = data.get('loser_id')

    return finish_game_logic(game_id, loser_id=loser_id)

def finish_game_logic(game_id, loser_id):
    match = active_matches.get(game_id)
    if not match:
        return jsonify({'error': 'Match not found'}), 404

    game = Game.query.get(game_id)
    if not game or game.status == 'finished':
        return jsonify({'message': 'Already finalized'}), 200

    total_time = int(time.time() - match['start_time'])
    stats_list = []
    for uid, data in match['users'].items():
        stats_list.append({
            'player_id': uid,
            'correct_answers': data['correct'],
            'wrong_answers': data['wrong'],
            'time_played': 60 - data['time_left'] if data['time_left'] >= 0 else 60,
            'result': 'lose' if int(uid) == int(loser_id) else 'win'
        })

    game_logic.finalize_game(
        game=game,
        stats_list=stats_list,
        total_time=total_time,
        loser_id=loser_id,
        categories=match['categories']
    )

    del active_matches[game_id]
    return jsonify({'message': 'Game finalized'}), 200
