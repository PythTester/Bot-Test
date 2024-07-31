## BNBOT README

## Overview

This project is a comprehensive and dynamic Discord bot built using the discord.py library, integrated with the Binance Smart Chain (BSC) via web3.py for handling blockchain interactions. The bot offers various features, including a virtual economy, role management, and mini-games, along with smart contract integration for cryptocurrency transactions.

## Features

**1. User Profiles and Economy**

User Data Management: Each user has a profile with statistics like level, experience points (XP), gold, and resources (fish, wood, ore).
Leveling System: Users gain XP through various activities, leveling up when enough XP is earned.
Virtual Economy: Users can earn and spend gold through activities such as hunting, fishing, chopping wood, and mining.

**2. Mini-Games**

Blackjack: A card game where users can bet gold.
Hi/Low: A guessing game where users predict if the next number will be higher or lower.
Dice Game: Users roll dice against the bot to win gold.

**3. Battles and Raids**

Battles: Users can challenge each other, betting troops and gold. The winner is decided based on troop strength.
Raids: Users can raid others to steal a percentage of their resources, with cooldowns to prevent frequent attacks.

**4. Resource Management and Shop**

Resource Gathering: Users can gather resources like fish, wood, and ore, which can be sold for gold.
Shop: A virtual shop allows users to buy or sell resources and gold using Binance Coin (BNB).

**5. Blockchain Integration**

BNB Deposits/Withdrawals: Users can deposit BNB to their profile and withdraw to an external wallet.
Token Transfers: Support for tipping other users in BNB or supported BEP-20 tokens.
BNB Balance Checking: Users can check their BNB and supported BEP-20 token balances.

**6. Role Management**

High Roller Role: Users can purchase a special role if they accumulate enough gold.
Administrator Tools: Commands for editing user data and managing messages are restricted to certain users.

## Setup Instructions

**1. Requirements**
```
Python 3.8+
discord.py (pip install discord.py)
web3.py (pip install web3)
SQLite3 (comes pre-installed with Python)
Other Python libraries: asyncio, logging, json, random, time
```
**2. Configuration**
```
Discord Bot Token: Update the bot.run('YOUR_BOT_TOKEN') line with your Discord bot token.
Game Data Channel: Replace GAME_DATA_CHANNEL_ID with the actual channel ID where game data will be sent.
Role IDs: Replace ROLE_ID with your server's role ID for the High Roller role.
BNB Shop Address: Set the SHOP_BNB_ADDRESS to the Binance Coin (BNB) address that will receive BNB payments.
```
**3. Database Initialization**

The bot uses SQLite to store user data. On the first run, the database will be initialized automatically with a table for storing user information.

**4. Running the Bot**

Execute the bot with:

```
python bot.py
Ensure that your environment variables are set correctly, especially your Discord bot token and Web3 HTTP provider URL.
```
## Commands Overview


**!hunt** - Go hunting and earn gold and XP.

**!fish** - Go fishing to catch fish and earn XP.

**!chop** - Chop wood to earn XP.

**!mine** - Mine ores to earn XP.

**!bet bj <amount>** - Play Blackjack.

**!bet hi_low <amount>** - Play Hi/Low.

**!bet dice <amount>** - Play Dice.

**!profile [user]** - View your or another user’s profile.

**!bag [user]** - View your or another user’s resource bag.

**!buy_troops <amount>** - Buy troops for battle.

**!battle <user> <troops> <gold>** - Challenge another user to a battle.

**!edit <user> <field> <value>** - Edit a user’s attributes (admin only).

**!shop** - Open the shop to buy/sell resources and roles.

**!deposit** - Generate a BNB deposit address.

**!withdraw <amount> <address>** - Withdraw BNB to an external address.

**!bals** - Check your BNB balance.

**!fee** - Check the current BNB transaction fee.

**!tip <user> <amount>** - Tip another user in BNB.


## License

This project is open-source and available under the MIT License.

## Contributions

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## Support

For issues or feature requests, please submit a ticket on the GitHub repository.

## Acknowledgments

Thanks to the creators of discord.py and web3.py for their excellent libraries.
Special thanks to the community for their support and contributions.
