import requests
from requests_oauthlib import OAuth1
from collections import namedtuple
import re
import logging
import asyncio
import concurrent.futures

import credentials

logger = logging.getLogger(__name__)

oauth = OAuth1(credentials.API_KEY,
               credentials.API_SECRET,
               credentials.ACCESS_TOKEN,
               credentials.ACCESS_TOKEN_SECRET)


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
    # print(post)
    twitter_url = f"https://www.twitter.com/{post.user['screen_name']}/status/{post.id}"
    text = re.sub(r'(^|[^@\w])@(\w{1,20})\b',
                  '\\1<a href="http://twitter.com/\\2">@\\2</a>',
                  post.full_text)
    if post.in_reply_to_screen_name:
        text = 'Reply: ' + text
    if hasattr(post, 'entities') and post.entities.get('urls'):
        for url in post.entities['urls']:
            text = text.replace(url['url'], url['expanded_url'])
    has_media = False
    if hasattr(post, 'extended_entities') and post.extended_entities:
        # print(post)
        # print('='*40)
        for media in post.extended_entities['media']:
            text = text.replace(media["url"], '')
            text = f'<a href="{media["expanded_url"]}">{media["type"]}</a>\n' + text
        has_media = True
    message = (f'<a href="{twitter_url}">{post.user["name"]}</a>: {text}\n\n'
               f'{post.retweet_count} retweets, {post.favorite_count} favorites.')
    return message, has_media


executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)


async def new_posts(user):
    def get_user_activity():
        return requests.get(f'https://api.twitter.com/1.1/statuses/user_timeline.json'
                            f'?screen_name={user}&count=4&tweet_mode=extended',
                            auth=oauth).json()

    user_act = await asyncio.get_event_loop().run_in_executor(executor, get_user_activity)
    if type(user_act) != list:
        print(user_act)
        print("USER ACTIVITY IS NOT A LIST OMG CAN YOU BELIEVE IT")
        logger.error(user_act)
        return []

    def convert_to_obj(post_dict):
        fields = list(post_dict.keys()) + ['score']
        score = post_dict["favorite_count"] + post_dict["retweet_count"]
        values = list(post_dict.values()) + [score]
        return namedtuple('Post', fields)(*values)
    return [convert_to_obj(e) for e in reversed(user_act)]
