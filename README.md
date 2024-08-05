## Discord RPG Bot with Web3 Integration

## Overview

This project is a comprehensive and dynamic Discord bot built using the discord.py library, integrated with the Binance Smart Chain (BSC) via web3.py for handling blockchain interactions. The bot offers various features, including a virtual economy, role management, and mini-games, along with smart contract integration for cryptocurrency transactions.

## Features 🪐

**RPG Activities:** Users can engage in hunting, fishing, chopping wood, and mining to earn in-game resources and experience points.

**Economy and Currency:** The bot manages an in-game currency system (gold) and allows users to convert between resources and gold. Users can also manage Binance Coin (BNB) balances and interact with the Binance Smart Chain.

**Games and Challenges:** Includes games like Blackjack, Dice, Hi and Low, and trivia challenges. Users can also challenge others to battles, risking their resources and gold.

**Shop System:** Users can buy and sell resources, purchase gold using BNB, and claim special roles.

**Leaderboard:** View top users based on various metrics, such as BNB balance, win/loss ratio, and troop count.

**Automated Processes:** Auto-mining feature that allows users to collect resources automatically over time.

**Web3 Integration:** Users can generate BNB deposit addresses, check BNB balances, and transfer BNB or BEP-20 tokens to other users.

## Setup Instructions ➕

**Prerequisites**
```
Python 3.8+
A Discord Bot Token
Binance Smart Chain node URL (e.g., https://bsc-dataseed.binance.org/)
discord.py (pip install discord.py)
web3.py (pip install web3)
SQLite3 (comes pre-installed with Python)
Other Python libraries: asyncio, logging, json, random, time
```

## Installation ➕

**1. Clone the repository:**
```
git clone https://github.com/your-username/discord-rpg-bot.git
cd discord-rpg-bot
```
**2. Install the required Python packages:**
```
pip install -r requirements.txt
```

**4. Initialize the database:**
```
python initialize_db.py
```

## Running the Bot
```
python bot.py
```

## Command Overview 📟

**Adventure & Resource Gathering** 🏹

- **!hunt:** Go hunting to earn gold and XP.

- **!fish:** Catch fish to earn XP.

- **!chop:** Chop wood to earn XP.

- **!mine:** Mine ores to earn XP.

**Economy Management** 💸

- **!profile [user]:** View your profile or another user's profile.

- **!bag [user]:** View your resource bag or another user's bag.

- **!troops:** Buy troops for battle.

- **!battle [user] [troops] [gold]:** Challenge another user to a battle.

- **!shop:** Open the shop to buy/sell resources and special roles.

- **!daily:** Claim daily XP and Gold to speed up the process!

**Gambling & Games** 🎲

- **!bet bj [amount]:** Play a game of blackjack and bet gold.

- **!bet hl [amount]:** Play a high-low guessing game and bet gold.

- **!bet dice <amount>:** - Play a dice game and bet gold.

- **!trivia:** Start a trivia challenge.

**Web3 Integration** 💻

- **!deposit:** Generate a BNB deposit address.

- **!withdraw [amount] [address]:** Withdraw BNB.

- **!bals:** Check your BNB and token balances.

- **!fee:** Check the current BNB transaction fee.

- **!tip [user] [amount]:** Tip another user in BNB or other supported tokens.

- **!airdrop [token] [amount] [#]:** Airdrop tokens to specified # of users. 

- **!lb:** View the leaderboard.

**Administration** 🏛️

- **!edit [user] [field] [value]:** - Edit a user's data (Admin only).
- **!prune [number]:** - Delete a specified number of messages (Admin only).

**Miscellaneous** 🖇️

- **!s <category> <suggestion>:** - Submit a suggestion to the admins.

## Database Structure 🌐

**your_data.db**
- users: Stores user profiles, including levels, XP, gold, resources, and Web3 information.

**your_database.db**
- user_stats: Tracks cumulative stats such as total fish caught, wood chopped, ore mined, and monsters defeated.

## Database Schema #1 🌐

- **user_id:** Discord user ID (Primary Key)

- **level:** User level

- **xp:** Experience points

- **gold:** Gold balance

- **win_streak:** Current win streak

- **wins:** Number of wins

- **losses:** Number of losses

- **troops:** Number of troops owned

- **fish:** Amount of fish collected

- **wood:** Amount of wood collected

- **ore:** Amount of ore collected

- **bnb_address:** User's BNB deposit address

- **bnb_private_key:** User's BNB private key

- **bnb_balance:** User's BNB balance

## Database Schema #2 🌐

- **user_id:** This is the primary key, uniquely identifying each user. It's typically the Discord user ID.

- **total_fish:** This column keeps a cumulative count of how many fish the user has caught.

- **total_wood:** This column tracks the total amount of wood the user has chopped.

- **total_ore:** This column stores the total amount of ore the user has mined.

- **total_monsters:** This column holds the total number of monsters the user has defeated.

## Web3 Integration 🌐

The bot connects to the Binance Smart Chain via Web3, allowing users to manage BNB and BEP-20 token balances, perform transactions, and interact with smart contracts.

## Supported Tokens 🪙

- BNB
- CAKE
- BUSD
- USDT
- ETH
- DOT
- ADA
- LINK
- UNI

## Error Handling 🛑

The bot includes error handling mechanisms to log and report issues to a designated Discord channel, ensuring smooth operation and quick troubleshooting.

## Security Considerations 🚨

**Private Keys:** The bot stores BNB private keys for users. Ensure these are securely handled and never exposed in logs or outputs.

**Role Permissions:** Ensure the bot's role in Discord has appropriate permissions, especially for commands like !edit, !prune, and others that affect server content.

## License

This project is open-source and available under the MIT License.

## Contributions

Contributions are welcome! Please open an issue or submit a pull request with any changes or enhancements.

## Support 🙏

For issues or feature requests, please submit a ticket on the GitHub repository.

## Acknowledgments

Thanks to the creators of discord.py and web3.py for their excellent libraries.
Special thanks to the community for their support and contributions.
