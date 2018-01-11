import discord
import asyncio
import datetime
from discord.ext.commands import Bot
from tinydb import TinyDB, Query
from twitch_api import TwitchAPI
from dateutil.parser import parse

# debugging
from IPython import embed as breakpoint

class BotHelper(object):
    bot_image = 'https://imgur.com/i3bLOXM.jpg'
    alert_channel_id = '400128509835739147'

    def __init__(self, bot, db, twitch_api):
        self.bot = bot
        self.db = db
        self.twitch_api = twitch_api
        self.twitch_channels_table = self.db.table('twitch_channels')

    """ Bot Messaging Methods """

    async def bot_say(self, message, expiration=10, trash=True):
        return await self._bot_to_discord(message=message, expiration=expiration, trash=trash)

    async def bot_embed(self, embed=None, expiration=10, channel=None, trash=True):
        embed = self._json_to_embed(embed)

        return await self._bot_to_discord(embed=embed, expiration=expiration, channel=channel, trash=trash)

    async def update_embed(self, channel=None, message_id=None, embed=None):
        channel = await self.get_channel(channel)
        message = await self.bot.get_message(channel, message_id)

        embed = self._json_to_embed(embed)

        await self.bot.edit_message(message, embed=embed)

    async def delete_message(self, message, delay=0.5):
        await asyncio.sleep(delay)
        try:
            await self.bot.delete_message(message)
        except:
            print('attempted to delete message that no longer exists')

    async def get_channel(self, channel_id):
        return self.bot.get_channel(channel_id)

    """ Twitch Methods """

    async def twitch_add_channel(self, name):
        if self.twitch_channels_table.contains(Query().name == name):
            await self.bot_say('`{}` is already on the list of twitch channels'.format(name))
        else:
            user_info = self.twitch_api.get_user_info(name=name)

            if user_info:
                self.twitch_channels_table.insert({
                    'id':                   user_info.get('id'),
                    'name':                 name,
                    'streaming_message_id': None
                })
                await self.bot_say('added `{}` to the list of twitch channels'.format(name))
            else:
                await self.bot_say('could not find username `{}` on twitch'.format(name))

    async def twitch_remove_channel(self, name):
        if name.lower() == "all":
            self.twitch_channels_table.purge()
            await self.bot_say('removed all twitch channels from the list')
        elif self.twitch_channels_table.contains(Query().name == name):
            self.twitch_channels_table.remove(Query().name == name)
            await self.bot_say('removing `{}` from the list of twitch channels'.format(name)) 
        else:
            await self.bot_say('`{}` is not on the list of twitch channels'.format(name))  

    async def twitch_list_channels(self):
        channel_names = self._all_twitch_channel_names()

        json_embed = {
            'title': 'List of Twitch channels currently tracking:',
            'description': '```\n{}```'.format('\n'.join(channel_names) or '\n'),
            'thumbnail': {
                'url': self.bot_image
            }
        }

        await self.bot_embed(embed=json_embed)

    """ """

    async def check_who_is_streaming(self):
        try:
            db_twitch_channel_names = self._all_twitch_channel_names(for_stream_info=True)
            db_twitch_channels = self.twitch_channels_table.all()
            live_streams = self.twitch_api.get_stream_info(db_twitch_channel_names)

            for db_twitch_channel in db_twitch_channels:
                db_twitch_id = db_twitch_channel.get('id')
                db_twitch_name = db_twitch_channel.get('name')
                db_twitch_streaming_message_id = db_twitch_channel.get('streaming_message_id')

                twitch_streaming_user_ids = [twitch_stream.get('user_id') for twitch_stream in live_streams]

                # if user is streaming on twitch
                if db_twitch_id in twitch_streaming_user_ids:
                    for stream in live_streams:
                        game_id      = stream.get('game_id')
                        stream_title = stream.get('title')
                        thumbnail    = stream.get('thumbnail_url')
                        viewer_count = stream.get('viewer_count')
                        user_id      = stream.get('user_id')

                        game = self.twitch_api.get_game_info(id=game_id)

                        game_boxart = game.get('box_art_url')
                        game_name   = game.get('name')

                        followers_count = self.twitch_api.get_followers_count(user_id)

                        streamer_info = self.twitch_api.get_user_info(id=user_id)

                        streamer_name = streamer_info.get('display_name')

                        json_embed = {
                            'description': 'https://www.twitch.tv/{}'.format(streamer_name),
                            'color':       0xFF0000,
                            'thumbnail': {
                                'url': game_boxart.replace('{width}', '240').replace('{height}', '336')
                            },
                            'image': {
                                'url': thumbnail.replace('{width}', '960').replace('{height}', '540')
                            },
                            'author': {
                                'name':     '{} is now streaming!'.format(streamer_name),
                                'icon_url': 'https://imgur.com/waJ7gpJ.jpg'
                            },
                            'fields': [
                                {
                                    'name':  'Now Playing',
                                    'value': game_name
                                },
                                {
                                    'name':  'Stream Title',
                                    'value': stream_title
                                },
                                {
                                    'name':   'Current Viewers',
                                    'value':  viewer_count,
                                    'inline': True
                                },
                                {
                                    'name':   'Followers',
                                    'value':  followers_count,
                                    'inline': True
                                }
                            ]
                        }

                        db_channel = self._get_db_channel_by_id(user_id)
                        message_id = db_channel.get('streaming_message_id')

                        # update stream message
                        if message_id:
                            await self.update_embed(embed=json_embed, channel=self.alert_channel_id, message_id=message_id)

                        # create new stream message
                        else:
                            message = await self.bot_embed(embed=json_embed, expiration=False, channel=self.alert_channel_id, trash=False)
                            
                            # update database with message id
                            self.twitch_channels_table.update({'streaming_message_id': message.id}, Query().id == user_id)
                # user is not stremaing on twitch
                else:
                    if db_twitch_streaming_message_id:
                        # remove message
                        channel = await self.get_channel(self.alert_channel_id)
                        try:
                            message = await self.bot.get_message(channel, db_twitch_streaming_message_id)
                            await self.delete_message(message)
                        except Exception as e:
                            print(e)
                        
                        self.twitch_channels_table.update({'streaming_message_id': None}, Query().id == db_twitch_id)

        except Exception as e:
            print(e)

    """ Misc Methods """

    def clean_number(self, number):
        return "{:,}".format(number)

    ##################
    # Private Methods
    ##################

    def _get_db_channel_by_id(self, id):
        return self.twitch_channels_table.search(Query().id == id)[0]

    def _all_twitch_channel_names(self, for_stream_info=False):
        channels = self.twitch_channels_table.all()

        if for_stream_info:
            return [('user_login',channel['name']) for channel in channels]

        return [channel['name'] for channel in channels]

    def _json_to_embed(self, json_embed):
        json_embed['timestamp'] = str(datetime.datetime.utcnow())

        embed = discord.Embed.from_data(json_embed)

        if json_embed.get('image'):
            embed.set_image(url=json_embed.get('image').get('url'))

        return embed

    async def _bot_to_discord(self, message=None, embed=None, expiration=10, channel=None, trash=True):
        if channel:
            channel = await self.get_channel(channel)
            message_in = await self.bot.send_message(channel, embed=embed)
        else:
            if message:
                message_in = await self.bot.say(message)
            elif embed:
                message_in = await self.bot.say(embed=embed)

        if trash:
            await self.bot.add_reaction(message_in, '🗑')

        # expire message or return message
        if expiration is not False:
            await self.delete_message(message_in, expiration)
        else:
            return message_in # only returns if message doesn't auto delete

def main():
    bot_helper = BotHelper("bot")
    breakpoint()

if __name__ == "__main__":
    main()