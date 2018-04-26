import praw
import logging
from datetime import datetime

import concurrent.futures
import asyncio
import credentials

logger = logging.getLogger(__name__)

reddit_credentials = credentials.reddit_credentials
reddit_reader = praw.Reddit(**reddit_credentials)


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
    """
       TODO: threshold, numero commenti, isolare nome subreddit
    """
    sub = post.subreddit.display_name

    title = post.title.replace('<', '&lt;').replace('>', '&gt;')
    permalink = post.permalink
    time_ago = format_time_delta(datetime.now().timestamp() - post.created_utc)
    comment_number = post.num_comments
    if post.over_18:
        title += ' - NSFW'

    template = ('{}: <a href=\"{}\">{}</a> - '
                '<a href=\"https://www.reddit.com{}\">{}+ Comments</a> - '
                'Posted {} ago')
    return template.format(sub, post.url, title, permalink, comment_number,
                           time_ago)


executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)


async def new_posts(subreddit, limit=15):
    def get_posts():
        sub = reddit_reader.subreddit(subreddit)
        return sub.new(limit=limit)
    return await asyncio.get_event_loop().run_in_executor(executor, get_posts)


async def top_day_posts(subreddit, loop=None, limit=15):
    """
        Returns top posts of this day on the subreddit
        Raise praw.qualcosa exception if subreddit doesn't exist
    """

    def get_posts():
        sub = reddit_reader.subreddit(subreddit)
        return list(sub.top('day', limit=limit))
    return await asyncio.get_event_loop().run_in_executor(executor, get_posts)


async def get_threshold(subreddit, monthly_rank=50):

    def get_last_post():
        sub = reddit_reader.subreddit(subreddit)
        return list(sub.top('month', limit=monthly_rank))[-1]
    last_post = await asyncio.get_event_loop().run_in_executor(executor, get_last_post)
    return last_post.score
