import hikari
import lightbulb
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Create the base Hikari bot
bot = hikari.GatewayBot(os.getenv("TOKEN"))
# Create the Lightbulb client from the bot
client = lightbulb.client_from_app(bot)

# Optional: Subscribe to start the client when the bot starts
bot.subscribe(hikari.StartingEvent, client.start)

# Load all extensions in your bot/extensions folder
client.load_extensions("./bot/extensions")

# Run the bot (blocking)
bot.run(
    status=hikari.Status.ONLINE,
    activity=hikari.Activity(
        name="v1.0.0",  # Replace or dynamically load your version here
        type=hikari.ActivityType.LISTENING,
    ),
)
