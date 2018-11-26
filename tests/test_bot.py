import sys, os
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../myroutinebot/')
from myroutinebot.handletask import HandleTask 
from myroutinebot.bot import Bot
from myroutinebot.taskbot import TaskBot
import pytest

from .schemas import assert_valid_schema, message_schema, no_message_schema

def test_get_url():
    bot = Bot()
    assert isinstance(bot.get_url(bot.URL), str)

def test_get_json_from_url():
    bot = Bot()
    url = 'https://api.telegram.org/bot597151993:AAFYtCYeSONpV_8Fj16EmAF16XQjG0grvVo/getUpdates?timeout=1'
    assert assert_valid_schema(bot.get_json_from_url(url), no_message_schema) == None
