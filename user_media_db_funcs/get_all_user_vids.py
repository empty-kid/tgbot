from data import db_session
from data.videos import Video


def get_all_user_vids(user_id):
    db_sess = db_session.create_session()
    vids = db_sess.query(Video).filter(user_id == user_id).all()
    return vids
