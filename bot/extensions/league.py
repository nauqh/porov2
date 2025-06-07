import hikari
import lightbulb
from loguru import logger
from src.agent import ConversationManager

loader = lightbulb.Loader()


@loader.listener(hikari.GuildMessageCreateEvent)
async def on_message_create(event, agent: ConversationManager) -> None:
    message = event.message

    if message.author.is_bot:
        return

    bot_id = (await event.app.rest.fetch_my_user()).id
    if bot_id not in message.user_mentions_ids:
        return

    content = message.content.replace(f"<@{bot_id}>", "").strip()
    username = message.author.username

    try:
        thread = await event.app.rest.create_message_thread(
            message.channel_id,
            message.id,
            f"Conversation with {username}",
        )
        conv_id = str(thread.id)
        logger.info(f"Created new conversation: {conv_id}")

        reply = agent.handle_message(
            conv_id, f"Username: {username}\n{content}")
        await event.app.rest.create_message(channel=thread.id, content=reply)

    except Exception as e:
        logger.exception(f"Error in thread-based reply: {e}")
        await event.app.rest.create_message(
            channel=thread.id,
            content="⚠️ Sorry, I ran into an error while replying."
        )


@loader.listener(hikari.GuildMessageCreateEvent)
async def on_thread_followup(event, agent: ConversationManager) -> None:
    message = event.message
    if message.author.is_bot:
        return
    # Only proceed if this message is inside a thread
    thread = await message.fetch_channel()
    if not isinstance(thread, hikari.GuildThreadChannel):
        return

    conv_id = str(thread.id)
    username = message.author.username
    logger.info(f"Received follow-up in thread {conv_id} from {username}")
    content = message.content.strip()

    # Count how many messages in the thread are from the bot
    history = await thread.fetch_history()
    bot = await event.app.rest.fetch_my_user()
    bot_responses = sum(
        1 for msg in history if msg.author.id == bot.id)

    if bot_responses >= 4:
        logger.info(f"Bot response limit reached in thread {conv_id}")
        await event.app.rest.create_message(
            channel=conv_id,
            content="This thread has reached the 4-response limit. Please start a new thread for further assistance."
        )
        return

    try:
        reply = agent.handle_message(
            conv_id, f"Username: {username}\n{content}")
        await event.app.rest.create_message(channel=conv_id, content=reply)
    except Exception as e:
        logger.exception(f"Error in thread follow-up reply: {e}")
        await event.app.rest.create_message(
            channel=conv_id,
            content="⚠️ Sorry, I ran into an error while replying."
        )
