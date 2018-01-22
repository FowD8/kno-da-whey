# Kno Da Whey

<img src="https://imgur.com/i3bLOXM.jpg" width="100">

# Settings

Create a `secrets.yml` file in the root directory with correct parameters

| Variable         				| Description                					 |
|-------------------------|--------------------------------------|
| BOT_TOKEN        				| App user bot token         					 |
| TWITCH_CLIENT_ID 				| Twitch API client_id token 					 |
| TWITCH_ALERT_CHANNEL_ID | Channel ID to write Twitch alerts to |
| BOT_IMAGE 							| URL of image to use for bot 				 |

# Usage

Use `python3 bot.py` to run the bot

## Commands

| Command                               | Description                                           |
|---------------------------------------|-------------------------------------------------------|
| !twitch channel add <channel_name>    | adds Twitch channel to list of channels to track      |
| !twitch channel remove <channel_name> | removes Twitch channel from list of channels to track |
| !twitch channel list                  | list of Twitch channels being tracked                 |
| !twitch channel show <channel_name>   | creates Twitch embed if user is streaming							|


# Output

Will create embed messages in specified channel to alert discord users when a user is streaming