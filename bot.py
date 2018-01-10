import discord
from discord.ext import commands
from discord.ext.commands import Bot
import asyncio
import yaml

# debugger
# use `embed()` to breakpoint
from IPython import embed

secrets = yaml.load(open('secrets.yml', 'r'))

bot = commands.Bot(command_prefix = '!')

# executed when bot is ready
@bot.event
async def on_ready():
	print('-------')
	print('Logged in as {} ({})'.format(bot.user.name, bot.user.id))
	print('-------')

# executed when any message gets a reaction
@bot.event
async def on_reaction_add(reaction, user):
	# check if a user clicked on a bot's message 🗑
	if reaction.emoji == '🗑' and reaction.message.author == bot.user and user != bot.user:
		await bot.delete_message(reaction.message)

@bot.command(pass_context = True)
async def test(ctx):
	# remove user's command message
	await bot.delete_message(ctx.message)

	# add message and 🗑 reaction
	test_message = await bot.say("Hello World??")
	await bot.add_reaction(test_message, '🗑')

bot.run(secrets['BOT_TOKEN'])