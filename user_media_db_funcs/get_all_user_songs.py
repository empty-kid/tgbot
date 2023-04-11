from data import db_session
from data.songs import Song


def get_all_user_songs(user_id):
    db_sess = db_session.create_session()
    songs = db_sess.query(Song).filter(user_id == user_id).all()
    return songs
