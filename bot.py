import discord
import asyncio
from discord.ext import commands
from discord.ext.commands import Bot
import yaml
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

        @bot.command(pass_context = True)
        async def delete_me(ctx):
            # remove user's command message
            await bot.delete_message(ctx.message)
            # add message and 🗑 reaction
            test_message = await bot.say("Hello World??")
            await bot.add_reaction(test_message, '🗑')

        @bot.command(pass_context = True)
        async def ping(*args):
            message = await bot.say(":ping_pong: Pong!")
            await bot.add_reaction(message, '🗑')

        bot.run(token)


def main():
    #change this if you're using it for your file
    secret_path = "C:/Users/Brian/Documents/GitHub/secrets.yml"
    secrets = yaml.load(open(secret_path, 'r'))
    bot = discord_bot(secrets['BOT_TOKEN'])

if __name__ == "__main__":
    main()