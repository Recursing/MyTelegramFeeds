import telepot
import telepot.aio
from telepot.aio.loop import MessageLoop
import asyncio
from json import dumps


class BotAdapter(telepot.aio.Bot):
    def __init__(self, token):
        super().__init__(token)
        self.commands = {}
        self.personal_handles = {}
        loop = asyncio.get_event_loop()
        loop.create_task(MessageLoop(self, self.handle).run_forever())

    def chunks(self, sequence, chunk_size=2):
        """
            [1,2,3,4,5], 2 --> [[1,2],[3,4],[5]]
        """
        lsequence = list(sequence)
        while lsequence:
            size = min(len(lsequence), chunk_size)
            yield lsequence[:size]
            lsequence = lsequence[size:]

    async def send(self, chat_id, text, show_keyboard=True, **kwargs):
        if show_keyboard:
            kwargs['reply_markup'] = self.default_keyboard
        else:
            kwargs['reply_markup'] = dumps({'remove_keyboard': True})
        await self.sendMessage(chat_id, text, **kwargs)

    def generate_keyboard(self, options):
        row_length = 2 if len(options) < 9 else 3
        text_table = self.chunks(options, chunk_size=row_length)
        keyboard = [[{'text': text} for text in row] for row in text_table]
        return keyboard

    async def ask(self, chat_id, question, reply_handler, possible_replies=None):
        if not possible_replies:
            possible_replies = []
        reply_markup = dumps({
            'force_reply': True,
            'keyboard': self.generate_keyboard(possible_replies + ['/cancel']),
            'one_time_keyboard': True,
            'resize_keyboard': True
        })
        await self.sendMessage(chat_id, question, reply_markup=reply_markup)

        async def temp_handle(message):
            if 'text' not in message:
                return
            del self.personal_handles[chat_id]
            if message['text'].startswith('/'):
                await self.handle(message)
            else:
                await reply_handler(chat_id, message['text'].split())

        self.personal_handles[chat_id] = temp_handle

    def add_command(self, name, callback, expectedType=None, question='', options=None):
        async def command_handler(chat_id, arguments):
            if expectedType in (list, str) and not arguments:
                await self.ask(chat_id, question, command_handler, options)
            else:
                if expectedType == str:
                    arguments = arguments[0]
                if expectedType is None:  # TODO check wanted number of args
                    await callback(chat_id)
                else:
                    await callback(chat_id, arguments)
        self.commands['/' + name] = command_handler
        self.default_keyboard = dumps({
            'resize_keyboard': True,
            'keyboard': self.generate_keyboard(self.commands),
            'one_time_keyboard': True
        })

    async def handle(self, message):
        print("recieved")
        if 'text' not in message:
            return
        chat_id = message['chat']['id']
        if chat_id in self.personal_handles:
            await self.personal_handles[chat_id](message)
            return
        text = message['text']
        if text.startswith('/'):
            command, *arguments = text.split(None)
            if command in self.commands:
                await self.commands[command](chat_id, arguments)
            else:
                await self.sendMessage(chat_id, 'Unknown command')
        else:
            await self.sendMessage(chat_id,
                                   "Doesn't look like anything to me")

    def start_handling(self, handle):
        self.message_loop(callback=self.handler)  # TODO await
