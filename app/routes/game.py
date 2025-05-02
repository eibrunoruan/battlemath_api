from flask import Blueprint, request, jsonify
from app import db
from app.models import Game, GameStats, Client
from app.auth import token_required

bp = Blueprint('game', __name__)

@bp.route('/game/start', methods=['POST'])
@token_required
def start_game(current_user):
    try:
        data = request.get_json() or {}
        categories = data.get('categories')

        if not categories:
            return jsonify({'error': 'Categories are required'}), 400

        game = Game(
            player_1_id=current_user.id,
            categories=','.join(categories),
            status='waiting'
        )
        db.session.add(game)
        db.session.commit()

        return jsonify({
            'message': 'Game created. Waiting for another player.',
            'game_id': game.id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/game/end', methods=['POST'])
@token_required
def end_game(current_user):
    try:
        data = request.get_json() or {}
        game_id = data.get('game_id')
        stats_list = data.get('stats')

        game = Game.query.get_or_404(game_id)

        if game.status == 'finished':
            return jsonify({'error': 'Game already finished'}), 400

        game.status = 'finished'
        game.total_time = data.get('total_time', 0)
        game.winner_id = data.get('winner_id')

        for stat in stats_list:
            gs = GameStats(
                game_id=game.id,
                player_id=stat['player_id'],
                correct_answers=stat['correct_answers'],
                wrong_answers=stat['wrong_answers'],
                time_played=stat['time_played'],
                result=stat['result']
            )
            db.session.add(gs)

            player = Client.query.get(gs.player_id)
            if gs.result == 'win':
                player.points += 31
            elif gs.result == 'lose':
                player.points -= 21
            elif gs.result == 'draw':
                player.points += 10

        db.session.commit()
        return jsonify({'message': 'Game finished successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/ranking', methods=['GET'])
def get_ranking():
    try:
        top_players = Client.query.order_by(Client.points.desc()).limit(10).all()
        return jsonify([{
            'username': p.username,
            'points': p.points,
            'icon': p.icon
        } for p in top_players]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/clients/<int:id>/history', methods=['GET'])
@token_required
def get_history(current_user, id):
    if current_user.id != id and not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    try:
        stats = GameStats.query.filter_by(player_id=id).all()
        return jsonify([{
            'game_id': s.game_id,
            'correct_answers': s.correct_answers,
            'wrong_answers': s.wrong_answers,
            'time_played': s.time_played,
            'result': s.result
        } for s in stats]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
