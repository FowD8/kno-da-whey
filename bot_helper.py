import discord
import asyncio
import datetime
from discord.ext.commands import Bot
from tinydb import TinyDB, Query
from twitch_api import TwitchAPI
from dateutil.parser import parse
import yaml
# debugging
from IPython import embed as breakpoint

class BotHelper(object):

    def __init__(self, bot, db, twitch_api):
        self.bot = bot
        self.db = db
        self.twitch_api = twitch_api
        self.twitch_channels_table = self.db.table('twitch_channels')
        self.timeouts_table = self.db.table('timeouts')

        secrets = yaml.load(open('secrets.yml', 'r'))
        self.bot_image = secrets['BOT_IMAGE']
        self.alert_channel_id = secrets['TWITCH_ALERT_CHANNEL_ID']

    """ Bot Messaging Methods """

    async def bot_say(self, message, expiration=10, channel=None, trash=True):
        return await self._bot_to_discord(message=message, expiration=expiration, channel=channel, trash=trash)

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
        # remove all
        if name.lower() == "all":
            streaming_message_ids = [streamer.get('streaming_message_id') for streamer in self.twitch_channels_table.all()]
            
            # remove all twitch alerts and purge table
            await self.remove_stream_embed(streaming_message_ids)
            self.twitch_channels_table.purge()

            await self.bot_say('removed all twitch channels from the list')
        # remove selected
        elif self.twitch_channels_table.contains(Query().name == name):
            streaming_message_id = [streamer.get('streaming_message_id') for streamer in self.twitch_channels_table.search(Query().name == name)]

            await self.remove_stream_embed(streaming_message_id)

            self.twitch_channels_table.remove(Query().name == name)
            await self.bot_say('removing `{}` from the list of twitch channels'.format(name)) 
        # selected does not exist
        else:
            await self.bot_say('`{}` is not on the list of twitch channels'.format(name))  

    async def twitch_show_channel(self, name):
        stream_info = self.twitch_api.get_stream_info(user_login=name.lower())

        if stream_info:
            stream_embed = self.create_stream_embed(stream_info)
            await self.bot_embed(embed=stream_embed, expiration=False)
        else:
            await self.bot_say('Sorry, but `{}` is not currently streaming'.format(name))

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

    """ Timeout Methods """

    async def timeout_add_user(self, server, user, timeout):
        if server.get_member(user):
            member = server.get_member(user)
        elif server.get_member_named(user):
            member = server.get_member_named(user)
        else:
            await self.bot_say('Could not find discord user with name or ID: `{}` *(case-sensitive)*'.format(user))

        if self.timeouts_table.contains(Query().id == member.id):
            await self.bot_say('`{}` is already on the timeout list'.format(member.name))
        else:
            self.timeouts_table.insert({
                'id':        member.id,
                'name':      member.name,
                'timestamp': str(datetime.datetime.utcnow() + datetime.timedelta(minutes=timeout))
            })
            await self.bot_say('added `{}` to the list users timed out'.format(member.name))

    async def timeout_remove_user(self):
        pass

    async def timeout_list_users(self):
        pass

    def timeout_check_user(self, user_id):
        return self.timeouts_table.contains(Query().id == user_id)

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
                    for stream_info in live_streams:
                        user_id = stream_info.get('user_id')
                        stream_embed = self.create_stream_embed(stream_info)

                        db_channel = self._get_db_channel_by_id(user_id)
                        message_id = db_channel.get('streaming_message_id')

                        # update stream message
                        if message_id:
                            await self.update_embed(embed=stream_embed, channel=self.alert_channel_id, message_id=message_id)

                        # create new stream message
                        else:
                            message = await self.bot_embed(embed=stream_embed, expiration=False, channel=self.alert_channel_id, trash=False)
                            
                            # update database with message id
                            self.twitch_channels_table.update({'streaming_message_id': message.id}, Query().id == user_id)
                # user is not stremaing on twitch
                else:
                    await self.remove_stream_embed(db_twitch_streaming_message_id)

        except Exception as e:
            print(e)

    def create_stream_embed(self, stream_info):
        game_id      = stream_info.get('game_id')
        stream_title = stream_info.get('title')
        thumbnail    = stream_info.get('thumbnail_url')
        viewer_count = stream_info.get('viewer_count')
        user_id      = stream_info.get('user_id')

        game = self.twitch_api.get_game_info(id=game_id)

        game_boxart = game.get('box_art_url')
        game_name   = game.get('name')

        followers_count = self.twitch_api.get_followers_count(user_id)

        streamer_info = self.twitch_api.get_user_info(id=user_id)

        streamer_name = streamer_info.get('display_name')

        return {
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
                    'value':  self.clean_number(viewer_count),
                    'inline': True
                },
                {
                    'name':   'Followers',
                    'value':  followers_count,
                    'inline': True
                }
            ]
        }

    async def remove_stream_embed(self, streaming_message_id):
        if type(streaming_message_id) is str or streaming_message_id == None:
            streaming_message_id = [streaming_message_id]

        for message_id in streaming_message_id:
            if message_id:
                # remove twitch alert
                channel = await self.get_channel(self.alert_channel_id)
                message = await self.bot.get_message(channel, message_id)
                await self.delete_message(message)

                # remove message_id from database
                self.twitch_channels_table.update({'streaming_message_id': None}, Query().streaming_message_id == message_id)

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

            if message:
                message_in = await self.bot.send_message(channel, message)
            elif embed:
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