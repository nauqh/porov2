import hikari
import lightbulb
from dotenv import load_dotenv
import os
from src.agent import ConversationManager


# Load environment variables
load_dotenv()

bot = hikari.GatewayBot(os.getenv("TOKEN"))
client = lightbulb.client_from_app(bot)
client.di.registry_for(lightbulb.di.Contexts.DEFAULT).register_factory(
    ConversationManager, lambda: ConversationManager()
)


@bot.listen(hikari.StartingEvent)
async def on_starting(_: hikari.StartingEvent) -> None:
    await client.load_extensions("bot.extensions.league")
    await client.start()

bot.run(
    status=hikari.Status.ONLINE,
    activity=hikari.Activity(
        name="v1.0.0",
        type=hikari.ActivityType.LISTENING,
    ),
)
