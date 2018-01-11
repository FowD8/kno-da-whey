from requests import get

# debugging
from IPython import embed as breakpoint

class TwitchAPI(object):

    def __init__(self, client_id):
        self.client_id = client_id

    def get_game_info(self, id=None, name=None):
        return self._get_info(id=id, name=name, endpoint='games')

    def get_user_info(self, id=None, name=None):
        return self._get_info(id=id, login=name, endpoint='users')

    def get_stream_info(self, user_id=None, user_login=None):
        return self._get_info(user_id=user_id, user_login=user_login, endpoint='streams')

    def get_followers_count(self, user_id, clean=True):
        params={
            'to_id': user_id, 
            'first': '1'
        }

        follows_info = self._get_endpoint('users/follows', params=params)

        if follows_info.get('total'):
            if clean:
                return self.clean_number(follows_info.get('total'))
            else:
                return follows_info.get('total')

    def clean_number(self, number):
        return "{:,}".format(number)

    ##################
    # Private Methods
    ##################

    def _get_info(self, id=None, name=None, login=None, user_id=None, user_login=None, endpoint=None):
        if type(id) == str:
            params = {'id': id}
        elif type(name) == str:
            params = {'name': name}
        elif type(login) == str:
            params = {'login': login}
        elif type(user_id) == str:
            params = {'user_id': user_id}
        elif type(user_login) == str:
            params = {'user_login': user_login}
        elif type(id) == list:
            params = id
        elif type(name) == list:
            params = name
        elif type(login) == list:
            params = login
        elif type(user_id) == list:
            params = user_id
        elif type(user_login) == list:
            params = user_login
        else:
            Exception('missing parameter')

        response = self._get_endpoint(endpoint, params=params)

        if response:
            if type(id) == str or type(name) == str or type(login) == str or type(user_id) == str or type(user_login) == str:
                return self._return_first_data(response)
            elif type(id) == list or type(name) == list or type(login) == list or type(user_id) == list or type(user_login) == list:
                return response.get('data')

    def _get_endpoint(self, endpoint, params=None):
        response = get(
            'https://api.twitch.tv/helix/{}'.format(endpoint),
            headers={'Client-ID': self.client_id},
            params=params
        )

        if response.status_code == 200:
            return response.json()

    def _return_first_data(self, response):
        return next(iter(response.get('data')), None)

def main():
    twitch_api = TwitchAPI("sdlsh9gh5zxwrb4ye041ft38znpvjt")
    game_info = twitch_api.get_game_info(name="Dark Souls 3")
    user_info = twitch_api.get_user_info(name="gamesdonequick")
    followers_count = twitch_api.get_followers_count(user_info.get('id'))

    users = [
        ('login','gamesdonequick'),
        ('login','fowd8'),
        ('login','ahlyssduh')
    ]

    temp = twitch_api.get_user_info(name=users)

    breakpoint()

if __name__ == "__main__":
    main()