import json
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from collections import namedtuple
import asyncio
import concurrent.futures

logger = logging.getLogger(__name__)


def format_time_delta(delta_seconds):
    hours = int(delta_seconds // 3600)
    minutes = int((delta_seconds % 3600) // 60)
    seconds = int(delta_seconds % 60)
    if hours:
        return "{}h {}m {}s".format(hours, minutes, seconds)
    elif minutes:
        return "{}m {}s".format(minutes, seconds)
    elif seconds:
        return "{}s".format(seconds)


def formatted_post(post):
    try:
        caption = post.edge_media_to_caption['edges'][0]['node']['text']
    except (KeyError, IndexError):
        caption = ''

    media_url = post.display_url
    time_ago = format_time_delta(datetime.now().timestamp() - post.taken_at_timestamp)
    comment_number = post.edge_media_to_comment['count']
    like_number = post.edge_liked_by['count']
    insta_url = f"https://www.instagram.com/p/{post.shortcode}/"

    info = (f'{post.user}: {insta_url}\n'
            f'{comment_number} comments, {like_number} likes\nPosted {time_ago} ago')
    return media_url, info, caption


executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)


async def new_posts(user):
    def get_user_activity():
        try:
            r = requests.get(f'https://www.instagram.com/{user}/').text
            m = json.loads(BeautifulSoup(r, "html.parser").find_all("script")[
                           2].text.replace("window._sharedData = ", "")[:-1])
            return m['entry_data']['ProfilePage'][0]
        except json.JSONDecodeError:
            print(requests.get(f'https://www.instagram.com/{user}/').text)
            return None

    user_activity = await asyncio.get_event_loop().run_in_executor(executor,
                                                                   get_user_activity)

    if user_activity is None:
        return []

    def convert_to_post_obj(post_dict):
        post_dict['user'] = user

        def sanitize_fieldname(fieldname):
            if fieldname.startswith('_'):
                return fieldname[2:]
            return fieldname
        fields = list(sanitize_fieldname(e) for e in post_dict.keys()) + ['score']
        score = post_dict["edge_liked_by"]['count']

        values = list(post_dict.values()) + [score]
        return namedtuple('Post', fields)(*values)

    edges = user_activity['graphql']['user']['edge_owner_to_timeline_media']['edges']
    return [convert_to_post_obj(edge['node']) for edge in edges][::-1]
