import asyncio
import concurrent.futures
import urllib
from MyFeedsBot import MyFeedsBot
import instagram_adapter
from credentials import BOT_API_KEY


class MyInstagramsBot(MyFeedsBot):
    def __init__(self, token):
        super().__init__(token)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)

    async def new_posts(self, source):
        return await instagram_adapter.new_posts(source)[:4]

    def format(self, post):
        return instagram_adapter.formatted_post(post)

    async def send_formatted_post(self, chat_id, post):
        image, instagram_info, instagram_caption = self.format(post)
        if len(instagram_caption) + len(instagram_info) < 200:
            caption = instagram_info + '\n' + instagram_caption
            description = ''
        else:
            caption = instagram_info
            description = instagram_caption

        if len(image) > 100:
            def download_image():
                return urllib.request.urlopen(image)
            asyncio.get_event_loop().run_in_executor(self.executor, download_image)
        await self.sendPhoto(chat_id, image, caption=caption)
        if description:
            await self.send(chat_id, description, show_keyboard=False)


bot = MyInstagramsBot(BOT_API_KEY)

loop = asyncio.get_event_loop()
loop.run_until_complete(bot.run_feed())
loop.run_forever()
