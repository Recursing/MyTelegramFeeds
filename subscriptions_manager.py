import dataset
import logging

logger = logging.getLogger(__name__)

connection_string = 'sqlite:///demo_db.db'  # TODO: throw warning if using test db
DB = dataset.connect(connection_string)


logger.info('Connected! (Hopefully)')


def subscribe(chat_id, source, threshold):
    """
        returns False if the user is already subscribed
    """
    subscription = {
        'chat_id': chat_id,
        'source': source,
        'threshold': threshold
    }

    # try to update, if not found insert
    if DB['subscriptions'].find_one(chat_id=chat_id, source=source):
        return False

    DB['subscriptions'].insert(subscription)
    return True


def unsubscribe(chat_id, source):
    """
        returns False if there is no matching subscription
    """
    return DB['subscriptions'].delete(chat_id=chat_id, source=source)


def update_threshold(chat_id, source, new_threshold):
    subscription = {
        'chat_id': chat_id,
        'source': source,
        'threshold': new_threshold
    }
    DB['subscriptions'].update(subscription, keys=['chat_id', 'source'])


def all_sources():
    return [
        list(e.values())[0] for e in DB['subscriptions'].distinct('source')
    ]


def get_subscriptions(source):
    return [(row['chat_id'], row['threshold'])
            for row in DB['subscriptions'].find(source=source)]


def user_thresholds(chat_id):
    for row in DB['subscriptions'].find(chat_id=chat_id):
        yield row['source'], row['threshold']


def user_subscriptions(chat_id):
    for row in DB['subscriptions'].find(chat_id=chat_id):
        yield row['source'], row['threshold']


def already_sent(chat_id, post_id):
    return bool(DB['messages'].find_one(chat_id=chat_id, post_id=post_id))


def mark_as_sent(chat_id, post_id):
    DB['messages'].insert(dict(chat_id=chat_id, post_id=post_id))
