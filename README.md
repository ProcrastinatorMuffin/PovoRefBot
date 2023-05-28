# Povo Referral Code Bot

This Telegram bot was made for [Nipponcoms](https://t.me/nipponcoms) and helps manage Povo referral codes. It accepts codes from users, stores them, and gives them out upon request.

## Features

The bot:

- Accepts Povo referral codes via DM or the /povo_add command in the chat.
- Stores codes with their usage count.
- Gives out a random code with the /povo command.
- Tracks usage of each code and removes them once their limit is reached.

## Setup

To set up and run the bot, follow these steps:

1. Clone this repository:

```
git clone https://gitlab.com/ihavepixelxd/povo_referral.git
```

2. Install the requirements:

```
pip install -r requirements.txt
```

3. Open the config.py file and change 'TG_API_TOKEN' to your actual Telegram bot API token.

4. Run database.py to initialize the SQLite database:

```
python database.py
```

5. Run bot.py to start the bot:

```
python bot.py
```

## Support

If you encounter any issues or have questions, feel free to reach out at telegram (@toshimikonakawa)