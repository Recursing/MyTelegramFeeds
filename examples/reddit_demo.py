import asyncio

from MyFeedsBot import MyFeedsBot, subscriptions_manager
import reddit_adapter
from credentials import BOT_API_KEY


class MySubredditsBot(MyFeedsBot):
    async def new_posts(self, source):
        posts = await reddit_adapter.top_day_posts(source, limit=15)
        if any(threshold < 100 for user, threshold
               in subscriptions_manager.get_subscriptions(source)):
            posts += await reddit_adapter.new_posts(source, limit=15)
        return posts

    def format(self, post):
        return reddit_adapter.formatted_post(post)

    async def default_threshold(self, source):
        return reddit_adapter.get_threshold(source, monthly_rank=100)


bot = MySubredditsBot(BOT_API_KEY)

loop = asyncio.get_event_loop()
loop.run_until_complete(bot.run_feed())
loop.run_forever()
