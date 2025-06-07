import hikari
import lightbulb
from loguru import logger
from src.agent import ConversationManager

loader = lightbulb.Loader()


@loader.listener(hikari.GuildMessageCreateEvent)
async def on_bot_mentioned(event: hikari.GuildMessageCreateEvent) -> None:
    message = event.message

    # Skip if from bot
    if message.author.is_bot:
        return

    # Check if bot is mentioned
    bot = await event.app.rest.fetch_my_user()
    if bot.id not in message.user_mentions_ids:
        return

    username = message.author.username

    await event.app.rest.create_message(
        channel=message.channel_id,
        content=f"Hi {username}, you mentioned me?"
    )
