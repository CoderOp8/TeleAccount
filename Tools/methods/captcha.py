from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup as IKM
from ..info import logger
from typing import Union
import re

class Captcha:
    async def captcha(
        phone_number: str,
        session_string: str,
        username: Union[str, int],
        force_find: bool = False,
        button: bool = False,
        type: str = "math"
    ):
        app = Client(phone_number, session_string=session_string)
        await app.connect()

        try:
            # Get captcha message
            if not force_find:
                message = await Captcha.get_last_message(app, username)
            else:
                message = await Captcha.find(app, username)

            # Solve math captcha
            if type == "math":
                captcha = Captcha.get_math_captcha(message.text)
                if captcha:
                    solve = eval(captcha)  # Safely evaluate the expression
                else:
                    raise ValueError(f"No valid math expression found in the message: {message.text}")

            # Solve via button click or direct message
            if button and isinstance(message.reply_markup, IKM):
                await Captcha.choose(message, str(solve))
            else:
                await app.send_message(username, str(solve))

            await app.disconnect()
            return 1

        except Exception as e:
            await app.disconnect()
            logger.exception(e)
            return 0

    async def choose(msg, solve):
        """ Click the correct button if the captcha has multiple choices. """
        n = 0
        for row in msg.reply_markup.inline_keyboard:
            for btn in row:
                if btn.text == solve:
                    try:
                        await msg.click(n, timeout=1)
                    except:
                        pass
                    return
            n += 1

    @staticmethod
    def get_math_captcha(text):
        """ Extracts a full math equation from text and removes unwanted characters. """
        pattern = re.compile(r'(\d+\s*[\+\-\*/]\s*\d+(?:\s*[\+\-\*/]\s*\d+)*)')  
        match = pattern.search(text)

        if match:
            equation = match.group(1).replace(" ", "")  # Remove spaces for safe evaluation
            return equation

        return False

    async def find(app, username):
        """ Finds the last math captcha in chat history. """
        async for m in app.get_chat_history(username, limit=10):
            data = Captcha.get_math_captcha(m.text)
            if data:
                return m

    async def get_last_message(app, username):
        """ Fetches the last message from the chat. """
        async for m in app.get_chat_history(username, limit=1):
            return m
