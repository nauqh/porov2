import hikari
import lightbulb
from loguru import logger
from src.agent import ConversationManager

loader = lightbulb.Loader()
agent = ConversationManager()


@loader.listener(hikari.GuildMessageCreateEvent)
async def on_bot_mentioned(event: hikari.GuildMessageCreateEvent) -> None:
    message = event.message

    if message.author.is_bot:
        return

    bot = await event.app.rest.fetch_my_user()
    if bot.id not in message.user_mentions_ids:
        return

    message = message.content.replace(f"<@{bot.id}>", "").strip()
    username = message.author.username

    # Create a thread for this message
    thread = await event.app.rest.create_message_thread(
        message.channel_id,
        message,
        f"Conversation with {username}",
    )

    # Use the thread ID as the session_id for ConversationManager
    conv_id = str(thread.id)
    input_text = f"Username: {username}\n{message}"

    try:
        reply = agent.handle_message(conv_id, input_text)

        await event.app.rest.create_message(
            channel=thread.id,
            content=reply
        )
    except Exception as e:
        logger.exception(f"Error in thread-based reply: {e}")
        await event.app.rest.create_message(
            channel=thread.id,
            content="⚠️ Sorry, I ran into an error while replying."
        )
