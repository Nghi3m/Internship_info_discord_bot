import os
import discord
from discord.ext import commands, tasks
from dotenv import  load_dotenv
from Housekeeping import Housekeeping

# load variables from .env file to OS' environment variables
load_dotenv()
bot_token = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ENDPOINT = os.getenv("ENDPOINT")

# set up permission
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# instantiate housekeeping class
housekeeping = Housekeeping(ENDPOINT)

@bot.event
async def on_ready():
    # setup slash command and start endpoint checking routine
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    finally:
        check_periodically.start()

# command for pulling from endpoint at any given moment
@bot.tree.command(name="pull", description="Pull from endpoint immediately")
async def pull(interaction: discord.Interaction):
    await housekeeping.send_message_if_added(interaction.response.send_message, True)

# routine for pulling from endpoint for every set interval
@tasks.loop(minutes=1)
async def check_periodically():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await housekeeping.send_message_if_added(channel.send)
    else:
        print(f"Channel with ID {CHANNEL_ID} not found.")

if __name__ == '__main__':
    bot.run(bot_token)