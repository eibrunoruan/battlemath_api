from app.models import Badge, Game, GameStats, Client
from app.models import db

def give_badge(player: Client, badge_name: str) -> None:
    badge = Badge.query.filter_by(name=badge_name).first()
    if badge and badge not in player.badges:
        player.badges.append(badge)

def apply_badge_rules(player: Client, stat: dict):

    if stat['result'] == 'win':
        wins_count = GameStats.query.filter_by(player_id=player.id, result='win').count()
        if wins_count == 1:
            give_badge(player, 'Primeira Vitória')

    if stat['correct_answers'] >= 10:
        give_badge(player, 'Precisão Mortal')

    total_games = Game.query.filter(
        (Game.player_1_id == player.id) | (Game.player_2_id == player.id)
    ).count()
    if total_games == 10:
        give_badge(player, 'Persistente')

    recent_stats = GameStats.query.filter_by(player_id=player.id).order_by(GameStats.id.desc()).limit(5).all()
    if len(recent_stats) == 5 and all(rs.result == 'win' for rs in recent_stats):
        give_badge(player, 'Imbatível')
