import hikari
import lightbulb
from loguru import logger
from src.agent import ConversationManager

loader = lightbulb.Loader()


@loader.listener(hikari.GuildMessageCreateEvent)
async def on_message_create(
    event: hikari.GuildMessageCreateEvent,
    agent: ConversationManager
) -> None:
    message = event.message

    if message.author.is_bot:
        return

    bot = await event.app.rest.fetch_my_user()
    if bot.id not in message.user_mentions_ids:
        return

    content = message.content.replace(f"<@{bot.id}>", "").strip()
    username = message.author.username

    # Create a thread for this message
    thread = await event.app.rest.create_message_thread(
        message.channel_id,
        message.id,
        f"Conversation with {username}",
    )

    # Use thread ID as session_id
    conv_id = str(thread.id)
    logger.info(f"Created new conversation: {conv_id}")

    try:
        reply = agent.handle_message(
            conv_id, f"Username: {username}\n{content}")
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


# @loader.listener(hikari.GuildMessageCreateEvent)
# async def on_thread_followup(event: hikari.GuildMessageCreateEvent) -> None:
#     manager: ConversationManager = event.app.d.manager

#     message = event.message

#     if message.author.is_bot:
#         return
#     thread = await message.fetch_channel()
#     if not isinstance(thread, hikari.GuildThreadChannel):
#         return

#     conv_id = str(thread.id)
#     logger.info(f"Continue conversation: {conv_id}")

#     try:
#         content = f"Username: {message.author.username}\n{message.content}"
#         reply = manager.handle_message(conv_id, content)

#         await event.app.rest.create_message(
#             channel=thread.id,
#             content=reply
#         )
#     except Exception as e:
#         logger.exception(f"Error handling follow-up in thread: {e}")
#         await event.app.rest.create_message(
#             channel=thread.id,
#             content="⚠️ Sorry, I ran into an error while replying to your follow-up."
#         )
