import os
import discord

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

@client.event
async def on_ready():
    print('MasterBot is ready!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content == 'sakura trick':
        response = 'https://i.imgur.com/oG4J1yz.png'
        await message.channel.send(response)

client.run(TOKEN)