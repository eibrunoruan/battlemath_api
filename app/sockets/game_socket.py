import os, time, json, jwt, redis
from flask import request, session, current_app
from flask_socketio import Namespace, emit, join_room
from app import socketio
from app.models import Game, Client
from app.services import game_logic

r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
sid_to_user = {}
TIMEOUT_LIMIT = 25


def _room_key(game_id):
    return f'room:{game_id}'


def _get_room(game_id):
    data = r.get(_room_key(game_id))
    return json.loads(data) if data else None


def _save_room(game_id, room):   # persist room dict
    r.setex(_room_key(game_id), 3600, json.dumps(room))


class GameNamespace(Namespace):
    def on_connect(self):
        raw = request.args.get('token') or request.headers.get('Authorization')
        if not raw:
            return False
        if raw.startswith('Bearer '):
            raw = raw.split(' ', 1)[1]
        try:
            payload = jwt.decode(raw, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            user = Client.query.get(payload['user'])
            if not user:
                return False
        except jwt.ExpiredSignatureError:
            return False
        except Exception:
            return False
        session['user_id'] = user.id
        sid_to_user[request.sid] = user.id
        emit('status', {'message': f'Connected as {user.username}', 'user_id': user.id})

    def on_join(self, data):
        game_id = data.get('game_id')
        user_id = session.get('user_id')
        if not game_id:
            return emit('error', {'message': 'game_id is required.'})
        join_room(game_id)

        room = _get_room(game_id) or {
            'users': {},
            'start_time': None,
            'categories': [],
            'last_active': {}
        }
        room['users'][user_id] = {
            'connected': True,
            'last_ping': time.time(),
            'time_left': 60,
            'correct': 0,
            'wrong': 0
        }
        room['last_active'][user_id] = time.time()
        _save_room(game_id, room)
        emit('user_joined', {'user_id': user_id}, room=game_id)

    def on_ready(self, data):
        game_id = data.get('game_id')
        categories = data.get('categories', [])
        room = _get_room(game_id)
        if room:
            room['start_time'] = time.time()
            room['categories'] = categories
            _save_room(game_id, room)
            emit('game_started', {'message': 'Game started'}, room=game_id)

    def on_request_question(self, data):
        game_id = data.get('game_id')
        room = _get_room(game_id)
        if room:
            question = game_logic.generate_question(room.get('categories', []))
            if question:
                emit('new_question', question, room=game_id)
            else:
                emit('error', {'message': 'No question found for selected categories.'}, room=game_id)

    def on_answer(self, data):
        game_id, question_id, answer = data.get('game_id'), data.get('question_id'), data.get('answer')
        user_id = session.get('user_id')
        if not all([game_id, question_id, answer]):
            return emit('error', {'message': 'Incomplete answer data.'})

        room = _get_room(game_id)
        if room and user_id in room['users']:
            user = room['users'][user_id]
            room['last_active'][user_id] = time.time()
            correct = game_logic.validate_answer(question_id, answer)
            if correct:
                user['time_left'] += 2
                user['correct'] += 1
            else:
                user['time_left'] -= 1
                user['wrong'] += 1
            _save_room(game_id, room)

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
        user_id = sid_to_user.pop(request.sid, None)
        if not user_id:
            return
        for key in r.scan_iter('room:*'):
            game_id = key.decode().split(':', 1)[1]
            room = _get_room(game_id)
            if room and user_id in room['users']:
                emit('game_over', {'loser_id': user_id}, room=game_id)
                self._finalize_game(game_id, loser_id=user_id)
                break

    def _finalize_game(self, game_id, loser_id):
        room = _get_room(game_id)
        if not room:
            return
        game = Game.query.get(game_id)
        if not game or game.status == 'finished':
            r.delete(_room_key(game_id))
            return

        total_time = int(time.time() - room['start_time'])
        stats_list = []
        for uid, data in room['users'].items():
            stats_list.append({
                'player_id': uid,
                'correct_answers': data['correct'],
                'wrong_answers': data['wrong'],
                'time_played': 60 - data['time_left'] if data['time_left'] >= 0 else 60,
                'result': 'lose' if uid == loser_id else 'win'
            })
        game_logic.finalize_game(
            game=game,
            stats_list=stats_list,
            total_time=total_time,
            loser_id=loser_id,
            categories=room['categories']
        )
        r.delete(_room_key(game_id))

def check_timeouts():
    while True:
        now = time.time()
        for key in r.scan_iter('room:*'):
            game_id = key.decode().split(':', 1)[1]
            room = _get_room(game_id)
            if not room:
                continue
            for uid, last_seen in list(room['last_active'].items()):
                if now - last_seen > TIMEOUT_LIMIT:
                    emit('game_over', {'loser_id': int(uid)}, room=game_id)
                    GameNamespace()._finalize_game(game_id, loser_id=int(uid))
                    break
        socketio.sleep(5)

socketio.start_background_task(check_timeouts)
socketio.on_namespace(GameNamespace('/ws/game'))
