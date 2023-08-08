### PovoRefBot

PovoRefBot is a Telegram bot designed to help manage and distribute referral codes. Users can add, delete, and retrieve referral codes, making it a handy tool for communities that rely on sharing referral links.

#### Features:
- Add new referral codes.
- Retrieve a referral code.
- Delete an existing referral code.
- View all referral codes with their usage count.
- Rate limiting to ensure fair usage.
- Detailed logging to assist with debugging and monitoring.

#### Setup:
1. Clone the repository:
   ```bash
   git clone <repository_url>
   ```

2. Navigate to the project directory:
   ```bash
   cd PovoRefBot
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your bot token in `config.py`.

5. Run the bot:
   ```bash
   python bot.py
   ```

#### Database:
The bot uses an SQLite database to manage and store referral codes and user activity. The database schema includes tables for referral codes (`codes`) and user activity (`user_activity`).

#### Logging:
Detailed logging is implemented, especially around database operations. The bot uses a rotating log system with a maximum of 3 backup log files, each having a size limit of 5MB.

#### Future Enhancements:
- Provide admin controls to manage user access and permissions.

#### Contributing:
Feel free to fork the repository and submit pull requests for any improvements or features you'd like to add.

#### License:
[MIT License](LICENSE)
