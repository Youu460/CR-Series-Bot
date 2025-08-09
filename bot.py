import logging
import logging.config

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)

from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from database.ia_filterdb import Media
from database.users_chats_db import db
from info import SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_STR, LOG_CHANNEL
from utils import temp
from typing import Union, Optional, AsyncGenerator
from pyrogram import types
from aiohttp import web
from plugins import web_server
from datetime import date, datetime 
import pytz
import time



PORT = "8080"

class Bot(Client):

    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=700,
            plugins={"root": "plugins"},
            sleep_threshold=5,
        )

        async def start_bot():
    b_users, b_chats = await db.get_banned()  # ✅ 4 spaces indentation
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats
        await super().start()
        await Media.ensure_indexes()

        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        self.username = '@' + me.username

        tz = pytz.timezone('Asia/Kolkata')
        today = date.today()
        now = datetime.now(tz)
        current_time = now.strftime("%I:%M:%S %p")

        # ✅ Safely try to join or fetch the log channel
        try:
            await self.get_chat(LOG_CHANNEL)
        except Exception as e:
            try:
                # If bot is not in the channel, try joining (works with @username or invite link)
                await self.join_chat(LOG_CHANNEL)
                logging.info(f"Joined LOG_CHANNEL: {LOG_CHANNEL}")
            except Exception as join_err:
                logging.error(f"Cannot access LOG_CHANNEL: {join_err}")
                # Skip sending the start message if channel not accessible
                return

        # If accessible, send restart message
        try:
            await self.send_message(
                chat_id=LOG_CHANNEL,
                text=(
                    f"@{me.username} Rᴇsᴛᴀʀᴛᴇᴅ !\n\n"
                    f"📅 Dᴀᴛᴇ : {today}\n"
                    f"⏰ Tɪᴍᴇ : {current_time}\n"
                    f"🌐 Tɪᴍᴇᴢᴏɴᴇ : Asia/Kolkata"
                )
            )
        except Exception as send_err:
            logging.error(f"Failed to send restart message: {send_err}")

        # Start web server
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()
        logging.info(f"{me.first_name} with Pyrogram v{version} (Layer {layer}) started as {me.username}.")

    async def stop(self, *args):
        await super().stop()
        logging.info("Bot stopped. Bye.")
    
    async def iter_messages(
        self,
        chat_id: Union[int, str],
        limit: int,
        offset: int = 0,
    ) -> Optional[AsyncGenerator["types.Message", None]]:
        """Iterate through a chat sequentially.
        This convenience method does the same as repeatedly calling :meth:`~pyrogram.Client.get_messages` in a loop, thus saving
        you from the hassle of setting up boilerplate code. It is useful for getting the whole chat messages with a
        single call.
        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).
                
            limit (``int``):
                Identifier of the last message to be returned.
                
            offset (``int``, *optional*):
                Identifier of the first message to be returned.
                Defaults to 0.
        Returns:
            ``Generator``: A generator yielding :obj:`~pyrogram.types.Message` objects.
        Example:
            .. code-block:: python
                for message in app.iter_messages("pyrogram", 1, 15000):
                    print(message.text)
        """
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            messages = await self.get_messages(chat_id, list(range(current, current+new_diff+1)))
            for message in messages:
                yield message
                current += 1


app = Bot()
app.run()
