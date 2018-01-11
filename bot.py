import discord
import asyncio
from discord.ext import commands
from discord.ext.commands import Bot
import yaml

#for my neural network work
import tensorflow as tf
import numpy as np
from requests import get

# debugger
# use `embed()` to breakpoint
from IPython import embed


class discord_bot(object):
    def __init__(self, token):
        bot = Bot(description="testing bot by brian",command_prefix = '!')
        # executed when bot is ready
        @bot.event
        async def on_ready():
            print('-------')
            print('Logged in as {} ({})'.format(bot.user.name, bot.user.id))
            print('-------')

        # executed when any message gets a reaction
        @bot.event
        async def on_reaction_add(reaction, user):
            #check if a user clicked on a bot's message
            if reaction.emoji == '🗑' and reaction.message.author == bot.user and user != bot.user:
                await bot.delete_message(reaction.message)

        #bot delete command test
        @bot.command(pass_context = True)
        async def delete_me(ctx):
            # remove user's command message
            await bot.delete_message(ctx.message)
            # add message and 🗑 reaction
            test_message = await bot.say("Hello World??")
            await bot.add_reaction(test_message, '🗑')

         #Basic ping pong test
        @bot.command(pass_context = True)
        async def ping(*args):
            message = await bot.say(":ping_pong: Pong!")
            await bot.add_reaction(message, '🗑')

        #Saves whatever picture is attached with the message, as the file name
        @bot.command(pass_context = True)
        async def save_last_meme(ctx):
            file_name = ctx.message.content[16:] + ".jpg"
            async for message in bot.logs_from(ctx.message.channel, limit=500):
                if message.attachments:
                    self.download_image(message.attachments[0]['url'], file_name)
                    message = await bot.say("Downloaded the most recent meme to %s"%file_name)
                    await bot.add_reaction(message, '🗑')
                    return
            message = await bot.say("Unable to find recent memes")
            await bot.add_reaction(message, '🗑')

        """Gonna work on trying to get an image recognition method working for fun
        command is gonna be !identify
        will take in an input image and run it through a classifier and see attempt to identify image
        Image dimensions: tbd
        Neural network implemented in tensorflow"""

        @bot.command(pass_context = True)
        async def identify(ctx):
            print(ctx.message.attachments[0]['url'])
            self.download_image(ctx.message.attachments[0]['url'], "test.jpg")
            message = await bot.say(ctx.message.attachments[0]['url'])
            await bot.add_reaction(message, '🗑')

        bot.run(token)

    def download_image(self, url, save_file):
        with open(save_file, 'wb') as sfile:
            response = get(url)
            sfile.write(response.content)



    #def identify_image(self, image):

    #def neural_net(self):


def main():
    #change this if you're using it for your file
    secrets = yaml.load(open("secrets.yml", 'r'))
    bot = discord_bot(secrets['BOT_TOKEN'])


if __name__ == "__main__":
    main()