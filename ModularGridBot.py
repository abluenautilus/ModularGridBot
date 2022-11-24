import discord
import re
import requests
from bs4 import BeautifulSoup
from MGModule import MGModule
import os

intents = discord.Intents.all()
client = discord.Client(command_prefix='!', intents=intents)

url_main = "https://modulargrid.net"
num_alternates = 0

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("[[") and message.content.endswith("]]"):

        themodule = MGModule()
        # Extract the module name from between the brackets
        match = re.match("\[\[(.*)\]\]", message.content)
        if match.groups():
            command = match.groups()[0]
            result = re.match("([a-zA-Z\s]*):?\s?(\d*)",command)
            if result:
                module = result.groups()[0]
                if result.groups()[1]:
                    num_alternates = result.groups()[1]
                else:
                    num_alternates = 0
            else:
                await message.channel.send("Error parsing command")
            if module:
                # Replace spaces with dashes
                module_slug = re.sub(" ", "-", module)
                bot_message = await message.channel.send("Looking for %s..." % module)
                # Create URL
                url = "%s/e/%s" % (url_main, module_slug)
                # Fetch URL
                response = requests.get(url)

                if response.status_code != 200:
                    await bot_message.edit(content="No URL match, searching database...")
                    await themodule.search(module, message, bot_message, num_alternates)
                    await bot_message.delete()

                else:
                    await bot_message.edit(content="Found module...")
                    themodule.initFromPage(response)
                    await themodule.render(message, bot_message)
                    await bot_message.delete()

        else:
            await message.channel.send("Module not parsed")


client.run(os.environ['DISCORD_TOKEN'])
