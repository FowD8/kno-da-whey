import discord
import asyncio
from discord.ext import commands
from discord.ext.commands import Bot
import yaml
from tinydb import TinyDB, Query
import datetime

# custom classes
from twitch_api import TwitchAPI
from bot_helper import BotHelper

# for my neural network work
import tensorflow as tf
import numpy as np
# import requests
from requests import get

# debugger
# use `embed()` to breakpoint
from IPython import embed as breakpoint


class discord_bot(object):
    def __init__(self, token, client_id):
        bot = Bot(description = "", command_prefix = '!')
        db = TinyDB('db.json')
        twitch_api = TwitchAPI(client_id)
        bot_helper = BotHelper(bot, db, twitch_api)
        
        ############
        # LISTENERS 
        ############

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
                await bot_helper.delete_message(reaction.message)

        # filter messages
        @bot.event
        async def on_message(message):
            # restricts bot message checks to server id 173297475057090562 (NoRobotsAllowed) and my channel
            if message.server.id == '173297475057090562' and message.channel.name == 'bryan':
                # fix to allow commands to work
                await bot.process_commands(message)

        ##########
        # THREADS
        ##########

        # checks twitch api for who is streaming
        async def check_twitch():
            await bot.wait_until_ready()

            while not bot.is_closed:
                await bot_helper.check_who_is_streaming()

                await asyncio.sleep(30)   

        ###########
        # COMMANDS 
        ###########

        """ TWITCH COMMANDS """
        # !twitch
        @bot.group(pass_context = True)
        async def twitch(ctx):
            # remove user's command message
            await bot_helper.delete_message(ctx.message)

            if ctx.invoked_subcommand is None:
                await bot_helper.bot_say('`{}` is an invalid command'.format(ctx.message.content))
        
        # !twitch channel
        @twitch.group(pass_context = True)
        async def channel(ctx):
            if ctx.invoked_subcommand is None:
                await bot_helper.bot_say('`{}` is an invalid command'.format(ctx.message.content))
        
        # !twitch channel add <twitch_channel>
        @channel.command()
        async def add(name: str):
            await bot_helper.twitch_add_channel(name)             
        
        # !twitch channel remove <twitch_channel>
        @channel.command()
        async def remove(name: str):
            await bot_helper.twitch_remove_channel(name)
        
        # !twitch channel list
        @channel.command()
        async def list():
            await bot_helper.twitch_list_channels()

        """ Basic ping pong test"""
        # !ping
        @bot.command(pass_context = True)
        async def ping(ctx):
            await bot_helper.delete_message(ctx.message)
            await bot_helper.bot_say(":ping_pong: Pong!", expiration=2)









        """Gonna work on trying to get an image recognition method working for fun
        command is gonna be !identify
        will take in an input image and run it through a classifier and see attempt to identify image
        Image dimensions: tbd
        Neural network implemented in tensorflow"""

        # Saves whatever picture is attached with the message, as the file name
        # @bot.command(pass_context = True)
        # async def save_meme(ctx):
        #     file_name = ctx.message.content[11:] + ".jpg"
        #     self.download_image(ctx.message.attachments[0]['url'], file_name)
        #     await delete_message(ctx.message)
        #     await bot_say("Saved Meme to %s" %file_name)

        # @bot.command(pass_context = True)
        # async def identify(ctx):
        #     print(ctx.message.attachments[0]['url'])
        #     self.download_image(ctx.message.attachments[0]['url'], "test.jpg")
        #     await bot_say(ctx.message.attachments[0]['url'])









        ##########
        # EXECUTE
        ##########

        bot.loop.create_task(check_twitch())
        bot.run(token)

    def download_image(self, url, save_file):
        with open(save_file, 'wb') as sfile:
            response = get(url)
            sfile.write(response.content)

    # def identify_image(self, image):

    # def neural_net(self):


def main():
    # remember to copy secrets.yml.example and input your info
    secrets = yaml.load(open('secrets.yml', 'r'))
    bot = discord_bot(secrets['BOT_TOKEN'], secrets['TWITCH_CLIENT_ID'])

if __name__ == "__main__":
    main()