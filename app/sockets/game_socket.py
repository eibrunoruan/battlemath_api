from flask_socketio import Namespace, emit, join_room, disconnect
from app import socketio, db
from app.models import Game, Client, GameStats
from app.services import game_logic
import time
import threading

active_rooms = {}
TIMEOUT_LIMIT = 25

class GameNamespace(Namespace):
    def on_connect(self):
        emit('status', {'message': 'Connected to the server.'})

    def on_join(self, data):
        game_id = data.get('game_id')
        user_id = data.get('user_id')

        if not game_id or not user_id:
            return emit('error', {'message': 'Invalid join data.'})

        join_room(game_id)

        if game_id not in active_rooms:
            active_rooms[game_id] = {
                'users': {},
                'start_time': None,
                'categories': [],
                'last_active': {}
            }

        active_rooms[game_id]['users'][user_id] = {
            'connected': True,
            'last_ping': time.time(),
            'time_left': 60,
            'correct': 0,
            'wrong': 0
        }
        active_rooms[game_id]['last_active'][user_id] = time.time()

        emit('user_joined', {'user_id': user_id}, room=game_id)

    def on_ready(self, data):
        game_id = data.get('game_id')
        categories = data.get('categories', [])

        if game_id in active_rooms:
            active_rooms[game_id]['start_time'] = time.time()
            active_rooms[game_id]['categories'] = categories
            emit('game_started', {'message': 'Game started'}, room=game_id)

    def on_request_question(self, data):
        game_id = data.get('game_id')
        if game_id in active_rooms:
            categories = active_rooms[game_id].get('categories', [])
            question = game_logic.generate_question(categories)
            if question:
                emit('new_question', question, room=game_id)
            else:
                emit('error', {'message': 'No question found for selected categories.'}, room=game_id)

    def on_answer(self, data):
        game_id = data.get('game_id')
        user_id = data.get('user_id')
        question_id = data.get('question_id')
        answer = data.get('answer')

        if not all([game_id, user_id, question_id, answer]):
            return emit('error', {'message': 'Incomplete answer data.'})

        if game_id in active_rooms and user_id in active_rooms[game_id]['users']:
            user = active_rooms[game_id]['users'][user_id]
            active_rooms[game_id]['last_active'][user_id] = time.time()
            correct = game_logic.validate_answer(question_id, answer)

            if correct:
                user['time_left'] += 2
                user['correct'] += 1
            else:
                user['time_left'] -= 1
                user['wrong'] += 1

            emit('state_update', {
                'user_id': user_id,
                'time_left': user['time_left'],
                'correct': user['correct'],
                'wrong': user['wrong']
            }, room=game_id)

            if user['time_left'] <= 0:
                emit('game_over', {'loser_id': user_id}, room=game_id)
                self._finalize_game(game_id, loser_id=user_id)

    def on_disconnect(self):
        disconnect()

    def _finalize_game(self, game_id, loser_id):
        if game_id not in active_rooms:
            return

        users = active_rooms[game_id]['users']
        categories = active_rooms[game_id]['categories']
        game = Game.query.get(game_id)
        if not game:
            return

        game.status = 'finished'
        game.categories = ','.join(categories)
        game.winner_id = next((uid for uid in users if uid != loser_id), None)
        game.total_time = int(time.time() - active_rooms[game_id]['start_time'])

        for user_id, data in users.items():
            stats = GameStats(
                game_id=game.id,
                player_id=user_id,
                correct_answers=data['correct'],
                wrong_answers=data['wrong'],
                time_played=60 - data['time_left'] if data['time_left'] >= 0 else 60,
                result='lose' if user_id == loser_id else 'win'
            )
            db.session.add(stats)
            player = Client.query.get(user_id)
            if user_id == loser_id:
                player.points -= 21
            else:
                player.points += 31

        db.session.commit()
        del active_rooms[game_id]

def check_timeouts():
    while True:
        now = time.time()
        for game_id, room in list(active_rooms.items()):
            for user_id, last_seen in list(room['last_active'].items()):
                if now - last_seen > TIMEOUT_LIMIT:
                    emit('game_over', {'loser_id': user_id}, room=game_id)
                    GameNamespace()._finalize_game(game_id, loser_id=user_id)
                    break
        time.sleep(5)

threading.Thread(target=check_timeouts, daemon=True).start()
socketio.on_namespace(GameNamespace('/ws/game'))
