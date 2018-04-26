import logging

import asyncio

import telepot_adapter
import subscriptions_manager

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='infolog.log',
    level=logging.INFO)


class MyFeedsBot(telepot_adapter.BotAdapter):
    def __init__(self, token, update_period=600):
        super().__init__(token)

        self.logger = logging.getLogger(__name__)
        self.start_message = 'Welcome to this feed bot! Try to /add something'
        # TODO decide how to configure messages (e.g. "which subreddit would you ...")
        self.add_command('add', callback=self.on_add, expectedType=list,
                         question='What would you like to add?')
        self.add_command('list', callback=self.on_list)
        self.add_command('start', callback=self.on_start)
        self.add_command('remove', callback=self.on_remove,
                         expectedType=list, question='What would you like to remove?')
        # TODO add more/less/update_threshold

        self.update_period = update_period

    async def on_start(self, chat_id):
        await self.send(chat_id, self.start_message)

    async def on_add(self, chat_id, sources):
        for source in sources:
            try:
                await self.new_posts(source)
            except Exception as e:
                print(e)
                await self.send(chat_id, f'Cannot get posts from {source}')
            threshold = await self.default_threshold(source)
            subscriptions_manager.subscribe(chat_id, source, threshold)
        await self.on_list(chat_id)
        await self.send_updates()

    async def on_remove(self, chat_id, sources):
        for source in sources:
            subscriptions_manager.unsubscribe(chat_id, source)
        await self.on_list(chat_id)

    async def on_moar(self, chat_id, source):
        pass

    async def on_less(self, chat_id, source):
        pass

    async def on_list(self, chat_id):
        subscriptions = subscriptions_manager.user_subscriptions(chat_id)
        message = 'You are now subscribed to:\n'
        message += '\n'.join(
            [f'{source}, threshold: {threshold}' for source, threshold in subscriptions])
        await self.send(chat_id, message)

    def format(self, post):
        return repr(post)

    def score(self, post):
        return 0

    async def default_threshold(self, source):
        return 0

    async def new_posts(self, source):
        raise NotImplementedError("You must implement a new_posts method")

    async def send_formatted_post(self, chat_id, post):
        await self.send(chat_id, self.format(post),
                        show_keyboard=False, parse_mode="HTML")

    async def send_post(self, chat_id, post):
        # TODO rate limiting
        if subscriptions_manager.already_sent(chat_id, post.id):
            return
        try:
            await self.send_formatted_post(chat_id, post)
        except Exception as e:
            print(e)
            self.logger.error('Failed to send {} to {}'.format(post, chat_id))
            self.logger.error(e)
            unsub_reasons = [
                'chat not found', 'bot was blocked by the user',
                'user is deactivated', 'chat not found', 'bot was kicked'
            ]
            if any(reason in str(e) for reason in unsub_reasons):
                self.logger.warning('Unsubscribing user {}'.format(chat_id))
                for sub, th, pm in subscriptions_manager.user_subscriptions(
                        chat_id):
                    subscriptions_manager.unsubscribe(chat_id, sub)
                await self.send(80906134, 'Unsibscribing:\n' + str(e))
            elif (hasattr(e, 'json')
                  and 'group chat was upgraded to a supergroup chat' in
                  e.json['description']):
                self.logger.warning('Resubscribing group {}'.format(chat_id))
                for sub, th in subscriptions_manager.user_subscriptions(chat_id):
                    subscriptions_manager.subscribe(
                        e.json['parameters']['migrate_to_chat_id'], sub, th)
                    subscriptions_manager.unsubscribe(chat_id, sub)
            else:
                await self.send(80906134, str(e))
        subscriptions_manager.mark_as_sent(chat_id, post.id)

    async def send_source_updates(self, source):
        subscriptions = subscriptions_manager.get_subscriptions(source)
        post_iterator = await self.new_posts(source)
        for post in post_iterator:
            for chat_id, threshold in subscriptions:
                if post.score >= threshold:
                    await self.send_post(chat_id, post)

    async def send_updates(self):
        for source in subscriptions_manager.all_sources():
            await self.send_source_updates(source)
        print("Sent updates")

    async def run_feed(self):
        print("Running?")
        while True:
            await self.send_updates()
            await asyncio.sleep(self.update_period)
