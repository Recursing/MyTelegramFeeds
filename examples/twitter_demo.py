import asyncio

from MyFeedsBot import MyFeedsBot
import twitter_adapter
from credentials import BOT_API_KEY


class MyTwittersBot(MyFeedsBot):
    async def new_posts(self, source):
        return await twitter_adapter.new_posts(source)

    def format(self, post):
        return twitter_adapter.formatted_post(post)

    async def send_formatted_post(self, chat_id, post):
        message, has_media = self.format(post)
        await self.bot.send(chat_id, message, show_keyboard=False,
                            parse_mode="HTML", disable_web_page_preview=(not has_media))


bot = MyTwittersBot(BOT_API_KEY)

loop = asyncio.get_event_loop()
loop.run_until_complete(bot.run_feed())
loop.run_forever()
