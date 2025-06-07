import hikari
import lightbulb
from loguru import logger
from src.agent import ConversationManager


loader = lightbulb.Loader()


@loader.command
class YourCommand(
    ...
):
    ...
