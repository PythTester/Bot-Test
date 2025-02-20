import discord
from discord.ext import commands
from discord.ui import Button, View
import random
import asyncio
import sqlite3
from web3 import Web3
from eth_account import Account
import logging
import time
import json
import requests
from decimal import Decimal, getcontext

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Database setup
conn = sqlite3.connect('your_data.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        level INTEGER DEFAULT 1,
        xp INTEGER DEFAULT 0,
        gold INTEGER DEFAULT 0,
        win_streak INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0,
        losses INTEGER DEFAULT 0,
        troops INTEGER DEFAULT 0,
        fish INTEGER DEFAULT 0,
        wood INTEGER DEFAULT 0,
        ore INTEGER DEFAULT 0,
        bnb_address TEXT,
        bnb_private_key TEXT,
        bnb_balance REAL DEFAULT 0
    )
''')
conn.commit()

# Web3 setup
w3 = Web3(Web3.HTTPProvider('https://example-dataseed.binance.org/'))

# Define the ID of the game-data channel
GAME_DATA_CHANNEL_ID = 000000000000000000  # Replace with your channel ID

# Shop setup
SHOP_BNB_ADDRESS = "000000000000000000000000000000000000"
ROLE_ID = 000000000000000000  # Replace with your actual role ID
ROLE_COST_GOLD = 5_000_000_000  # 5B Gold
FISH_TO_GOLD_RATE = 155 # 1 fish = 25 gold
WOOD_TO_GOLD_RATE = 155 # 1 wood = 50 gold
ORE_TO_GOLD_RATE = 155  # 1 ore = 50 gold
BNB_TO_GOLD_RATE = 10_000_000_000  # 1 BNB = 10B gold
BNB_TO_GOLD_RATE_STR = f"{BNB_TO_GOLD_RATE // 1_000_000_000}B"

def get_your_data(user_id):
    c.execute('SELECT * FROM users WHERE user_id=?', (user_id,))
    row = c.fetchone()
    if row is None:
        c.execute('INSERT INTO users (user_id) VALUES (?)', (user_id,))
        conn.commit()
        return {"level": 1, "xp": 0, "gold": 0, "win_streak": 0, "wins": 0, "losses": 0, "troops": 0, "fish": 0, "wood": 0, "ore": 0, "bnb_address": None, "bnb_private_key": None, "bnb_balance": 0}
    return {"level": row[1], "xp": row[2], "gold": row[3], "win_streak": row[4], "wins": row[5], "losses": row[6], "troops": row[7], "fish": row[8], "wood": row[9], "ore": row[10], "bnb_address": row[11], "bnb_private_key": row[12], "bnb_balance": row[13]}

def update_your_data(user_id, data):
    c.execute('''
        UPDATE users
        SET level=?, xp=?, gold=?, win_streak=?, wins=?, losses=?, troops=?, fish=?, wood=?, ore=?, bnb_address=?, bnb_private_key=?, bnb_balance=?
        WHERE user_id=?
    ''', (data["level"], data["xp"], data["gold"], data["win_streak"], data["wins"], data["losses"], data["troops"], data["fish"], data["wood"], data["ore"], data["bnb_address"], data["bnb_private_key"], data["bnb_balance"], user_id))
    conn.commit()

def add_xp(user_id, amount):
    data = get_your_data(user_id)
    data["xp"] += amount
    while data["xp"] >= data["level"] * 100:
        data["xp"] -= data["level"] * 100
        data["level"] += 1
    update_your_data(user_id, data)

async def delete_message_after_delay(message, delay=30):
    await asyncio.sleep(delay)
    await message.delete()

async def delete_user_command(ctx):
    await ctx.message.delete()

async def send_error_to_channel(ctx, error):
    game_data_channel = bot.get_channel(GAME_DATA_CHANNEL_ID)
    if game_data_channel:
        embed = discord.Embed(
            title="❌ Error",
            description=f"An error occurred: {error}",
            color=0xff0000
        )
        await game_data_channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

@bot.event
async def on_command_error(ctx, error):
    await send_error_to_channel(ctx, error)

@bot.command(name="edit")
@commands.has_permissions(administrator=True)
async def edit(ctx, member: discord.Member, field: str, value: int):
    try:
        user_id = member.id
        data = get_your_data(user_id)
        
        if field not in data:
            await ctx.send("Invalid field.")
            await delete_user_command(ctx)
            return
        
        data[field] += value
        update_your_data(user_id, data)
        
        embed = discord.Embed(
            title="✅ User Data Edited",
            description=f"**{member.display_name}**'s `{field}` has been updated by `{value}`.",
            color=0x00ff00
        )
        embed.add_field(name="New Value", value=f"{data[field]}", inline=False)
        embed.set_footer(text=f"Edited by {ctx.author.display_name}")
        
        game_data_channel = bot.get_channel(GAME_DATA_CHANNEL_ID)
        if game_data_channel:
            await game_data_channel.send(embed=embed)
        await delete_user_command(ctx)
    except Exception as e:
        await send_error_to_channel(ctx, str(e))
        await delete_user_command(ctx)

# Unified monster data with custom emojis included
MONSTERS = [
    {
        "name": "Goblin",
        "gold": (50, 100),
        "xp": (10, 20),
        "description": "A sneaky goblin with a penchant for mischief!",
        "weight": 30,  # 30% chance
        "emoji": "👹"
    },
    {
        "name": "Orc",
        "gold": (100, 200),
        "xp": (15, 30),
        "description": "A brutish orc with a mean streak and a big club.",
        "weight": 30,  # 30% chance
        "emoji": "👺"
    },
    {
        "name": "Troll",
        "gold": (150, 300),
        "xp": (20, 35),
        "description": "A towering troll that regenerates its wounds.",
        "weight": 20,  # 20% chance
        "emoji": "👾"
    },
    {
        "name": "Wraith",
        "gold": (200, 400),
        "xp": (25, 40),
        "description": "A ghostly wraith that drains the life force of the living.",
        "weight": 15,  # 15% chance
        "emoji": "👻"
    },
    {
        "name": "Dragon",
        "gold": (300, 500),
        "xp": (30, 50),
        "description": "A fearsome dragon with scales as hard as steel.",
        "weight": 5,  # 5% chance
        "emoji": "🐉"
    }
]

def weighted_random_choice(monsters):
    total_weight = sum(monster['weight'] for monster in monsters)
    random_weight = random.uniform(0, total_weight)
    cumulative_weight = 0
    for monster in monsters:
        cumulative_weight += monster['weight']
        if random_weight <= cumulative_weight:
            return monster

@bot.command(name="hunt")
async def hunt(ctx):
    try:
        user_id = ctx.author.id

        # Choose a monster based on weights
        monster = weighted_random_choice(MONSTERS)
        gold_reward = random.randint(*monster["gold"])
        xp_reward = random.randint(*monster["xp"])

        # Update user's XP and gold
        add_xp(user_id, xp_reward)
        data = get_your_data(user_id)
        data["gold"] += gold_reward
        update_your_data(user_id, data)
        update_user_stats(user_id, {'monsters': 1})

        # Create the embed message
        embed = discord.Embed(
            title=f"{monster['emoji']} Hunt Result",
            color=0x8B0000  # Dark red color for hunting
        )
        
        embed.add_field(
            name="Monster Defeated",
            value=f"{ctx.author.mention} defeated a **{monster['name']}** {monster['emoji']}!\n{monster['description']}",
            inline=False
        )
        
        embed.add_field(
            name="Experience Gained",
            value=f"**{xp_reward}** XP",
            inline=True
        )
        
        embed.add_field(
            name="Total XP",
            value=f"**{data['xp']}/{data['level']*100}** XP (Level {data['level']})",
            inline=True
        )
        
        embed.add_field(
            name="Gold Received",
            value=f"**{gold_reward}** 💰 Gold",
            inline=False
        )
        
        # Optional: Replace with your monster image URL
        embed.set_thumbnail(url="https://example.com/monster_image.png")
        embed.set_footer(text="Keep hunting to earn more rewards!")
        
        # Send the embed message
        await ctx.send(embed=embed, delete_after=30)
        
        # Delete the user's command message immediately
        await delete_user_command(ctx)
    except Exception as e:
        await send_error_to_channel(ctx, str(e))


@bot.command(name="fish")
async def fish(ctx):
    try:
        user_id = ctx.author.id

        # Define fish types with their respective XP rewards and custom emojis
        fish_rewards = {
            "🐟 Salmon": {"xp": random.randint(8, 15), "emoji": "🐟"},
            "🐠 Trout": {"xp": random.randint(8, 20), "emoji": "🐠"},
            "🐡 Tuna": {"xp": random.randint(10, 30), "emoji": "🐡"},
            "🦈 Shark": {"xp": random.randint(15, 35), "emoji": "🦈"},
            "🐳 Whale": {"xp": random.randint(20, 50), "emoji": "🐳"}
        }

        # Choose a fish based on the defined probabilities
        fish = random.choices(
            population=list(fish_rewards.keys()),
            weights=[30, 30, 20, 15, 5],  # Adjust these weights for probability distribution
            k=1
        )[0]
        
        # Get the XP and emoji for the selected fish
        xp = fish_rewards[fish]["xp"]
        fish_emoji = fish_rewards[fish]["emoji"]

        # Update user data with XP and fish count
        add_xp(user_id, xp)
        data = get_your_data(user_id)
        data["fish"] += 1
        update_your_data(user_id, data)
        update_user_stats(user_id, {'fish': 1})

        # Create and send the embed message
        embed = discord.Embed(
            title=f"{fish_emoji} Fishing Result",
            description=f"You caught a **{fish}** {fish_emoji}!",
            color=0x1E90FF  # Dodger blue color for fishing
        )
        
        embed.add_field(
            name="Experience Gained",
            value=f"**{xp}** XP",
            inline=True
        )
        
        embed.add_field(
            name="Total XP",
            value=f"**{data['xp']}/{data['level']*100}** XP (Level {data['level']})",
            inline=True
        )
        
        embed.add_field(
            name="Fish Caught",
            value=f"**{data['fish']}** fish caught in total!",
            inline=False
        )
        
        embed.set_thumbnail(url="https://example.com/fish_image.png")  # Replace with your fish image URL
        embed.set_footer(text="Keep fishing to catch more rare fish!")

        await ctx.send(embed=embed, delete_after=30)
        

        # Delete the user's command message immediately
        await delete_user_command(ctx)
        
    except Exception as e:
        await send_error_to_channel(ctx, str(e))


@bot.command(name="chop")
async def chop(ctx):
    try:
        await ctx.message.delete()
        user_id = ctx.author.id

        # Define the types of wood, their probabilities, and the XP they give
        wood_types = {
            "🌳 Oak": {"chance": 50, "xp": (8, 16)},    # 50% chance, 8-16 XP
            "🌲 Pine": {"chance": 30, "xp": (16, 24)},   # 30% chance, 16-24 XP
            "🍁 Maple": {"chance": 15, "xp": (24, 32)},  # 15% chance, 24-32 XP
            "🌴 Mahogany": {"chance": 4, "xp": (32, 40)},  # 4% chance, 32-40 XP
            "🎋 Bamboo": {"chance": 1, "xp": (40, 50)}   # 1% chance, 40-50 XP
        }

        # Choose the wood based on the defined probabilities
        wood = random.choices(list(wood_types.keys()), weights=[wood["chance"] for wood in wood_types.values()], k=1)[0]

        # Calculate XP gained based on the type of wood
        xp = random.randint(*wood_types[wood]["xp"])
        add_xp(user_id, xp)

        # Update the user's data
        data = get_your_data(user_id)
        data["wood"] += 1
        update_your_data(user_id, data)
        update_user_stats(user_id, {'wood': 1})

        # Create and send the embed message
        embed = discord.Embed(
            title=f"🪓 Chopping Result",
            color=0x8B4513  # A brownish color for chopping wood
        )

        embed.add_field(
            name="Wood Chopped",
            value=f"You chopped some **{wood}** wood!",
            inline=False
        )

        embed.add_field(
            name="Experience Gained",
            value=f"**{xp}** XP",
            inline=True
        )

        embed.add_field(
            name="Total XP",
            value=f"**{data['xp']}/{data['level']*100}** XP (Level {data['level']})",
            inline=True
        )

        embed.set_thumbnail(url="https://example.com/wood_image.png")  # Replace with your wood image URL
        embed.set_footer(text="Keep chopping to earn more rewards!")

        message = await ctx.send(embed=embed)

        # Automatically delete the message after 30 seconds
        await asyncio.sleep(20)
        await message.delete()

    except Exception as e:
        await send_error_to_channel(ctx, str(e))




@bot.command(name="mine")
async def mine(ctx):
    try:
        user_id = ctx.author.id
        
        # Define the ore types with their respective XP or gold rewards
        ore_rewards = {
            "<:stone:1242707938523615273> Iron": {"xp": random.randint(8, 18), "gold": 0},
            "<:gold:1242708201732964382> Gold": {"xp": 25, "gold": random.randint(51, 158)},  # Replace with your custom emoji ID
            "💎 Diamond": {"xp": random.randint(29, 36), "gold": 0}
        }
        
        # Randomly choose an ore and get its rewards
        ore = random.choices(
            population=list(ore_rewards.keys()),
            weights=[50, 30, 20],  # Adjust these weights for probability distribution
            k=1
        )[0]
        xp = ore_rewards[ore]["xp"]
        gold_reward = ore_rewards[ore]["gold"]

        # Update user's XP and ore count or gold
        if xp > 0:
            add_xp(user_id, xp)
        if gold_reward > 0:
            data = get_your_data(user_id)
            data["gold"] += gold_reward
            update_your_data(user_id, data)

        # Update ore count
        data = get_your_data(user_id)
        data["ore"] += 1
        update_your_data(user_id, data)
        update_user_stats(user_id, {'ore': 1})
        
        # Create the embed message
        embed = discord.Embed(
            title="🛠️ Mining Result",
            color=0xFFD700  # Gold color
        )
        
        embed.add_field(
            name="Ore Mined",
            value=f"{ore}",
            inline=False
        )
        
        if xp > 0:
            embed.add_field(
                name="Experience Gained",
                value=f"**{xp}** XP",
                inline=True
            )
            embed.add_field(
                name="Total XP",
                value=f"**{data['xp']}/{data['level']*100}** XP (Level {data['level']})",
                inline=True
            )
        
        if gold_reward > 0:
            embed.add_field(
                name="Gold Received",
                value=f"**{gold_reward}** 💰 Gold",
                inline=False
            )
        
        embed.set_thumbnail(url="https://example.com/ore_image.png")  # Replace with your ore image URL
        embed.set_footer(text="Keep mining to earn more rewards!")
        
        # Send the embed message
        await ctx.send(embed=embed, delete_after=20)
        
        # Delete the user's command message immediately
        await delete_user_command(ctx)
    except Exception as e:
        await send_error_to_channel(ctx, str(e))



@bot.command(name="bet")
async def bet(ctx, game: str, amount: int):
    try:
        if game.lower() == 'bj':
            await blackjack(ctx, amount)
        elif game.lower() == 'hl':
            await hl(ctx, amount)
        elif game.lower() == 'dice':
            await dice(ctx, amount)
    except Exception as e:
        await send_error_to_channel(ctx, str(e))

async def blackjack(ctx, amount):
    try:
        user_id = ctx.author.id
        data = get_your_data(user_id)
        
        if data["gold"] < amount:
            await ctx.send("You don't have enough gold to bet that amount.")
            await delete_user_command(ctx)
            return

        data["gold"] -= amount
        update_your_data(user_id, data)

        view = BlackjackView(ctx.author.id, amount)
        message = await ctx.send(embed=view.create_embed(), view=view)
        bot.loop.create_task(delete_message_after_delay(message))
        await delete_user_command(ctx)
    except Exception as e:
        await send_error_to_channel(ctx, str(e))

class BlackjackView(View):
    def __init__(self, player_id, bet_amount):
        super().__init__()
        self.player_id = player_id
        self.bet_amount = bet_amount
        self.player_hand = []
        self.dealer_hand = []
        self.player_score = 0
        self.dealer_score = 0
        self.deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4
        random.shuffle(self.deck)
        self.dealer_hand.append(self.deck.pop())
        self.player_hand.append(self.deck.pop())
        self.player_hand.append(self.deck.pop())
        self.update_scores()

    def update_scores(self):
        self.player_score = sum(self.player_hand)
        self.dealer_score = sum(self.dealer_hand)
        self.adjust_for_ace(self.player_hand)
        self.adjust_for_ace(self.dealer_hand)

    def adjust_for_ace(self, hand):
        """Adjusts score for Ace being either 1 or 11."""
        while sum(hand) > 21 and 11 in hand:
            hand[hand.index(11)] = 1

    async def reward_gold(self, interaction, win=False, blackjack=False, tie=False):
        try:
            data = get_your_data(self.player_id)
            if tie:
                data["gold"] += self.bet_amount
                update_your_data(self.player_id, data)
                await interaction.response.edit_message(embed=self.create_embed("It's a tie! You get your gold back."), view=None)
                return

            if win:
                gold = self.bet_amount * 2
                if blackjack:
                    bonus_msg = "**Blackjack! You won your bet back with a bonus!**"
                else:
                    bonus_msg = f"You won **{gold}** gold!"
                data["gold"] += gold
                data["wins"] += 1
                data["win_streak"] += 1
                if data["win_streak"] >= 5:
                    data["gold"] += 2000
                    bonus_msg += " **Streak bonus! You received an additional 2000 gold!**"
                update_your_data(self.player_id, data)
                await interaction.response.edit_message(embed=self.create_embed(bonus_msg), view=None)
            else:
                data["losses"] += 1
                data["win_streak"] = 0
                update_your_data(self.player_id, data)
                await interaction.response.edit_message(embed=self.create_embed("Dealer wins."), view=None)
        except Exception as e:
            await send_error_to_channel(interaction.message, str(e))

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if interaction.user.id != self.player_id:
                await interaction.response.send_message("This game is not for you!", ephemeral=True)
                return
            self.player_hand.append(self.deck.pop())
            self.update_scores()
            if self.player_score > 21:
                await self.reward_gold(interaction, win=False)
            else:
                await interaction.response.edit_message(embed=self.create_embed())
        except Exception as e:
            await send_error_to_channel(interaction.message, str(e))

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.red)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if interaction.user.id != self.player_id:
                await interaction.response.send_message("This game is not for you!", ephemeral=True)
                return
            # Dealer hits until they reach at least 17, but stops hitting at 16 to make it easier for the player.
            while self.dealer_score < 16:
                self.dealer_hand.append(self.deck.pop())
                self.update_scores()
            if self.dealer_score > 21 or self.player_score > self.dealer_score:
                if self.player_score == 21:
                    await self.reward_gold(interaction, win=True, blackjack=True)
                else:
                    await self.reward_gold(interaction, win=True)
            elif self.player_score == self.dealer_score:
                await self.reward_gold(interaction, tie=True)
            else:
                await self.reward_gold(interaction, win=False)
        except Exception as e:
            await send_error_to_channel(interaction.message, str(e))

    def create_embed(self, result=None):
        embed = discord.Embed(
            title="♦️ Blackjack",
            description="Hit to draw a card, Stand to end your turn.",
            color=0x0000ff
        )
        embed.add_field(name="Your Hand", value=f"{self.player_hand} (Score: {self.player_score})", inline=False)
        embed.add_field(name="Dealer's Hand", value=f"{self.dealer_hand} (Score: {self.dealer_score})", inline=False)
        if result:
            embed.add_field(name="Result", value=result, inline=False)
        return embed


async def hl(ctx, amount):
    try:
        user_id = ctx.author.id
        data = get_your_data(user_id)
        
        if data["gold"] < amount:
            await ctx.send("You don't have enough gold to bet that amount.")
            await delete_user_command(ctx)
            return

        data["gold"] -= amount
        update_your_data(user_id, data)

        number = random.randint(1, 100)
        view = HiLowView(ctx.author.id, number, amount)
        message = await ctx.send(embed=view.create_embed(), view=view)
        bot.loop.create_task(delete_message_after_delay(message))
        await delete_user_command(ctx)
    except Exception as e:
        await send_error_to_channel(ctx, str(e))

class HiLowView(View):
    def __init__(self, player_id, number, bet_amount):
        super().__init__()
        self.player_id = player_id
        self.number = number
        self.bet_amount = bet_amount

    @discord.ui.button(label="Higher", style=discord.ButtonStyle.green)
    async def higher(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.guess(interaction, True)
        except Exception as e:
            await send_error_to_channel(interaction.message, str(e))

    @discord.ui.button(label="Lower", style=discord.ButtonStyle.red)
    async def lower(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.guess(interaction, False)
        except Exception as e:
            await send_error_to_channel(interaction.message, str(e))

    async def guess(self, interaction: discord.Interaction, guess_higher):
        try:
            if interaction.user.id != self.player_id:
                await interaction.response.send_message("This game is not for you!", ephemeral=True)
                return
            new_number = random.randint(1, 100)
            data = get_your_data(self.player_id)
            if (guess_higher and new_number > self.number) or (not guess_higher and new_number < self.number):
                gold = self.bet_amount * 2
                data["gold"] += gold
                data["wins"] += 1
                data["win_streak"] += 1
                if data["win_streak"] >= 5:
                    data["gold"] += 2000
                    bonus_msg = f"You guessed correctly! The number was {new_number}. You won **{gold}** gold! **Streak bonus! You received an additional 2000 gold!**"
                else:
                    bonus_msg = f"You guessed correctly! The number was {new_number}. You won **{gold}** gold!"
                update_your_data(self.player_id, data)
                await interaction.response.edit_message(embed=self.create_embed(bonus_msg), view=None)
            else:
                data["losses"] += 1
                data["win_streak"] = 0
                update_your_data(self.player_id, data)
                await interaction.response.edit_message(embed=self.create_embed(f"You guessed wrong! The number was {new_number}."), view=None)
            self.number = new_number
            self.stop()
        except Exception as e:
            await send_error_to_channel(interaction.message, str(e))

    def create_embed(self, result=None):
        embed = discord.Embed(
            title="🔼🔽 Hi and Low",
            description="Guess if the next number is **higher** or **lower**.",
            color=0x0000ff
        )
        embed.add_field(name="Current Number", value=f"{self.number}", inline=False)
        if result:
            embed.add_field(name="Result", value=result, inline=False)
        return embed

async def dice(ctx, amount):
    try:
        user_id = ctx.author.id
        data = get_your_data(user_id)
        
        if data["gold"] < amount:
            await ctx.send("You don't have enough gold to bet that amount.")
            await delete_user_command(ctx)
            return

        data["gold"] -= amount
        update_your_data(user_id, data)

        view = DiceView(ctx.author.id, amount)
        message = await ctx.send(embed=view.create_embed(), view=view)
        bot.loop.create_task(delete_message_after_delay(message))
        await delete_user_command(ctx)
    except Exception as e:
        await send_error_to_channel(ctx, str(e))

class DiceView(View):
    def __init__(self, player_id, bet_amount):
        super().__init__()
        self.player_id = player_id
        self.bet_amount = bet_amount

    @discord.ui.button(label="Roll Dice", style=discord.ButtonStyle.green)
    async def roll_dice(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if interaction.user.id != self.player_id:
                await interaction.response.send_message("This game is not for you!", ephemeral=True)
                return
            player_roll = random.randint(1, 6)
            bot_roll = random.randint(1, 6)
            data = get_your_data(self.player_id)
            if player_roll > bot_roll:
                gold = self.bet_amount * 2
                data["gold"] += gold
                data["wins"] += 1
                data["win_streak"] += 1
                if data["win_streak"] >= 5:
                    data["gold"] += 2000
                    bonus_msg = f"You rolled **{player_roll}**, I rolled **{bot_roll}**. You win! You won **{gold}** gold! **Streak bonus! You received an additional 2000 gold!**"
                else:
                    bonus_msg = f"You rolled **{player_roll}**, I rolled **{bot_roll}**. You win! You won **{gold}** gold!"
                update_your_data(self.player_id, data)
                await interaction.response.edit_message(embed=self.create_embed(bonus_msg), view=None)
            elif player_roll < bot_roll:
                data["losses"] += 1
                data["win_streak"] = 0
                update_your_data(self.player_id, data)
                await interaction.response.edit_message(embed=self.create_embed(f"You rolled **{player_roll}**, I rolled **{bot_roll}**. I win!"), view=None)
            else:
                data["gold"] += self.bet_amount
                update_your_data(self.player_id, data)
                await interaction.response.edit_message(embed=self.create_embed(f"We both rolled **{player_roll}**. It's a tie! You get your gold back."), view=None)
        except Exception as e:
            await send_error_to_channel(interaction.message, str(e))

    def create_embed(self, result=None):
        embed = discord.Embed(
            title="🎲 Dice Game",
            description="Roll the dice and see if you can get a higher number.",
            color=0x0000ff
        )
        if result:
            embed.add_field(name="Result", value=result, inline=False)
        return embed

@bot.command(name="profile")
async def profile(ctx, member: discord.Member = None):
    try:
        user = member or ctx.author
        data = get_your_data(user.id)
        win_loss_ratio = data["wins"] / data["losses"] if data["losses"] > 0 else data["wins"]
        embed = discord.Embed(
            title=f"{user.name}'s Profile",
            description=f"**Level**: {data['level']}\n"
                        f"**XP**: {data['xp']}/{data['level']*100}\n"
                        f"**Gold**: {data['gold']}\n"
                        f"**Wins**: {data['wins']}\n"
                        f"**Losses**: {data['losses']}\n"
                        f"**Win/Loss Ratio**: {win_loss_ratio:.2f}\n"
                        f"**Win Streak**: {data['win_streak']}\n"
                        f"**Troops**: {data['troops']}",
            color=0x00ff00
        )
        embed.set_thumbnail(url=user.avatar.url)
        await ctx.send(embed=embed)
        await delete_user_command(ctx)
    except Exception as e:
        await send_error_to_channel(ctx, str(e))

@bot.command(name="bag")
async def bag(ctx, member: discord.Member = None):
    try:
        user = member or ctx.author
        your_data = get_your_data(user.id)
        your_data = get_user_stats(user.id)

        # Create an embed with current resources and totals
        embed = discord.Embed(
            title=f"🎒 {user.name}'s Bag",
            description="Here are your current resources and total stats:",
            color=0x00ff00
        )

        # Current resources in the user's bag
        embed.add_field(
            name="Current Fish",
            value=f"🐟 **{your_data['fish']}** fish",
            inline=False
        )

        embed.add_field(
            name="Current Wood",
            value=f"🌲 **{your_data['wood']}** wood",
            inline=False
        )

        embed.add_field(
            name="Current Ore",
            value=f"⛏️ **{your_data['ore']}** ore",
            inline=False
        )

        # Total stats from your_data
        embed.add_field(
            name="Total Fish Caught",
            value=f"🐟 **{your_data['fish']}** fish",
            inline=False
        )

        embed.add_field(
            name="Total Wood Chopped",
            value=f"🌲 **{your_data['wood']}** wood",
            inline=False
        )

        embed.add_field(
            name="Total Ore Mined",
            value=f"⛏️ **{your_data['ore']}** ore",
            inline=False
        )

        embed.add_field(
            name="Total Monsters Hunted",
            value=f"👹 **{your_data['monsters']}** monsters",
            inline=False
        )

        embed.set_thumbnail(url=user.avatar.url)
        embed.set_footer(text="Keep collecting and hunting to increase your totals!")

        await ctx.send(embed=embed)
        await delete_user_command(ctx)
    except Exception as e:
        await send_error_to_channel(ctx, str(e))


from discord.ui import View, Button

@bot.command(name="troops")
async def buy_troops(ctx):
    try:
        user_id = ctx.author.id
        data = get_your_data(user_id)
        troop_cost = 3  # Cost per troop in fish, wood, and ore

        # Create an embed showing the cost of troops
        embed = discord.Embed(
            title="🛡️ Buy Troops",
            description=f"Each troop costs **{troop_cost} Fish, {troop_cost} Wood, and {troop_cost} Ore**.\n\nHow many troops would you like to buy?",
            color=0x00ff00
        )
        embed.add_field(name="Your Resources", value=f"**Fish:** {data['fish']} 🐟\n**Wood:** {data['wood']} 🌲\n**Ore:** {data['ore']} ⛏️", inline=False)
        embed.set_footer(text="Type the number of troops you want to buy or click Cancel to stop.")

        # Create the view for buttons
        class TroopPurchaseView(View):
            def __init__(self):
                super().__init__(timeout=30)
                self.cancelled = False

            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("This action is not for you!", ephemeral=True)
                    return

                self.cancelled = True
                cancel_embed = discord.Embed(
                    title="❌ Purchase Cancelled",
                    description="You have cancelled the purchase of troops.",
                    color=0xff0000
                )
                await interaction.response.edit_message(embed=cancel_embed, view=None)
                self.stop()

        view = TroopPurchaseView()

        # Send the embed message with the view
        instruction_message = await ctx.send(embed=embed, view=view)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

        try:
            # Wait for the user's response with the number of troops or for them to cancel
            reply = await bot.wait_for('message', check=check, timeout=30.0)
            amount = int(reply.content)
            total_fish = amount * troop_cost
            total_wood = amount * troop_cost
            total_ore = amount * troop_cost

            # Check if the user cancelled the purchase
            if view.cancelled:
                await reply.delete()
                return

            # Check if the user has enough resources in your_data
            if data["fish"] >= total_fish and data["wood"] >= total_wood and data["ore"] >= total_ore:
                data["fish"] -= total_fish
                data["wood"] -= total_wood
                data["ore"] -= total_ore
                data["troops"] += amount
                update_your_data(user_id, data)
                confirmation_embed = discord.Embed(
                    title="✅ Troops Purchased",
                    description=f"You bought **{amount}** troops for **{total_fish} Fish, {total_wood} Wood, and {total_ore} Ore**.",
                    color=0x00ff00
                )
                confirmation_embed.add_field(name="Remaining Resources", value=f"**Fish:** {data['fish']} 🐟\n**Wood:** {data['wood']} 🌲\n**Ore:** {data['ore']} ⛏️", inline=False)
                confirmation_embed.set_footer(text="Your troops are ready for battle!")
            else:
                insufficient_resources = []
                if data["fish"] < total_fish:
                    insufficient_resources.append(f"**Fish:** Need {total_fish}, have {data['fish']}")
                if data["wood"] < total_wood:
                    insufficient_resources.append(f"**Wood:** Need {total_wood}, have {data['wood']}")
                if data["ore"] < total_ore:
                    insufficient_resources.append(f"**Ore:** Need {total_ore}, have {data['ore']}")

                confirmation_embed = discord.Embed(
                    title="❌ Insufficient Resources",
                    description="You don't have enough resources to buy those troops.",
                    color=0xff0000
                )
                for resource in insufficient_resources:
                    confirmation_embed.add_field(name="Resource Shortage", value=resource, inline=False)

            # Send the confirmation embed
            await ctx.send(embed=confirmation_embed, delete_after=30)
            await instruction_message.delete()
            await reply.delete()

        except asyncio.TimeoutError:
            if not view.cancelled:  # Only show timeout if not cancelled
                timeout_embed = discord.Embed(
                    title="⏰ Time's Up!",
                    description="You didn't respond in time. Please try the command again.",
                    color=0xffa500
                )
                await ctx.send(embed=timeout_embed, delete_after=10)
                await instruction_message.delete()

        await delete_user_command(ctx)
    except Exception as e:
        await send_error_to_channel(ctx, str(e))



@bot.command(name="battle")
async def battle(ctx, opponent: discord.Member, challenger_troops: int, gold: int):
    try:
        challenger_id = ctx.author.id
        opponent_id = opponent.id
        challenger_data = get_your_data(challenger_id)
        opponent_data = get_your_data(opponent_id)

        # Check if the challenger has enough troops and gold
        if challenger_data["troops"] < challenger_troops:
            await ctx.send("You don't have enough troops to start this battle.")
            return
        if challenger_data["gold"] < gold:
            await ctx.send("You don't have enough gold to bet.")
            return

        # Create the initial embed message
        battle_embed = discord.Embed(
            title="⚔️ Battle Challenge!",
            description=f"{ctx.author.mention} has challenged {opponent.mention} to a battle!\n\n"
                        f"**Troops:** {challenger_troops} 🪖\n"
                        f"**Gold:** {gold} 🪙",
            color=0xFF5733
        )
        battle_embed.set_footer(text="Opponent, choose the number of troops to send by clicking the button.")

        # Define the button for troop selection
        class TroopSelectionView(View):
            def __init__(self, opponent, max_troops, challenger_id, opponent_id, challenger_troops, gold):
                super().__init__(timeout=30)  # Set timeout for 30 seconds
                self.opponent = opponent
                self.max_troops = max_troops
                self.challenger_id = challenger_id
                self.opponent_id = opponent_id
                self.challenger_troops = challenger_troops
                self.gold = gold
                self.initial_message = None  # Initialize the initial message as None

            def set_initial_message(self, message):
                self.initial_message = message

            async def on_timeout(self):
                # Called when the opponent doesn't respond within the timeout
                npc_battle_embed = discord.Embed(
                    title="⚔️ No Response",
                    description=f"{self.opponent.mention} didn't respond in time. {ctx.author.mention}, do you want to battle an NPC instead?",
                    color=0xFFA500
                )
                npc_battle_embed.set_footer(text="You have 30 seconds to accept or decline the NPC battle.")

                class NPCBattleView(View):
                    def __init__(self, challenger_id, challenger_troops, gold):
                        super().__init__(timeout=30)
                        self.challenger_id = challenger_id
                        self.challenger_troops = challenger_troops
                        self.gold = gold

                    @discord.ui.button(label="Battle NPC", style=discord.ButtonStyle.green)
                    async def battle_npc(self, interaction: discord.Interaction, button: discord.ui.Button):
                        if interaction.user.id != self.challenger_id:
                            await interaction.response.send_message("This NPC battle option is not for you!", ephemeral=True)
                            return
                        
                        data = get_your_data(self.challenger_id)
                        
                        # 45% chance for the user to win the battle against the NPC
                        if random.random() <= 0.45:
                            # User wins
                            win_gold = self.gold * 2  # Double the bet if user wins
                            data["gold"] += win_gold
                            data["wins"] += 1  # Update win count
                            data["win_streak"] += 1  # Increment win streak

                            # Deduct only a portion of the troops since the user won
                            troops_lost = random.randint(1, self.challenger_troops // 2)
                            data["troops"] -= troops_lost

                            npc_win_embed = discord.Embed(
                                title="🏆 NPC Battle Result",
                                description=f"You won against the NPC!\n\n**Gold Gained:** {win_gold} 🪙\n**Troops Lost:** {troops_lost} 🪖",
                                color=0x00FF00
                            )
                            await interaction.response.edit_message(embed=npc_win_embed, view=None)
                        else:
                            # User loses
                            data["gold"] -= self.gold
                            data["losses"] += 1  # Update loss count
                            data["win_streak"] = 0  # Reset win streak

                            # Deduct all troops since the user lost
                            data["troops"] -= self.challenger_troops

                            npc_lose_embed = discord.Embed(
                                title="❌ NPC Battle Result",
                                description=f"You lost against the NPC...\n\n**Gold Lost:** {self.gold} 🪙\n**Troops Lost:** {self.challenger_troops} 🪖",
                                color=0xFF0000
                            )
                            await interaction.response.edit_message(embed=npc_lose_embed, view=None)

                        # Update the user's data
                        update_your_data(self.challenger_id, data)

                    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
                    async def decline_npc(self, interaction: discord.Interaction, button: discord.ui.Button):
                        if interaction.user.id != self.challenger_id:
                            await interaction.response.send_message("This option is not for you!", ephemeral=True)
                            return
                        await interaction.message.delete()

                npc_view = NPCBattleView(self.challenger_id, self.challenger_troops, self.gold)
                await self.initial_message.edit(embed=npc_battle_embed, view=npc_view)

            @discord.ui.button(label="Select Troops", style=discord.ButtonStyle.primary)
            async def select_troops(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != self.opponent.id:
                    await interaction.response.send_message("This battle is not for you!", ephemeral=True)
                    return

                # Create an embed asking how many troops to send
                selection_embed = discord.Embed(
                    title="⚔️ Troop Selection",
                    description=f"{self.opponent.mention}, how many troops do you want to send to the battle?\n\n"
                                f"**Available Troops:** {self.max_troops} 🪖",
                    color=0x3498DB
                )
                selection_embed.set_footer(text="Please type the number of troops in the chat.")
                await interaction.response.send_message(embed=selection_embed, ephemeral=True)

                def check_response(m):
                    return m.author.id == self.opponent.id and m.channel == interaction.channel

                try:
                    msg = await bot.wait_for('message', check=check_response, timeout=60)
                    opponent_troops = int(msg.content)

                    if opponent_troops > self.max_troops or opponent_troops <= 0:
                        error_embed = discord.Embed(
                            title="⚠️ Invalid Number",
                            description=f"You can only send up to **{self.max_troops}** troops! Please try again.",
                            color=0xE74C3C
                        )
                        await interaction.followup.send(embed=error_embed, ephemeral=True)
                        return
                    if opponent_data["gold"] < self.gold:
                        error_embed = discord.Embed(
                            title="⚠️ Not Enough Gold",
                            description="You don't have enough gold to match the bet. Please try again with a lower amount.",
                            color=0xE74C3C
                        )
                        await interaction.followup.send(embed=error_embed, ephemeral=True)
                        return

                    # Delete the initial battle challenge message
                    if self.initial_message:
                        await self.initial_message.delete()

                    # Proceed with the battle
                    await process_battle(interaction, self.challenger_id, self.opponent_id, self.challenger_troops, opponent_troops, self.gold)
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(
                        title="⏳ Timeout",
                        description="You took too long to respond. The battle request has timed out.",
                        color=0xE67E22
                    )
                    await interaction.followup.send(embed=timeout_embed, ephemeral=True)
                except ValueError:
                    error_embed = discord.Embed(
                        title="⚠️ Invalid Input",
                        description="Please enter a valid number of troops.",
                        color=0xE74C3C
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                except Exception as e:
                    logging.error(f"An unexpected error occurred: {e}")
                    error_embed = discord.Embed(
                        title="❌ Error",
                        description=f"An error occurred: {e}",
                        color=0xE74C3C
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)

        # Create the view and send the initial challenge message
        view = TroopSelectionView(opponent, opponent_data["troops"], challenger_id, opponent_id, challenger_troops, gold)
        initial_message = await ctx.send(embed=battle_embed, view=view)
        view.set_initial_message(initial_message)  # Set the initial message in the view
    except Exception as e:
        logging.error(f"An error occurred in the battle command: {e}")
        await send_error_to_channel(ctx, str(e))

async def process_battle(interaction, challenger_id, opponent_id, challenger_troops, opponent_troops, gold):
    try:
        challenger_data = get_your_data(challenger_id)
        opponent_data = get_your_data(opponent_id)

        # Fetch the Discord member objects for the challenger and opponent
        challenger_member = await bot.fetch_user(challenger_id)
        opponent_member = await bot.fetch_user(opponent_id)

        previous_message = None  # Track the previous message to delete it

        initial_challenger_troops = challenger_troops
        initial_opponent_troops = opponent_troops

        # Simulate battle progress with periodic troop loss updates
        for i in range(5):  # Changed from 3 to 5
            # Calculate losses for this round
            challenger_loss = random.randint(1, max(1, challenger_troops // 4))
            opponent_loss = random.randint(1, max(1, opponent_troops // 4))
            challenger_troops -= challenger_loss
            opponent_troops -= opponent_loss

            # Send update to the channel
            progress_embed = discord.Embed(
                title=f"⚔️ Battle Progress: Round {i + 1}",
                description=f"{challenger_member.display_name} vs {opponent_member.display_name}\n"
                            f"**{challenger_loss}** challenger troops lost | **{opponent_loss}** opponent troops lost\n"
                            f"**Remaining Troops:**\n"
                            f"{challenger_member.display_name}: {challenger_troops} 🪖\n"
                            f"{opponent_member.display_name}: {opponent_troops} 🪖",
                color=0xFFA500
            )

            if previous_message:
                await previous_message.delete()

            previous_message = await interaction.followup.send(embed=progress_embed)

            # Pause before the next round
            await asyncio.sleep(2)

        if previous_message:
            await previous_message.delete()

        # Calculate the final winner based on remaining troops
        if challenger_troops > opponent_troops:
            winner_id = challenger_id
            loser_id = opponent_id
            winner_troops = challenger_troops
            loser_troops_lost = initial_opponent_troops - opponent_troops
        else:
            winner_id = opponent_id
            loser_id = challenger_id
            winner_troops = opponent_troops
            loser_troops_lost = initial_challenger_troops - challenger_troops

        winner_member = await bot.fetch_user(winner_id)
        loser_member = await bot.fetch_user(loser_id)

        # Update winner's and loser's data
        winner_data = get_your_data(winner_id)
        loser_data = get_your_data(loser_id)

        # Update the winner's troops to reflect only the surviving troops
        if winner_id == challenger_id:
            winner_data["troops"] = (winner_data["troops"] - initial_challenger_troops) + winner_troops
        else:
            winner_data["troops"] = (winner_data["troops"] - initial_opponent_troops) + winner_troops

        # Deduct the number of troops that died from the loser's total troop count
        loser_data["troops"] = max(0, loser_data["troops"] - loser_troops_lost)

        winner_data["wins"] += 1
        winner_data["win_streak"] += 1
        winner_data["gold"] += gold

        loser_data["losses"] += 1
        loser_data["win_streak"] = 0
        loser_data["gold"] -= gold

        update_your_data(winner_id, winner_data)
        update_your_data(loser_id, loser_data)

        # Announce the final result
        result_embed = discord.Embed(
            title="🏆 Final Battle Result",
            description=f"**{winner_member.display_name}** wins the battle against **{loser_member.display_name}**!\n\n"
                        f"**{winner_troops} troops** remain and **{gold} gold** gained!",
            color=0x00FF00
        )
        await interaction.followup.send(embed=result_embed)
    except Exception as e:
        logging.error(f"An error occurred during battle processing: {e}")
        await interaction.followup.send(f"An error occurred during battle processing: {e}", ephemeral=True)



class CloseButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.message.delete()
        except discord.errors.NotFound:
            pass  # Handle case where message was already deleted

@bot.command(name="commands")
async def commands(ctx):
    embed = discord.Embed(
        title="Bot Commands",
        description="Here is a list of all available commands:",
        color=0x00ff00
    )
    embed.add_field(name="!hunt", value="Go hunting and earn gold and XP.", inline=False)
    embed.add_field(name="!fish", value="Go fishing and catch fish to earn XP.", inline=False)
    embed.add_field(name="!chop", value="Chop wood to earn XP.", inline=False)
    embed.add_field(name="!mine", value="Mine ores to earn XP.", inline=False)
    embed.add_field(name="!bet bj <amount>", value="Play a game of blackjack and bet gold.", inline=False)
    embed.add_field(name="!bet hl <amount>", value="Play a Hi and Low guessing game and bet gold.", inline=False)
    embed.add_field(name="!bet dice <amount>", value="Play a dice game and bet gold.", inline=False)
    embed.add_field(name="!profile [user]", value="View your profile or another user's profile.", inline=False)
    embed.add_field(name="!bag [user]", value="View your bag or another user's bag of resources.", inline=False)
    embed.add_field(name="!buy_troops", value="Buy troops for battle.", inline=False)
    embed.add_field(name="!battle <user> <troops> <gold>", value="Challenge another user to a battle.", inline=False)
    embed.add_field(name="!shop", value="Open the shop to buy/sell resources and special roles.", inline=False)
    embed.add_field(name="!deposit", value="Generate a BNB deposit address.", inline=False)
    embed.add_field(name="!withdraw <amount> <address>", value="Withdraw BNB to an external address.", inline=False)
    embed.add_field(name="!bals", value="Check your BNB balance.", inline=False)
    embed.add_field(name="!fee <coin> <amount>", value="Check current BNB or BEP20 Token transaction fee.", inline=False)
    embed.add_field(name="!tip <user> <amount>", value="Tip another user in BNB.", inline=False)
    embed.add_field(name="!airdrop <coin> <amount> <# of users>", value="Airdrop BEP20 Tokens to other users.", inline=False)
    embed.add_field(name="!s <category> <suggestion>", value="Leave a suggestion for the admins to implement.", inline=False)
    embed.add_field(name="!trivia", value="Start a trivia game with random questions and earn rewards.", inline=False)

    view = CloseButtonView()  # Create the view with the close button
    await ctx.send(embed=embed, view=view)
    await delete_user_command(ctx)

@bot.command(name="shop")
async def shop(ctx):
    try:
        # Create an embed for the shop menu
        embed = discord.Embed(
            title="🏪 Welcome to the Shop!",
            description="You can sell your resources for gold or buy gold using BNB.",
            color=0x00ff00
        )
        embed.add_field(name="🐟 Sell Fish", value=f"{FISH_TO_GOLD_RATE} gold per fish", inline=False)
        embed.add_field(name="🌲 Sell Wood", value=f"{WOOD_TO_GOLD_RATE} gold per wood", inline=False)
        embed.add_field(name="⛏️ Sell Ore", value=f"{ORE_TO_GOLD_RATE} gold per ore", inline=False)
        embed.add_field(name="💰 Buy Gold with BNB", value=f"{BNB_TO_GOLD_RATE_STR} gold per 1 BNB", inline=False)
        embed.set_footer(text="Use the buttons below to interact with the shop.")

        # Send the shop embed with the view (buttons)
        view = ShopView(ctx.author.id)
        await ctx.send(embed=embed, view=view)

    except Exception as e:
        await send_error_to_channel(ctx, str(e))


class ShopView(View):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    @discord.ui.button(label="Sell Fish", style=discord.ButtonStyle.green)
    async def sell_fish(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.sell_resource(interaction, "fish", FISH_TO_GOLD_RATE, "🐟")

    @discord.ui.button(label="Sell Wood", style=discord.ButtonStyle.green)
    async def sell_wood(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.sell_resource(interaction, "wood", WOOD_TO_GOLD_RATE, "🌲")

    @discord.ui.button(label="Sell Ore", style=discord.ButtonStyle.green)
    async def sell_ore(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.sell_resource(interaction, "ore", ORE_TO_GOLD_RATE, "⛏️")

    @discord.ui.button(label="Buy Gold with BNB", style=discord.ButtonStyle.red)
    async def buy_gold(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.buy_gold_with_bnb(interaction)

    async def sell_resource(self, interaction: discord.Interaction, resource, rate, emoji):
        try:
            user_id = interaction.user.id
            data = get_your_data(user_id)
            resource_amount = data[resource]

            if resource_amount <= 0:
                await interaction.response.send_message(f"You don't have any {resource} to sell.", ephemeral=True)
                return

            gold_earned = resource_amount * rate
            data["gold"] += gold_earned
            data[resource] = 0  # Set resource to 0 after selling

            update_your_data(user_id, data)

            await interaction.response.send_message(f"You sold all your {emoji} {resource} and earned **{gold_earned}** gold!", ephemeral=True)
        except Exception as e:
            await send_error_to_channel(interaction.message, str(e))

    async def buy_gold_with_bnb(self, interaction: discord.Interaction):
        try:
            user_id = interaction.user.id
            data = get_your_data(user_id)

            # Calculate the gas fee
            gas_price = w3.eth.gas_price  # Get the current gas price
            gas_limit = 21000  # Standard gas limit for a simple BNB transfer
            fee_wei = gas_price * gas_limit
            fee_bnb = float(w3.from_wei(fee_wei, 'ether'))

            if data["bnb_balance"] <= 0:
                await interaction.response.send_message("You don't have any BNB to buy gold.", ephemeral=True)
                return

            # Ask the user how much BNB they want to spend
            await interaction.response.send_message("How much BNB do you want to spend?", ephemeral=True)

            def check(m):
                return m.author.id == user_id and m.channel == interaction.channel

            msg = await bot.wait_for('message', check=check, timeout=60)
            bnb_amount = float(msg.content)

            # Check if the user has enough BNB
            if bnb_amount + fee_bnb > data["bnb_balance"]:
                await interaction.followup.send(f"You don't have enough BNB to spend that amount. You need to account for the transaction fee of **{fee_bnb:.8f} BNB**.", ephemeral=True)
                return

            gold_purchased = int(bnb_amount * BNB_TO_GOLD_RATE)
            data["gold"] += gold_purchased
            data["bnb_balance"] -= (bnb_amount + fee_bnb)

            # Create the transaction to send BNB to the shop address
            tx = {
                'nonce': w3.eth.get_transaction_count(data["bnb_address"]),
                'to': SHOP_BNB_ADDRESS,
                'value': w3.to_wei(bnb_amount, 'ether'),
                'gas': gas_limit,
                'gasPrice': gas_price,
            }

            # Sign the transaction with the user's private key
            signed_tx = w3.eth.account.sign_transaction(tx, data["bnb_private_key"])
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            # Update the user's balance in the database
            update_your_data(user_id, data)

            embed = discord.Embed(
                title="💸 Gold Purchase Successful!",
                description=f"You bought **{gold_purchased} gold** with **{bnb_amount:.8f} BNB**.\nTransaction hash: [{tx_hash.hex()}](https://example.com/tx/{tx_hash.hex()})",
                color=0x00ff00
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("You took too long to respond. Please try again.", ephemeral=True)
        except Exception as e:
            await send_error_to_channel(interaction.message, str(e))

@bot.command(name="deposit")
async def deposit(ctx):
    try:
        user_id = ctx.author.id
        data = get_your_data(user_id)

        if data["bnb_address"] is None:
            account = Account.create()
            data["bnb_address"] = account.address
            data["bnb_private_key"] = account._private_key.hex()
            update_your_data(user_id, data)

        await ctx.author.send(f"Your BNB deposit address is: {data['bnb_address']}")
        await delete_user_command(ctx)
    except Exception as e:
        await send_error_to_channel(ctx, str(e))

class ConfirmWithdrawView(View):
    def __init__(self, user_id, amount, address, token, fee_bnb):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.amount = amount
        self.address = address
        self.token = token
        self.fee_bnb = fee_bnb
        self.confirmed = False

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This confirmation is not for you.", ephemeral=True)
            return

        self.confirmed = True
        try:
            await interaction.message.delete()
        except discord.errors.NotFound:
            pass  # Handle case where message was already deleted
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This action is not for you.", ephemeral=True)
            return

        self.confirmed = False
        try:
            await interaction.message.delete()
        except discord.errors.NotFound:
            pass  # Handle case where message was already deleted
        self.stop()


@bot.command(name="withdraw")
async def withdraw(ctx, amount: float, address: str, token: str = 'BNB'):
    try:
        await ctx.message.delete()

        user_id = ctx.author.id
        data = get_your_data(user_id)

        token = token.upper()

        if token not in TOKEN_CONTRACTS:
            await ctx.send(f"Unsupported token: {token}. Supported tokens are: BNB, {', '.join(TOKEN_CONTRACTS.keys())}")
            return

        gas_price = w3.eth.gas_price
        gas_limit = 21000 if token == 'BNB' else 60000  # Higher gas limit for token transfers
        fee_wei = gas_price * gas_limit
        fee_bnb = float(w3.from_wei(fee_wei, 'ether'))

        if token == 'BNB':
            transaction_fee_bnb = amount * 0.01
            total_fee_bnb = fee_bnb + transaction_fee_bnb
            if data["bnb_balance"] < (amount + total_fee_bnb):
                await ctx.send(f"You don't have enough BNB to withdraw {amount} BNB. You need at least {amount + total_fee_bnb} BNB to cover the withdrawal and fee.")
                return
        else:
            token_price_in_bnb = get_token_to_bnb_price(token)
            if token_price_in_bnb is None:
                await ctx.send(f"Could not retrieve {token} price in BNB. Please try again later.")
                return

            amount_in_bnb = amount * token_price_in_bnb
            transaction_fee_bnb = amount_in_bnb * 0.01
            total_fee_bnb = fee_bnb + transaction_fee_bnb

            token_contract = w3.eth.contract(address=Web3.to_checksum_address(TOKEN_CONTRACTS[token]), abi=ERC20_ABI)
            token_balance = token_contract.functions.balanceOf(data["bnb_address"]).call()
            token_balance_eth = float(w3.from_wei(token_balance, 'ether'))

            if token_balance_eth < amount:
                await ctx.send(f"You don't have enough {token} to withdraw {amount} {token}.")
                return

            if data["bnb_balance"] < total_fee_bnb:
                await ctx.send(f"You don't have enough BNB to cover the transaction fee of {total_fee_bnb:.8f} BNB.")
                return

        def format_decimal(value):
            return f"{value:.8f}".rstrip('0').rstrip('.')

        embed = discord.Embed(
            title="📤 Confirm Withdrawal",
            description=f"Are you sure you want to withdraw **{format_decimal(amount)} {token}** to `{address}`?\n\n"
                        f"**Network Gas Fee:** {format_decimal(fee_bnb)} BNB\n"
                        f"**Transaction Fee (1%):** {format_decimal(transaction_fee_bnb)} BNB\n"
                        f"**Total Fee:** {format_decimal(total_fee_bnb)} BNB",
            color=0x00ff00
        )
        view = ConfirmWithdrawView(user_id, amount, address, token, total_fee_bnb)
        confirmation_message = await ctx.send(embed=embed, view=view)

        await view.wait()
        await confirmation_message.delete()

        if view.confirmed:
            if token == 'BNB':
                data["bnb_balance"] -= (amount + total_fee_bnb)
                tx = {
                    'nonce': w3.eth.get_transaction_count(data["bnb_address"]),
                    'to': address,
                    'value': w3.to_wei(amount, 'ether'),
                    'gas': gas_limit,
                    'gasPrice': gas_price,
                }
                signed_tx = w3.eth.account.sign_transaction(tx, data["bnb_private_key"])
                tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

                fee_tx = {
                    'nonce': w3.eth.get_transaction_count(data["bnb_address"]) + 1,
                    'to': SHOP_BNB_ADDRESS,
                    'value': w3.to_wei(transaction_fee_bnb, 'ether'),
                    'gas': gas_limit,
                    'gasPrice': gas_price,
                }
                signed_fee_tx = w3.eth.account.sign_transaction(fee_tx, data["bnb_private_key"])
                fee_tx_hash = w3.eth.send_raw_transaction(signed_fee_tx.rawTransaction)
            else:
                token_contract_address = TOKEN_CONTRACTS[token]
                token_contract = w3.eth.contract(address=Web3.to_checksum_address(token_contract_address), abi=ERC20_ABI)

                tx = token_contract.functions.transfer(address, w3.to_wei(amount, 'ether')).build_transaction({
                    'from': data["bnb_address"],
                    'nonce': w3.eth.get_transaction_count(data["bnb_address"]),
                    'gas': gas_limit,
                    'gasPrice': gas_price,
                })
                signed_tx = w3.eth.account.sign_transaction(tx, data["bnb_private_key"])
                tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

                fee_tx = {
                    'nonce': w3.eth.get_transaction_count(data["bnb_address"]) + 1,
                    'to': SHOP_BNB_ADDRESS,
                    'value': w3.to_wei(transaction_fee_bnb, 'ether'),
                    'gas': gas_limit,
                    'gasPrice': gas_price,
                }
                signed_fee_tx = w3.eth.account.sign_transaction(fee_tx, data["bnb_private_key"])
                fee_tx_hash = w3.eth.send_raw_transaction(signed_fee_tx.rawTransaction)

            update_your_data(user_id, data)

            embed = discord.Embed(
                title="📤 Withdrawal Successful",
                description=f"Transaction hash: [{tx_hash.hex()}](https://example.com/tx/{tx_hash.hex()})\n"
                            f"Fee transaction hash: [{fee_tx_hash.hex()}](https://example.com/tx/{fee_tx_hash.hex()})",
                color=0x00ff00
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("Withdrawal cancelled.", delete_after=10)

    except Exception as e:
        await send_error_to_channel(ctx, str(e))




@bot.command(name="bals")
async def bals(ctx):
    try:
        user_id = ctx.author.id
        data = get_your_data(user_id)

        if data["bnb_address"] is None:
            await ctx.send("You don't have a BNB address. Use !deposit to generate one.")
            return

        # BNB Balance
        bnb_balance = w3.eth.get_balance(data["bnb_address"])
        bnb_balance = float(w3.from_wei(bnb_balance, 'ether'))

        # Contract addresses for the tokens
        token_contracts = {
            "CAKE": "000000000000000000000000000000000000000000",
            "BUSD": "000000000000000000000000000000000000000000",
            "USDT": "000000000000000000000000000000000000000000",
            "ETH": "000000000000000000000000000000000000000000",
            "DOT": "000000000000000000000000000000000000000000",
            "ADA": "000000000000000000000000000000000000000000",
            "LINK": "000000000000000000000000000000000000000000",
            "UNI": "000000000000000000000000000000000000000000"
        }

        # ABI for the token contracts
        token_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }
        ]

        def format_decimal(value):
            # Format the value to remove unnecessary trailing zeros
            return f"{value:.8f}".rstrip('0').rstrip('.')

        # Get balances for each token
        token_balances = {}
        for token_name, contract_address in token_contracts.items():
            try:
                contract = w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=token_abi)
                balance = contract.functions.balanceOf(data["bnb_address"]).call()
                token_balances[token_name] = float(w3.from_wei(balance, 'ether'))
            except Exception as token_error:
                await send_error_to_channel(ctx, f"Error retrieving {token_name} balance: {token_error}")
                token_balances[token_name] = 0.0

        # Update the database with the new BNB balance
        data["bnb_balance"] = bnb_balance
        update_your_data(user_id, data)

        # Create the embed with all balances
        embed = discord.Embed(
            title="💰 Your Balances",
            description="Here are your balances for BNB and supported BEP-20 tokens:",
            color=0x00ff00
        )
        embed.add_field(name="BNB Balance", value=f"**{format_decimal(bnb_balance)} BNB**", inline=False)

        for token_name, balance in token_balances.items():
            embed.add_field(name=f"{token_name} Balance", value=f"**{format_decimal(balance)} {token_name}**", inline=False)

        await ctx.send(embed=embed)
        await delete_user_command(ctx)
    except Exception as e:
        await send_error_to_channel(ctx, str(e))


# Function to get the current price of a token in BNB using CoinGecko API
def get_token_to_bnb_price(token):
    try:
        contract_address = TOKEN_CONTRACTS.get(token)
        if not contract_address:
            raise ValueError(f"Token {token} is not supported for price fetching.")

        # Use CoinGecko API to get token price in BNB
        url = f"https://api.coingecko.com/api/v3/simple/token_price/binance-smart-chain?contract_addresses={contract_address}&vs_currencies=bnb"
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code

        data = response.json()
        print(f"API Response for {token}: {data}")  # Debugging step: print the API response

        if contract_address in data and 'bnb' in data[contract_address]:
            token_price_in_bnb = float(data[contract_address]['bnb'])
            return token_price_in_bnb
        else:
            raise ValueError(f"Unexpected API response format: {data}")

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except ValueError as ve:
        print(f"Value error: {ve}")
        return None
    except Exception as e:
        print(f"General error: {e}")
        return None

@bot.command(name="fee")
async def fee(ctx, token: str = "BNB", amount: str = None):
    try:
        token = token.upper()

        # Check if the token is supported
        if token not in TOKEN_CONTRACTS:
            await ctx.send(f"Unsupported token: {token}. Supported tokens are: {', '.join(TOKEN_CONTRACTS.keys())}")
            return

        # Convert the amount to a float, if provided
        if amount is not None:
            try:
                amount = float(amount)
            except ValueError:
                await ctx.send("Please provide a valid number for the amount.")
                return

        # Determine the gas limit based on the token
        if token == "BNB":
            gas_limit = 21000  # Standard gas limit for BNB transfer
        else:
            gas_limit = 60000  # Higher gas limit for BEP-20 token transfers

        gas_price = w3.eth.gas_price  # Get the current gas price
        fee_wei = gas_price * gas_limit
        fee_bnb = float(w3.from_wei(fee_wei, 'ether'))  # Convert gas fee to BNB

        def format_decimal(value):
            # Format the value to remove unnecessary trailing zeros
            return f"{value:.8f}".rstrip('0').rstrip('.')

        transaction_fee_bnb = 0
        if token != "BNB" and amount is not None:
            # Fetch the price of the token in BNB using CoinGecko
            token_price_in_bnb = get_token_to_bnb_price(token)
            if token_price_in_bnb is None:
                await ctx.send(f"Could not retrieve {token} price in BNB. Please try again later.")
                return

            # Convert the token amount to BNB equivalent
            amount_in_bnb = amount * token_price_in_bnb

            # Calculate the 1% fee in BNB
            transaction_fee_bnb = amount_in_bnb * 0.01
        elif amount is not None:
            transaction_fee_bnb = amount * 0.01

        total_fee_bnb = fee_bnb + transaction_fee_bnb

        if amount is not None:
            description = (
                f"To withdraw **{format_decimal(amount)} {token}**, the estimated fees are:\n\n"
                f"**Network Gas Fee:** {format_decimal(fee_bnb)} BNB\n"
                f"**Transaction Fee (1%):** {format_decimal(transaction_fee_bnb)} BNB\n"
                f"**Total Fee:** {format_decimal(total_fee_bnb)} BNB"
            )
        else:
            description = (
                f"The current estimated fee for a standard {token} transaction is:\n\n"
                f"**Network Gas Fee:** {format_decimal(fee_bnb)} BNB"
            )

        # Add the bot's transaction fee statement
        description += (
            f"\n\n**Bot Transaction Fee:** 1% of the withdrawal amount."
        )

        embed = discord.Embed(
            title=f"💸 Withdrawal Fee Estimate ({token})",
            description=description,
            color=0x00ff00
        )
        await ctx.send(embed=embed)
        await delete_user_command(ctx)
    except Exception as e:
        await send_error_to_channel(ctx, str(e))


class ConfirmTipView(View):
    def __init__(self, user_id, member, amount, fee_bnb, token):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.member = member
        self.amount = amount
        self.fee_bnb = fee_bnb
        self.token = token  # Store the token if needed
        self.confirmed = False


    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This confirmation is not for you.", ephemeral=True)
            return

        self.confirmed = True
        self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This confirmation is not for you.", ephemeral=True)
            return

        # Delete the message when declined
        await interaction.message.delete()
        self.confirmed = False
        self.stop()

# A dictionary mapping token names to their contract addresses
TOKEN_CONTRACTS = {
    'BNB': None,  # BNB is native to the BSC network, so no contract is needed
    'CAKE': '0000000000000000000000000000000000000000000000',
    'BUSD': '0000000000000000000000000000000000000000000000',
    # Add other tokens here...
}

@bot.command(name="tip")
async def tip(ctx, member: discord.Member, amount: str, token: str = 'BNB'):
    try:
        # Debug: Print the raw amount and token
        print(f"Raw amount received: {amount}, Token: {token}")

        # Validate that the amount is a valid number
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be greater than 0.")
        except ValueError:
            await ctx.send("Invalid amount specified. Please enter a positive number.")
            await delete_user_command(ctx)
            return

        user_id = ctx.author.id
        recipient_id = member.id

        # Normalize the token name to uppercase
        token = token.upper()

        # Debug: Print the normalized token and amount after conversion
        print(f"Normalized amount: {amount}, Normalized Token: {token}")

        if token not in TOKEN_CONTRACTS:
            await ctx.send(f"Unsupported token: {token}. Supported tokens are: {', '.join(TOKEN_CONTRACTS.keys())}")
            await delete_user_command(ctx)
            return

        data = get_your_data(user_id)
        recipient_data = get_your_data(recipient_id)

        if token == 'BNB':
            token_balance = data['bnb_balance']
        else:
            # Retrieve the balance of the specified token
            token_balance = get_token_balance(data['bnb_address'], TOKEN_CONTRACTS[token])

        # Calculate gas fees
        gas_limit = 21000  # This might need to be adjusted for token transfers
        gas_price = w3.eth.gas_price  # Current gas price
        fee_wei = gas_price * gas_limit
        fee_bnb = float(w3.from_wei(fee_wei, 'ether'))

        if token == 'BNB' and token_balance < (amount + fee_bnb):
            await ctx.send(f"You don't have enough BNB to tip {amount:.8f} BNB. You need at least {(amount + fee_bnb):.8f} BNB to cover the tip and fee.")
            await delete_user_command(ctx)
            return
        elif token_balance < amount:
            await ctx.send(f"You don't have enough {token} to tip {amount:.8f} {token}.")
            await delete_user_command(ctx)
            return

        if recipient_data['bnb_address'] is None:
            await ctx.send(f"{member.display_name} does not have a BNB address set up.")
            await delete_user_command(ctx)
            return

        # Create the confirmation embed
        embed = discord.Embed(
            title="🎁 Confirm Tip",
            description=f"You are about to tip **{amount:.8f} {token}** to {member.display_name}.\n"
                        f"**Gas Fee:** {fee_bnb:.8f} BNB\n"
                        f"**Total Deducted:** {amount + fee_bnb:.8f} BNB (if BNB is being tipped)",
            color=0x00ff00
        )
        embed.set_footer(text="Please confirm or decline within 60 seconds.")

        # Create the confirmation view
        view = ConfirmTipView(user_id, member, amount, fee_bnb, token)
        await ctx.send(embed=embed, view=view)
        await delete_user_command(ctx)

        # Wait for the user's response
        await view.wait()

        if view.confirmed:
            if token == 'BNB':
                # Proceed with the BNB transaction
                tx = {
                    'nonce': w3.eth.get_transaction_count(data['bnb_address']),
                    'to': recipient_data['bnb_address'],
                    'value': w3.to_wei(amount, 'ether'),
                    'gas': gas_limit,
                    'gasPrice': gas_price,
                }
                signed_tx = w3.eth.account.sign_transaction(tx, data['bnb_private_key'])
                tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            else:
                # Proceed with the token transfer
                token_contract = w3.eth.contract(address=Web3.to_checksum_address(TOKEN_CONTRACTS[token]), abi=ERC20_ABI)
                tx = token_contract.functions.transfer(recipient_data['bnb_address'], w3.to_wei(amount, 'ether')).build_transaction({
                    'from': data['bnb_address'],
                    'nonce': w3.eth.get_transaction_count(data['bnb_address']),
                    'gas': gas_limit,
                    'gasPrice': gas_price,
                })
                signed_tx = w3.eth.account.sign_transaction(tx, data['bnb_private_key'])
                tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            # Update the sender and recipient balances in the database
            if token == 'BNB':
                data['bnb_balance'] -= (amount + fee_bnb)
                recipient_data['bnb_balance'] += amount
            else:
                update_token_balance(user_id, token, -amount)
                update_token_balance(recipient_id, token, amount)

            update_your_data(user_id, data)
            update_your_data(recipient_id, recipient_data)

            confirmation_embed = discord.Embed(
                title="🎉 Tip Successful",
                description=f"You tipped **{amount:.8f} {token}** to {member.display_name}.\n"
                            f"Transaction hash: [{tx_hash.hex()}](https://example.com/tx/{tx_hash.hex()})",
                color=0x00ff00
            )
            await ctx.send(embed=confirmation_embed)

        else:
            pass  # If declined, no further action is needed

    except Exception as e:
        await send_error_to_channel(ctx, str(e))

# Function to get token balance
def get_token_balance(address, contract_address):
    try:
        token_contract = w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=ERC20_ABI)
        balance = token_contract.functions.balanceOf(address).call()
        return w3.from_wei(balance, 'ether')
    except Exception as e:
        logging.error(f"Error retrieving {contract_address} balance: {str(e)}")
        return 0.0

# Function to update token balance in database
def update_token_balance(user_id, token, amount):
    # Implement a function to update the user's balance for the specified token
    pass

# ERC20 ABI (Simplified for balanceOf and transfer functions)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
]

# A dictionary to store the timestamps of the last raid for each raider-opponent pair
raid_cooldowns = {}

@bot.command(name="raid")
async def raid(ctx, target: discord.Member):
    try:
        raider_id = ctx.author.id
        target_id = target.id
        current_time = time.time()

        # Check if this raider-opponent pair is on cooldown
        if (raider_id, target_id) in raid_cooldowns:
            last_raid_time = raid_cooldowns[(raider_id, target_id)]
            cooldown_period = 30 * 60  # 30 minutes in seconds
            if current_time - last_raid_time < cooldown_period:
                remaining_time = int(cooldown_period - (current_time - last_raid_time))
                minutes = remaining_time // 60
                seconds = remaining_time % 60
                await ctx.send(f"⏳ You can raid {target.mention} again in {minutes} minutes and {seconds} seconds.")
                await delete_user_command(ctx)
                return

        # Proceed with the raid if not on cooldown
        raider_data = get_your_data(raider_id)
        target_data = get_your_data(target_id)

        # Calculate the amount to raid (up to 30% of each resource)
        max_raid_percentage = 0.3
        gold_raid = random.randint(0, int(target_data["gold"] * max_raid_percentage))
        fish_raid = random.randint(0, int(target_data["fish"] * max_raid_percentage))
        wood_raid = random.randint(0, int(target_data["wood"] * max_raid_percentage))
        ore_raid = random.randint(0, int(target_data["ore"] * max_raid_percentage))

        # Subtract the raided resources from the target and add to the raider
        target_data["gold"] -= gold_raid
        target_data["fish"] -= fish_raid
        target_data["wood"] -= wood_raid
        target_data["ore"] -= ore_raid

        raider_data["gold"] += gold_raid
        raider_data["fish"] += fish_raid
        raider_data["wood"] += wood_raid
        raider_data["ore"] += ore_raid

        # Update both users' data in the database
        update_your_data(raider_id, raider_data)
        update_your_data(target_id, target_data)

        # Update the raid cooldown
        raid_cooldowns[(raider_id, target_id)] = current_time

        # Create an appealing embed with emojis and markdown
        embed = discord.Embed(
            title="🏴‍☠️ Raid Successful!",
            description=f"{ctx.author.mention} raided {target.mention} and took their resources!",
            color=0xFFA500
        )
        embed.add_field(name="💰 Gold Stolen", value=f"**{gold_raid}** gold", inline=False)
        embed.add_field(name="🐟 Fish Stolen", value=f"**{fish_raid}** fish", inline=False)
        embed.add_field(name="🌲 Wood Stolen", value=f"**{wood_raid}** wood", inline=False)
        embed.add_field(name="⛏️ Ore Stolen", value=f"**{ore_raid}** ore", inline=False)
        embed.set_thumbnail(url=ctx.author.avatar.url)
        embed.set_footer(text="Better luck next time, defender!")
        
        await ctx.send(embed=embed)
        await delete_user_command(ctx)
    except Exception as e:
        await send_error_to_channel(ctx, str(e))

# Auto-mine functionality with cooldowns
auto_mine_cooldowns = {}

class AutoMineButton(View):
    def __init__(self, user_id):
        super().__init__(timeout=None)  # The timeout is set to None to keep the button active
        self.user_id = user_id

    @discord.ui.button(label="Start Auto-Mining Again", style=discord.ButtonStyle.green)
    async def start_auto_mine(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This button is not for you!", ephemeral=True)
            return

        # Run the auto_mine command again
        # Since this is now an interaction, pass `interaction` instead of `ctx`
        await auto_mine(interaction)


@bot.command(name="am")
async def auto_mine(ctx):
    await handle_auto_mine(ctx)

async def handle_auto_mine(ctx_or_interaction):
    try:
        user_id = ctx_or_interaction.author.id if hasattr(ctx_or_interaction, 'author') else ctx_or_interaction.user.id

        # Delete the user's command message if it's a command
        if hasattr(ctx_or_interaction, 'message'):
            await ctx_or_interaction.message.delete()

        current_time = time.time()

        # Check if the user is on cooldown
        if user_id in auto_mine_cooldowns:
            last_used_time = auto_mine_cooldowns[user_id]
            cooldown_period = 3 * 60  # 3 minutes in seconds
            if current_time - last_used_time < cooldown_period:
                remaining_time = int(cooldown_period - (current_time - last_used_time))
                minutes = remaining_time // 60
                seconds = remaining_time % 60
                await ctx_or_interaction.send(f"⏳ You can use the command again in {minutes} minutes and {seconds} seconds.")
                return

        # Notify the user that auto-mining has started
        embed = discord.Embed(
            title="⛏️ Auto-Mining Started!",
            description="You will collect resources every 30 seconds for the next 3 minutes.",
            color=0x00ff00
        )
        embed.set_footer(text="You'll be notified when the process is complete.")
        message = await ctx_or_interaction.send(embed=embed)

        # Delete the "Auto-Mining Started" message after 30 seconds
        await asyncio.sleep(30)
        await message.delete()

        # Set the cooldown for the user
        auto_mine_cooldowns[user_id] = current_time

        # Initialize the resource collection loop and track total resources collected
        total_fish = 0
        total_wood = 0
        total_ore = 0

        for _ in range(6):  # 6 cycles for 3 minutes (30 seconds per cycle)
            # Collect a random amount of resources
            fish_collected = random.randint(1, 6)
            wood_collected = random.randint(1, 6)
            ore_collected = random.randint(1, 6)

            # Update the total resources collected
            total_fish += fish_collected
            total_wood += wood_collected
            total_ore += ore_collected

            # Update the user's resources
            data = get_your_data(user_id)
            data["fish"] += fish_collected
            data["wood"] += wood_collected
            data["ore"] += ore_collected
            update_your_data(user_id, data)

            # Wait for 30 seconds before the next collection cycle
            await asyncio.sleep(30)

        # Notify the user that the auto-mining is complete and show total resources collected
        complete_embed = discord.Embed(
            title="⛏️ Auto-Mining Complete!",
            description="You have finished collecting resources. Here is what you gathered during the session:\n"
                        f"**Total Fish Collected**: {total_fish} 🐟\n"
                        f"**Total Wood Collected**: {total_wood} 🌲\n"
                        f"**Total Ore Collected**: {total_ore} ⛏️\n"
                        "You can use the `!am` command again or click the button below to start auto-mining again.",
            color=0x00ff00
        )
        view = AutoMineButton(user_id)
        await ctx_or_interaction.send(embed=complete_embed, view=view)

    except Exception as e:
        await send_error_to_channel(ctx_or_interaction, str(e))

# Define the role ID and cost
ROLE_ID = 000000000000000000# Replace with your actual role ID

@bot.command(name="highroller")
async def highroller(ctx):
    try:
        user_id = ctx.author.id
        data = get_your_data(user_id)

        # Check if the user has enough gold
        if data["gold"] < 5_000_000_000:
            embed = discord.Embed(
                title="🎲 High Roller Role",
                description=f"Sorry {ctx.author.mention}, you need **5B gold** to claim the High Roller role.",
                color=0xFF0000
            )
            embed.set_footer(text="Keep earning gold and try again!")
            await ctx.send(embed=embed)
            await delete_user_command(ctx)
            return

        role = ctx.guild.get_role(ROLE_ID)
        if not role:
            embed = discord.Embed(
                title="❌ Role Not Found",
                description="The High Roller role does not exist on this server. Please contact an admin.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            await delete_user_command(ctx)
            return

        if role in ctx.author.roles:
            embed = discord.Embed(
                title="🎲 High Roller Role",
                description=f"{ctx.author.mention}, you already have the High Roller role!",
                color=0x00FF00
            )
            await ctx.send(embed=embed)
            await delete_user_command(ctx)
            return

        # Deduct gold and assign the role
        data["gold"] -= 5_000_000_000
        update_your_data(user_id, data)
        await ctx.author.add_roles(role)

        embed = discord.Embed(
            title="🏅 High Roller Role Claimed!",
            description=f"Congratulations {ctx.author.mention}! You've claimed the **High Roller** role for **5B gold**!",
            color=0x00FF00
        )
        embed.add_field(name="Remaining Gold", value=f"{data['gold']} 🪙", inline=False)
        embed.set_thumbnail(url=ctx.author.avatar.url)
        embed.set_footer(text="Enjoy your new status!")
        await ctx.send(embed=embed)
        await delete_user_command(ctx)

    except Exception as e:
        await send_error_to_channel(ctx, str(e))

ALLOWED_USER_IDS = [295953756757950474]

@bot.command(name="prune")
async def prune(ctx, number: int):
    if ctx.author.id not in ALLOWED_USER_IDS:
        await ctx.send("You do not have permission to use this command.")
        return
    
    if number < 1:
        await ctx.send("Please specify a number greater than 0.")
        return
    
    # Deletes the command message itself first
    await ctx.message.delete()
    
    # Deletes the specified number of previous messages
    deleted = await ctx.channel.purge(limit=number)
    
    # Sends a confirmation message that auto-deletes after 5 seconds
    confirmation_msg = await ctx.send(f"🧹 Deleted {len(deleted)} messages.")
    await confirmation_msg.delete(delay=5)

@prune.error
async def prune_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send("Please provide a valid number of messages to delete.")
    else:
        await ctx.send(f"An error occurred: {error}")

@bot.command(name="lb")
async def leaderboard(ctx):
    try:
        # Delete the user's command message immediately
        await ctx.message.delete()

        def format_decimal(value, decimals=8):
            # Format the value to remove unnecessary trailing zeros
            return f"{value:.{decimals}f}".rstrip('0').rstrip('.')

        class LeaderboardView(View):
            def __init__(self):
                super().__init__(timeout=120)  # Timeout after 2 minutes of inactivity
                self.current_page = 0

            async def update_embed(self, interaction: discord.Interaction):
                if self.current_page == 0:
                    embed = await self.get_top_bnb_users()
                elif self.current_page == 1:
                    embed = await self.get_top_win_loss_users()
                elif self.current_page == 2:
                    embed = await self.get_top_troops_users()
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="BNB", style=discord.ButtonStyle.success)  # Changed to green
            async def bnb_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.current_page = 0
                await self.update_embed(interaction)

            @discord.ui.button(label="Win/Loss", style=discord.ButtonStyle.success)  # Changed to green
            async def win_loss_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.current_page = 1
                await self.update_embed(interaction)

            @discord.ui.button(label="Troops", style=discord.ButtonStyle.success)  # Changed to green
            async def troops_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.current_page = 2
                await self.update_embed(interaction)

            async def get_top_bnb_users(self):
                c.execute('''
                    SELECT user_id, bnb_balance FROM users ORDER BY bnb_balance DESC LIMIT 3
                ''')
                top_users = c.fetchall()

                embed = discord.Embed(
                    title="🏆 Top 3 BNB Balances",
                    description="Here are the users with the highest BNB balances!",
                    color=0xFFD700
                )

                medals = ["🥇", "🥈", "🥉"]
                for i, (user_id, bnb_balance) in enumerate(top_users):
                    user = await bot.fetch_user(user_id)
                    embed.add_field(
                        name=f"{medals[i]} {user.display_name}",
                        value=f"**Balance:** {format_decimal(bnb_balance)} BNB",
                        inline=False
                    )

                embed.set_footer(text="Keep earning BNB to climb the leaderboard!")
                return embed

            async def get_top_win_loss_users(self):
                c.execute('''
                    SELECT user_id, wins, losses, 
                    CASE 
                        WHEN losses = 0 THEN wins * 1.0  -- If losses are zero, just use the wins as the ratio
                        ELSE (wins * 1.0) / losses      -- Multiply wins by 1.0 to ensure floating-point division
                    END AS ratio
                    FROM users 
                    ORDER BY ratio DESC 
                    LIMIT 10
                ''')
                top_users = c.fetchall()

                embed = discord.Embed(
                    title="🏆 Top 10 Win/Loss Ratios",
                    description="Here are the users with the highest win/loss ratios!",
                    color=0x00FF00
                )

                for i, (user_id, wins, losses, ratio) in enumerate(top_users, start=1):
                    user = await bot.fetch_user(user_id)
                    embed.add_field(
                        name=f"{i}. {user.display_name}",
                        value=f"**Wins:** {wins}, **Losses:** {losses}, **Ratio:** {format_decimal(ratio, decimals=2)}",
                        inline=False
                    )

                embed.set_footer(text="Battle to improve your win/loss ratio!")
                return embed

            async def get_top_troops_users(self):
                c.execute('''
                    SELECT user_id, troops FROM users ORDER BY troops DESC LIMIT 5
                ''')
                top_users = c.fetchall()

                embed = discord.Embed(
                    title="🏅 Top 5 Troops",
                    description="Here are the users with the most troops!",
                    color=0x1E90FF
                )

                for i, (user_id, troops) in enumerate(top_users, start=1):
                    user = await bot.fetch_user(user_id)
                    embed.add_field(
                        name=f"{i}. {user.display_name}",
                        value=f"**Troops:** {troops}",
                        inline=False
                    )

                embed.set_footer(text="Recruit more troops to rise in the ranks!")
                return embed

        view = LeaderboardView()
        initial_embed = await view.get_top_bnb_users()  # Start with the first page

        # Send the leaderboard message
        message = await ctx.send(embed=initial_embed, view=view)

        # Auto-delete the leaderboard message after 60 seconds
        await message.delete(delay=60)

    except Exception as e:
        await send_error_to_channel(ctx, str(e))


# Predefined list of trivia questions grouped by category
TRIVIA_QUESTIONS = {
    "General Knowledge": [
        {
            "question": "What is the capital of France?",
            "options": ["Berlin", "London", "Paris", "Rome"],
            "correct_answer": "Paris"
        },
        {
            "question": "Which planet is known as the Red Planet?",
            "options": ["Earth", "Mars", "Jupiter", "Venus"],
            "correct_answer": "Mars"
        },
        {
            "question": "Who was known as The King of Pop?",
            "options": ["Michael Jackson", "Justin Timberlake", "Prince", "Harry Styles"],
            "correct_answer": "Michael Jackson"
        },
        {
            "question": "Which country is known as the Land of the Rising Sun?",
            "options": ["China", "South Korea", "Japan", "Thailand"],
            "correct_answer": "Japan"
        },
        {
            "question": "What is the largest island in the world?",
            "options": ["Madagascar", "Iceland", "Australia", "Greenland"],
            "correct_answer": "Greenland"
        },
        {
            "question": "Which artist painted the ceiling of the Sistine Chapel?",
            "options": ["Leonardo da Vinci", "Michelangelo", "Raphael", "Caravaggio"],
            "correct_answer": "Michelangelo"
        },
        {
            "question": "What is the tallest mountain in the world?",
            "options": ["K2", "Kangchenjunga", "Mount Everest", "Lhotse"],
            "correct_answer": "Mount Everest"
        },
        {
            "question": "Who was the first person to fly solo across the Atlantic Ocean?",
            "options": ["Wilbur Wright", "Amelia Earhart", "Howard Hughes", "Charles Lindbergh"],
            "correct_answer": "Charles Lindbergh"
        },
        {
            
            "question": "Which country has the most natural lakes?",
            "options": ["Finland", "United States", "Canada", "Russia"],
            "correct_answer": "Canada"  
        },
        {
            "question": "Which country is the largest producer of coffee in the world?",
            "options": ["Colombia", "Brazil", "Ethiopia", "Vietnam"],
            "correct_answer": "Brazil"
        },
        {
            "question": "What does the “D” in D-Day stand for?",
            "options": ["Departure", "Decision", "Deliverance", "Day"],
            "correct_answer": "Day"
        },
        {
            "question": "Who is the author of 'The Great Gatsby'?",
            "options": ["Ernest Hemingway", "T.S. Eliot", "John Steinbeck", "F. Scott Fitzgerald"],
            "correct_answer": "F. Scott Fitzgerald"
        },
        # Add more General Knowledge questions here
    ],
    "Science": [
        {
            "question": "Which country is the largest producer of coffee in the world?",
            "options": ["CO2", "O2", "H2O", "N2"],
            "correct_answer": "H2O"
        },
        {
            "question": "Which planet is closest to the Sun?",
            "options": ["Mercury", "Venus", "Earth", "Mars"],
            "correct_answer": "Mercury"
        },
        {
            "question": "How Far Is Earth From Mars?",
            "options": ["500M Miles", "14M Miles", "140M Miles", "1400M Miles"],
            "correct_answer": "140M Miles"
        },
         {
            "question": "What is the most abundant element in the universe?",
            "options": ["Carbon", "Nitrogen", "Hydrogen", "Oxygen"],
            "correct_answer": "Hydrogen"
        },
        {
            "question": "What type of bond involves the sharing of electron pairs between atoms?",
            "options": ["Metallic bond", "Covalent bond", "Ionic bond", "Hydrogen bond"],
            "correct_answer": "Covalent bond" 
        },
        {
            "question": "What is the chemical formula for methane?",
            "options": ["NH₃", "CO₂", "H₂O", "CH₄"],
            "correct_answer": "CH₄"
        },
        {
            "question": "What is the hardest substance in the human body?",
            "options": ["Bone", "Tooth enamel", "Cartilage", "Keratin"],
            "correct_answer": "Tooth enamel"
        },
        {
            "question": "What is the boiling point of water in Fahrenheit?",
            "options": ["100°F", "180°F", "212°F", "220°F"],
            "correct_answer": "212°F"
        },
        {
            "question": "What is the study of the interactions between organisms and their environment called?",
            "options": ["Botany", "Zoology", "Biology", "Ecology"],
            "correct_answer": "Ecology"
        },
        # Add more Science questions here
    ],
    "History": [
        {
            "question": "Who was the first President of the United States?",
            "options": ["Thomas Jefferson", "George Washington", "Abraham Lincoln", "John Adams"],
            "correct_answer": "George Washington"
        },
        {
            "question": "What year did World War II end?",
            "options": ["1941", "1939", "1945", "1950"],
            "correct_answer": "1945"
        },
        {
            "question": "How Many Years Did The 100 Year War Last?",
            "options": ["121", "100", "116", "153"],
            "correct_answer": "116"
        },
        {
            "question": "What year did the Berlin Wall fall?",
            "options": ["1987", "1991", "1989", "1993"],
            "correct_answer": "1989"  
        },
        {
            "question": "Who wrote the Communist Manifesto?",
            "options": ["Vladimir Lenin", "Leon Trotsky", "Joseph Stalin", "Karl Marx and Friedrich Engels"],
            "correct_answer": "Karl Marx and Friedrich Engels"
        },
        {
            "question": "Which battle is considered the turning point of the American Revolutionary War?",
            "options": ["The Battle of Bunker Hill", "The Battle of Saratoga", "The Battle of Yorktown", "The Battle of Lexington and Concord"],
            "correct_answer": "The Battle of Saratoga"
        },
        {
            "question": "What was the name of the first artificial Earth satellite, launched by the Soviet Union in 1957?",
            "options": ["Soyuz", "Luna", "Vostok", "Sputnik"],
            "correct_answer": "Sputnik"
        },
        {
            "question": "What ancient civilization built the Machu Picchu complex in Peru?",
            "options": ["The Aztecs", "The Incas", "The Mayans", "The Olmecs"],
            "correct_answer": "The Incas"
        },
        {
            "question": "What was the capital of the Byzantine Empire?",
            "options": ["Rome", "Athens", "Constantinople", "Alexandria"],
            "correct_answer": "Constantinople"
        },
        {
            "question": "What was the name of the ship that brought the Pilgrims to America in 1620?",
            "options": ["The Santa Maria", "The Pinta", "The Nina", "The Mayflower"],
            "correct_answer": "The Mayflower"
        },
        {
            "question": "In what year did the French Revolution begin?",
            "options": ["1776", "1789", "1815", "1793"],
            "correct_answer": "1789"
        },

        # Add more History questions here
    ],
    # Add more categories and questions here
}

# Fetch a random trivia question from the selected category
def get_random_trivia_question(category):
    question_data = random.choice(TRIVIA_QUESTIONS[category])
    return question_data['question'], question_data['correct_answer'], question_data['options']

@bot.command(name="trivia")
async def trivia(ctx):
    try:
        # Ask the user to select a category
        categories = list(TRIVIA_QUESTIONS.keys())
        category_options = "\n".join([f"{i+1}. {category}" for i, category in enumerate(categories)])
        
        embed = discord.Embed(
            title="🎲 Trivia Categories",
            description=f"Please select a category by typing the number:\n\n{category_options}",
            color=0x00ff00
        )
        category_message = await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit() and 1 <= int(m.content) <= len(categories)

        try:
            # Wait for the user to select a category
            category_response = await bot.wait_for('message', check=check, timeout=15.0)
            category_index = int(category_response.content) - 1
            selected_category = categories[category_index]

            # Delete the user's command message and category response
            await ctx.message.delete()
            await category_message.delete()
            await category_response.delete()

            # Get a random trivia question from the selected category
            question, correct_answer, all_answers = get_random_trivia_question(selected_category)

            # Embed the trivia question
            embed = discord.Embed(
                title=f"❓ Trivia Time! ({selected_category})",
                description=f"**{question}**\n\n",
                color=0x00ff00
            )
            for i, answer in enumerate(all_answers, start=1):
                embed.add_field(name=f"Option {i}", value=answer, inline=False)
            embed.set_footer(text="You have 15 seconds to answer!")

            trivia_message = await ctx.send(embed=embed)

            def check_answer(m):
                return m.author == ctx.author and m.channel == ctx.channel

            try:
                # Wait for the user's answer
                answer_message = await bot.wait_for('message', check=check_answer, timeout=15.0)
                data = get_your_data(ctx.author.id)

                # Delete the trivia question and user's answer
                await trivia_message.delete()
                await answer_message.delete()

                user_answer = answer_message.content.strip().lower()

                # Check if the user provided the correct answer or the correct option number
                if user_answer.isdigit() and 1 <= int(user_answer) <= len(all_answers):
                    user_answer_text = all_answers[int(user_answer) - 1].lower()
                else:
                    user_answer_text = user_answer

                if user_answer_text == correct_answer.lower():
                    gold_reward = random.randint(100, 500)  # Random gold reward between 100 and 500
                    data["gold"] += gold_reward
                    data["wins"] += 1  # Increment wins for correct answer
                    data["win_streak"] += 1  # Increment win streak for correct answer
                    update_your_data(ctx.author.id, data)
                    
                    # Correct Answer Embed
                    correct_embed = discord.Embed(
                        title="🎉 Correct Answer!",
                        description=f"{ctx.author.mention}, you got it right! 🥳\n\nYou earned **{gold_reward}** gold! 💰",
                        color=0x00ff00
                    )
                    correct_embed.add_field(
                        name="🏆 Your Reward",
                        value=f"**{gold_reward}** gold has been added to your account!\n",
                        inline=False
                    )
                    correct_embed.set_thumbnail(url="https://example.com/correct.png")  # Replace with an appropriate image URL
                    await ctx.send(embed=correct_embed, delete_after=20)  # Auto-delete after 20 seconds
                else:
                    data["losses"] += 1  # Increment losses for incorrect answer
                    data["win_streak"] = 0  # Reset win streak on incorrect answer
                    update_your_data(ctx.author.id, data)

                    # Incorrect Answer Embed
                    incorrect_embed = discord.Embed(
                        title="❌ Incorrect Answer",
                        description=f"Sorry {ctx.author.mention}, that's not the right answer. 😢\n\nThe correct answer was: **{correct_answer}**.",
                        color=0xff0000
                    )
                    incorrect_embed.add_field(
                        name="Better Luck Next Time!",
                        value="Don't worry, you can try again with the next question! 💪",
                        inline=False
                    )
                    incorrect_embed.set_thumbnail(url="https://example.com/wrong.png")  # Replace with an appropriate image URL
                    await ctx.send(embed=incorrect_embed, delete_after=20)  # Auto-delete after 20 seconds
            except asyncio.TimeoutError:
                # Delete the trivia question if the user runs out of time
                await trivia_message.delete()

                # Timeout Embed
                timeout_embed = discord.Embed(
                    title="⏰ Time's Up!",
                    description=f"Time ran out, {ctx.author.mention}! ⌛\n\nThe correct answer was: **{correct_answer}**.",
                    color=0xffa500
                )
                timeout_embed.add_field(
                    name="Try Again Soon!",
                    value="Make sure to answer quickly next time! ⏳",
                    inline=False
                )
                timeout_embed.set_thumbnail(url="https://example.com/timeout.png")  # Replace with an appropriate image URL
                await ctx.send(embed=timeout_embed, delete_after=20)  # Auto-delete after 20 seconds

        except asyncio.TimeoutError:
            await category_message.delete()
            await ctx.send(f"⏰ You took too long to select a category. Please try again, {ctx.author.mention}.", delete_after=20)

    except Exception as e:
        await send_error_to_channel(ctx, str(e))


## Format Tokens
def format_bnb(amount):
    return "{:.8f}".format(Decimal(amount).normalize()).rstrip('0').rstrip('.')

# Function to send BEP-20 tokens (like CAKE) on the blockchain
async def send_bep20_on_blockchain(sender_address, private_key, recipient_address, amount, token_contract_address):
    try:
        # Load the token contract
        token_contract = w3.eth.contract(address=Web3.to_checksum_address(token_contract_address), abi=ERC20_ABI)

        # Build the transaction
        nonce = w3.eth.get_transaction_count(sender_address)
        gas_price = w3.eth.gas_price
        gas_limit = 60000  # Token transfers require more gas than simple BNB transfers

        tx = token_contract.functions.transfer(recipient_address, w3.to_wei(amount, 'ether')).build_transaction({
            'from': sender_address,
            'nonce': nonce,
            'gas': gas_limit,
            'gasPrice': gas_price,
        })

        # Sign and send the transaction
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        if tx_receipt['status'] == 1:
            return tx_hash.hex()
        else:
            raise Exception("Transaction failed")
    except Exception as e:
        print(f"Failed to send BEP-20 token: {e}")
        return None

# Function to fetch the BEP-20 token balance for a user
def get_token_balance(address, token_contract_address):
    try:
        token_contract = w3.eth.contract(address=Web3.to_checksum_address(token_contract_address), abi=ERC20_ABI)
        balance = token_contract.functions.balanceOf(address).call()
        return w3.from_wei(balance, 'ether')
    except Exception as e:
        print(f"Error retrieving balance for {token_contract_address}: {e}")
        return Decimal(0)

# Function to send BNB on the blockchain
async def send_bnb_on_blockchain(sender_address, private_key, recipient_address, amount):
    try:
        nonce = w3.eth.get_transaction_count(sender_address)
        gas_price = w3.eth.gas_price
        gas_limit = 21000  # Standard gas limit for BNB transfer

        tx = {
            'nonce': nonce,
            'to': recipient_address,
            'value': w3.to_wei(amount, 'ether'),
            'gas': gas_limit,
            'gasPrice': gas_price
        }

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        if tx_receipt['status'] == 1:
            return tx_hash.hex()
        else:
            raise Exception("Transaction failed")
    except Exception as e:
        print(f"Failed to send BNB: {e}")
        return None

# Airdrop command
@bot.command(name="airdrop")
async def airdrop(ctx, token: str, total_amount: float, winners: int):
    try:
        user_id = ctx.author.id
        data = get_your_data(user_id)  # Use the existing get_your_data function

        # Normalize the token input
        token = token.upper()

        # Check if the token is supported
        if token not in TOKEN_CONTRACTS:
            await ctx.send("Unsupported token. Please use a supported token.")
            return

        # Determine if the airdrop is for BNB or a BEP-20 token
        if token == "BNB":
            amount_per_winner = Decimal(total_amount) / Decimal(winners)
            gas_limit = 21000  # Standard gas limit for BNB transfer
            transaction_function = send_bnb_on_blockchain
            user_balance = data['bnb_balance']
        else:
            amount_per_winner = Decimal(total_amount) / Decimal(winners)
            gas_limit = 60000  # Higher gas limit for token transfers
            transaction_function = send_bep20_on_blockchain

            # Fetch the token balance dynamically
            token_contract_address = TOKEN_CONTRACTS[token]
            user_balance = get_token_balance(data['bnb_address'], token_contract_address)

        gas_price = w3.eth.gas_price
        gas_fee = gas_limit * gas_price * winners  # Total gas fee for all transactions
        gas_fee_bnb = w3.from_wei(gas_fee, 'ether')

        # Check if the user has enough balance
        if token == "BNB":
            total_needed = Decimal(total_amount) + Decimal(gas_fee_bnb)
            if data['bnb_balance'] < total_needed:
                await ctx.send("You don't have enough BNB to cover the airdrop and transaction fees.")
                return
        else:
            if data['bnb_balance'] < Decimal(gas_fee_bnb):
                await ctx.send("You don't have enough BNB to cover the gas fees.")
                return
            if user_balance < Decimal(total_amount):
                await ctx.send(f"You don't have enough {token} to complete this airdrop.")
                return

        # Format the total amount and gas fee
        formatted_total_amount = format_bnb(total_amount)
        formatted_gas_fee = format_bnb(gas_fee_bnb)

        # Create the initial confirmation embed
        embed = discord.Embed(
            title="🎉 Airdrop Confirmation",
            description=f"You are about to start an airdrop of **{formatted_total_amount} {token}** for **{winners}** users.\n\n"
                        f"**Gas Fee (in BNB):** {formatted_gas_fee} BNB\n\n"
                        f"Do you want to proceed?",
            color=0x00FF00
        )
        embed.set_footer(text="Please confirm or decline within 60 seconds.")

        # Send the confirmation message and delete the original command message
        confirmation_message = await ctx.send(embed=embed)
        await ctx.message.delete()  # Delete the command message

        # Create the confirmation view
        class ConfirmAirdropView(View):
            def __init__(self, author_id, amount_per_winner, winners, token):
                super().__init__(timeout=60)
                self.author_id = author_id
                self.amount_per_winner = amount_per_winner
                self.winners = winners
                self.token = token

            @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != self.author_id:
                    await interaction.response.send_message("You are not authorized to confirm this airdrop.", ephemeral=True)
                    return

                # Start the airdrop process
                await self.start_airdrop(interaction, confirmation_message)

            @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
            async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != self.author_id:
                    await interaction.response.send_message("You are not authorized to decline this airdrop.", ephemeral=True)
                    return

                # Cancel the airdrop
                await confirmation_message.delete()
                await interaction.response.send_message("The airdrop has been canceled and the message has been deleted.", ephemeral=True)

            async def start_airdrop(self, interaction, original_message):
                # Update the message to show the airdrop has started
                embed = discord.Embed(
                    title="🎉 Airdrop Started!",
                    description=f"Be quick! The first {self.winners} users to claim will share **{format_bnb(self.amount_per_winner * self.winners)} {self.token}**!",
                    color=0x00FF00
                )
                embed.set_footer(text="Click the button below to claim your share!")
                
                # Create the button for users to claim the airdrop
                class AirdropButton(View):
                    def __init__(self, author_id, amount_per_winner, winners, token):
                        super().__init__(timeout=None)
                        self.author_id = author_id
                        self.amount_per_winner = amount_per_winner
                        self.winners = winners
                        self.claimed_users = []
                        self.token = token

                    @discord.ui.button(label="Claim", style=discord.ButtonStyle.primary)
                    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
                        if interaction.user.id in self.claimed_users:
                            await interaction.response.send_message("You have already claimed this airdrop!", ephemeral=True)
                            return

                        if len(self.claimed_users) < self.winners:
                            self.claimed_users.append(interaction.user.id)
                            await interaction.response.send_message(f"🎉 You have claimed your share of {format_bnb(self.amount_per_winner)} {self.token}!", ephemeral=True)

                            # Send the BNB or BEP-20 token to the user immediately after claiming
                            sender_data = get_your_data(self.author_id)
                            recipient_data = get_your_data(interaction.user.id)
                            
                            tx_hash = None
                            if self.token == "BNB":
                                tx_hash = await send_bnb_on_blockchain(sender_data['bnb_address'], sender_data['bnb_private_key'], recipient_data['bnb_address'], self.amount_per_winner)
                            else:
                                token_contract_address = TOKEN_CONTRACTS[self.token]
                                tx_hash = await send_bep20_on_blockchain(sender_data['bnb_address'], sender_data['bnb_private_key'], recipient_data['bnb_address'], self.amount_per_winner, token_contract_address)

                            if tx_hash:
                                if self.token == "BNB":
                                    recipient_data['bnb_balance'] += Decimal(self.amount_per_winner)
                                    sender_data['bnb_balance'] -= Decimal(self.amount_per_winner) + Decimal(gas_fee_bnb)
                                else:
                                    recipient_data[f'{self.token.lower()}_balance'] += Decimal(self.amount_per_winner)
                                    sender_data[f'{self.token.lower()}_balance'] -= Decimal(self.amount_per_winner)
                                    sender_data['bnb_balance'] -= Decimal(gas_fee_bnb)

                                update_your_data(interaction.user.id, recipient_data)
                                update_your_data(self.author_id, sender_data)

                                # Create a more appealing transaction message
                                transaction_embed = discord.Embed(
                                    title="💸 Transaction Successful!",
                                    description=f"**{format_bnb(self.amount_per_winner)} {self.token}** has been sent to <@{interaction.user.id}>!\n\n"
                                                f"**Transaction ID:** [`{tx_hash}`](https://example.com/tx/{tx_hash})",
                                    color=0x00FF00
                                )
                                transaction_embed.set_footer(text="Thank you for participating in the airdrop!")
                                transaction_embed.set_thumbnail(url="https://example.com/transaction-icon.png")  # Optional: Add a relevant icon

                                await interaction.followup.send(embed=transaction_embed, ephemeral=True)
                            else:
                                await interaction.followup.send("❌ Failed to send. Please contact support.", ephemeral=True)

                            if len(self.claimed_users) == self.winners:
                                button.disabled = True
                                await interaction.message.edit(view=self)
                                await self.end_airdrop(interaction, original_message)
                        else:
                            await interaction.response.send_message("Sorry, the airdrop has ended.", ephemeral=True)

                    async def end_airdrop(self, interaction, original_message):
                        # Edit the original message to indicate the end of the airdrop
                        claimed_users_mentions = ', '.join([f"<@{user_id}>" for user_id in self.claimed_users])
                        embed = discord.Embed(
                            title="🎉 Airdrop Ended!",
                            description=f"The airdrop has ended! Congratulations to the winners: {claimed_users_mentions}",
                            color=0x00FF00
                        )
                        await original_message.edit(embed=embed)

                # Update the original message to start the airdrop with a claim button
                view = AirdropButton(self.author_id, self.amount_per_winner, self.winners, self.token)
                await original_message.edit(embed=embed, view=view)

        # Send the confirmation message with buttons
        view = ConfirmAirdropView(user_id, amount_per_winner, winners, token)
        await confirmation_message.edit(embed=embed, view=view)

    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.command(name="s")
async def submit_suggestion(ctx, category: str, *, suggestion: str):
    try:
        # Validate the category
        category = category.lower()
        if category not in ["game", "wallet"]:
            await ctx.send("Invalid category! Please use either 'game' or 'wallet'.", delete_after=10)
            await ctx.message.delete()
            return
        
        # Delete the user's command message
        await ctx.message.delete()

        # Create the embed for the suggestion
        embed = discord.Embed(
            title="💡 New Suggestion",
            description=suggestion,
            color=0x00ff00
        )
        embed.add_field(name="Category", value=category.capitalize(), inline=False)
        embed.add_field(name="Suggested by", value=ctx.author.mention, inline=False)
        embed.set_footer(text=f"User ID: {ctx.author.id}")
        embed.timestamp = ctx.message.created_at

        # Use the new avatar method
        if ctx.author.avatar:
            embed.set_thumbnail(url=ctx.author.avatar.url)

        # Send the suggestion to the Suggestions channel
        suggestions_channel = bot.get_channel(1242646174662524990)  # Replace with your channel ID
        await suggestions_channel.send(embed=embed)

        # Send a confirmation message to the user
        confirmation_message = await ctx.send("Thank you for your suggestion! It has been submitted.", delete_after=10)

    except Exception as e:
        await ctx.send(f"An error occurred: {e}", delete_after=10)


import sqlite3

def create_your_database():
    # Connect to a new SQLite database (this will create the file if it doesn't exist)
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()

    # Create a table for tracking stats if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_stats (
        user_id INTEGER PRIMARY KEY,
        total_fish INTEGER DEFAULT 0,
        total_wood INTEGER DEFAULT 0,
        total_ore INTEGER DEFAULT 0,
        total_monsters INTEGER DEFAULT 0
    )
    """)

    # Commit and close the connection
    conn.commit()
    conn.close()

create_your_database()


def update_user_stats(user_id, new_stats):
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()

    # Ensure the user exists in the stats database
    cursor.execute("INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)", (user_id,))

    # Update the user's stats
    cursor.execute("""
        UPDATE user_stats
        SET total_fish = total_fish + ?,
            total_wood = total_wood + ?,
            total_ore = total_ore + ?,
            total_monsters = total_monsters + ?
        WHERE user_id = ?
    """, (
        new_stats.get('fish', 0),
        new_stats.get('wood', 0),
        new_stats.get('ore', 0),
        new_stats.get('monsters', 0),
        user_id
    ))

    conn.commit()
    conn.close()

def get_user_stats(user_id):
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT total_fish, total_wood, total_ore, total_monsters FROM user_stats WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    conn.close()

    if row:
        return {
            'fish': row[0],
            'wood': row[1],
            'ore': row[2],
            'monsters': row[3]
        }
    else:
        return {
            'fish': 0,
            'wood': 0,
            'ore': 0,
            'monsters': 0
        }

# Adapter function to convert datetime to a string
def adapt_datetime(dt):
    return dt.isoformat()

# Converter function to convert a string back to datetime
def convert_datetime(s):
    return datetime.datetime.fromisoformat(s.decode("utf-8"))

# Register the adapter and converter with sqlite3
sqlite3.register_adapter(datetime.datetime, adapt_datetime)
sqlite3.register_converter("timestamp", convert_datetime)

# Connect to the database with the custom converter
conn = sqlite3.connect('your_database.db', detect_types=sqlite3.PARSE_DECLTYPES)
c = conn.cursor()


@bot.command(name="daily")
async def daily(ctx):
    try:
        user_id = ctx.author.id
        data = get_your_data(user_id)
        
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Check if the user has claimed daily rewards in the last 24 hours
        if data["last_daily"] is not None:
            last_daily = data["last_daily"]
            delta = now - last_daily
            if delta < datetime.timedelta(hours=24):
                remaining_time = datetime.timedelta(hours=24) - delta
                hours, remainder = divmod(remaining_time.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                timeout_embed = discord.Embed(
                    title="⏳ Daily Reward Cooldown",
                    description=f"You have already claimed your daily reward!\n\nYou can claim again in **{hours}h {minutes}m {seconds}s**.",
                    color=0xFFA500
                )
                await ctx.send(embed=timeout_embed, delete_after=10)
                return

        # Randomize XP and gold rewards
        xp_reward = random.randint(200, 300)
        gold_reward = random.randint(1000, 3000)

        # Update user data
        data["xp"] += xp_reward
        data["gold"] += gold_reward
        data["last_daily"] = now
        update_your_data(user_id, data)

        # Create and send the reward embed
        embed = discord.Embed(
            title="🎁 Daily Reward Claimed!",
            description=f"**{ctx.author.mention}, you've received your daily rewards!**",
            color=0x00FF00
        )
        embed.add_field(
            name="XP Gained",
            value=f"**{xp_reward}** XP 💪",
            inline=True
        )
        embed.add_field(
            name="Gold Gained",
            value=f"**{gold_reward}** 🪙 Gold",
            inline=True
        )
        embed.add_field(
            name="Total XP",
            value=f"**{data['xp']}** XP",
            inline=True
        )
        embed.add_field(
            name="Total Gold",
            value=f"**{data['gold']}** Gold",
            inline=True
        )
        embed.set_thumbnail(url=ctx.author.avatar.url)
        embed.set_footer(text="Come back tomorrow for more rewards!")

        await ctx.send(embed=embed, delete_after=30)

        # Delete the user's command message immediately
        await ctx.message.delete()
    except Exception as e:
        await send_error_to_channel(ctx, str(e))

# Card information with probabilities for each card
cards = [
    {"id": 1, "name": "Zeus", "image": "https://i.imgur.com/Lq7SRsv.png", "probability": 0.05},
    {"id": 2, "name": "Hades", "image": "https://i.imgur.com/FoF4KFJ.png", "probability": 0.05},
    {"id": 3, "name": "Nebuchanezzar", "image": "https://i.imgur.com/RB9nAx6.png", "probability": 0.10},
    {"id": 4, "name": "Leonidas", "image": "https://i.imgur.com/yvkH8dP.png", "probability": 0.10},
    {"id": 5, "name": "Yue Fei", "image": "https://i.imgur.com/eMhlQIC.png", "probability": 0.10},
    {"id": 6, "name": "Alexander The Great", "image": "https://i.imgur.com/CvYdyqv.png", "probability": 0.10},
    {"id": 7, "name": "Alfred The Great", "image": "https://i.imgur.com/AQr2x9a.png", "probability": 0.20},
    {"id": 8, "name": "Napoleon", "image": "https://i.imgur.com/8qUQjP9.png", "probability": 0.20},
    {"id": 9, "name": "Saladin", "image": "https://i.imgur.com/dCN6r1N.png", "probability": 0.10}
]



# Dictionaries for user cards, marketplace listings, and balances
users_with_cards = {}
marketplace = {}
user_balances = {}
user_stats = {}  # This will store wins, losses, and gold

# Function to draw a card based on probability
def draw_card():
    return random.choices(
        cards,
        weights=[card["probability"] for card in cards],
        k=1
    )[0]

# Command to start the game and draw the first card
@bot.command(name="start")
async def start(ctx):
    user_id = ctx.author.id

    # Check if user already has received their first card
    if user_id in users_with_cards:
        embed = discord.Embed(
            title="You Already Have Your First Card!",
            description=f"{ctx.author.mention}, you can only use this command once to receive your first card!",
            color=discord.Color.red()
        )
        embed.set_footer(text="Use your cards wisely and trade in the marketplace!")
        await ctx.send(embed=embed)
        return

    # Draw the first card based on probability
    card = draw_card()
    users_with_cards[user_id] = [card]  # Store the first card in a list

    # Initialize user balance if they don't have one
    if user_id not in user_balances:
        user_balances[user_id] = 100  # Starting balance for new users

    # Initialize user stats
    user_stats[user_id] = {"wins": 0, "losses": 0, "gold": user_balances[user_id]}

    # Create an embedded message with the card information
    embed = discord.Embed(
        title="You Received Your First Card!",
        description=f"{ctx.author.mention}, congratulations on receiving your first card!",
        color=discord.Color.blue()
    )
    embed.add_field(name="Card Name", value=card["name"], inline=False)
    embed.set_image(url=card["image"])
    if card["name"] == "Zeus":
        embed.add_field(name="Special Message", value="You Received Zeus, the mighty ruler of Olympus!", inline=False)
    embed.set_footer(text="Enjoy your card and good luck!")
    await ctx.send(embed=embed)

@bot.command(name="sell")
async def sell(ctx, card_id: int, price: int):
    user_id = ctx.author.id

    # Check if user has any cards to sell
    if user_id not in users_with_cards or not users_with_cards[user_id]:
        await ctx.send(f"{ctx.author.mention}, you don't have any cards to sell!")
        return

    # Find the card by ID
    card_to_sell = next((card for card in users_with_cards[user_id] if card["id"] == card_id), None)

    if not card_to_sell:
        await ctx.send(f"{ctx.author.mention}, you don't have a card with that ID!")
        return

    # Add card to the marketplace with the correct seller ID
    marketplace[user_id] = {"card": card_to_sell, "price": price}

    # Remove the card from the user's inventory
    users_with_cards[user_id].remove(card_to_sell)

    # Send confirmation message
    embed = discord.Embed(
        title="Card Listed for Sale",
        description=f"{ctx.author.mention}, your card '{card_to_sell['name']}' has been listed for sale at {price} coins.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)



@bot.command(name="store")
async def store(ctx):
    print("Current marketplace listings:", marketplace)  # Debug print to see current listings

    # Check if the marketplace is empty
    if not marketplace:
        await ctx.send("The marketplace is currently empty.")
        return

    # Create an embed listing all cards in the marketplace
    embed = discord.Embed(
        title="Marketplace",
        description="Cards available for sale:",
        color=discord.Color.gold()
    )

    for seller_id, listing in marketplace.items():
        card = listing["card"]
        price = listing["price"]

        try:
            # Attempt to fetch the seller as a member in the current guild
            seller = await ctx.guild.fetch_member(seller_id)  # Fetch member from the API
            seller_name = seller.display_name  # Use the display name if found
        except discord.NotFound:
            seller_name = "Unknown User"  # Fallback if seller is not found

        embed.add_field(
            name=f"{card['name']} (ID: {card['id']}) - {price} coins",
            value=f"Seller: {seller_name}",
            inline=False
        )

    await ctx.send(embed=embed)



@bot.command(name="buycard")
async def buycard(ctx, seller: discord.Member, card_id: int):
    buyer_id = ctx.author.id
    seller_id = seller.id

    # Check if the seller has cards listed in the marketplace
    if seller_id not in marketplace:
        await ctx.send(f"{seller.mention} doesn't have a card listed in the marketplace.")
        return

    listing = marketplace[seller_id]
    card = listing["card"]

    # Ensure the card ID matches
    if card["id"] != card_id:
        await ctx.send(f"{ctx.author.mention}, the requested card ID does not match the listing.")
        return

    # Check if the buyer has enough balance
    price = listing["price"]
    buyer_balance = user_balances.get(buyer_id, 0)

    # Debugging: Check balances before the transaction
    print(f"Before Transaction - Buyer ID: {buyer_id}, Buyer Balance: {buyer_balance}, Seller ID: {seller_id}, Seller Balance: {user_balances.get(seller_id, 0)}")

    if buyer_balance < price:
        await ctx.send(f"{ctx.author.mention}, you don't have enough coins to buy this card! You need {price} coins but have {buyer_balance} coins.")
        return

    # Deduct the price from the buyer and add it to the seller
    user_balances[buyer_id] -= price
    user_balances[seller_id] += price

    # Debugging: Check balances after the transaction
    print(f"After Transaction - Buyer ID: {buyer_id}, Buyer Balance: {user_balances[buyer_id]}, Seller ID: {seller_id}, Seller Balance: {user_balances[seller_id]}")

    # Transfer the card to the buyer
    if buyer_id not in users_with_cards:
        users_with_cards[buyer_id] = []  # Initialize list if buyer doesn't have cards

    users_with_cards[buyer_id].append(card)  # Add the card to the buyer's collection

    # Remove the listing from the marketplace
    del marketplace[seller_id]

    # Send confirmation message
    embed = discord.Embed(
        title="Card Purchased",
        description=f"{ctx.author.mention} bought {card['name']} from {seller.mention} for {price} coins!",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

    # Update user profiles
    await update_user_profile_balance(seller)  # Update seller's balance
    await update_user_profile_balance(ctx.author)  # Update buyer's balance



# Command to remove a card from the user's collection by card ID
@bot.command(name="remove")
async def remove_card(ctx, card_id: int):
    user_id = ctx.author.id

    # Check if user has any cards
    if user_id not in users_with_cards or not users_with_cards[user_id]:
        await ctx.send(f"{ctx.author.mention}, you don't have any cards to remove!")
        return

    # Find the card by ID
    card_to_remove = next((card for card in users_with_cards[user_id] if card["id"] == card_id), None)

    if not card_to_remove:
        await ctx.send(f"{ctx.author.mention}, you don't have a card with that ID!")
        return

    # Remove the card from the user's inventory
    users_with_cards[user_id].remove(card_to_remove)

    # Send confirmation message
    embed = discord.Embed(
        title="Card Removed",
        description=f"{ctx.author.mention}, you have successfully removed the card {card_to_remove['name']}.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

# Command to view the user's cards
@bot.command(name="cards")
async def view_cards(ctx):
    user_id = ctx.author.id

    # Check if user has any cards
    if user_id not in users_with_cards or not users_with_cards[user_id]:
        await ctx.send(f"{ctx.author.mention}, you don't have any cards!")
        return

    # Create an embed listing all user's cards
    embed = discord.Embed(
        title="Your Cards",
        description="Here are the cards you own:",
        color=discord.Color.blue()
    )

    for card in users_with_cards[user_id]:
        embed.add_field(name=card["name"], value=f"ID: {card['id']}", inline=False)

    await ctx.send(embed=embed)

@bot.command(name="npc")
async def npc_battle(ctx):
    user_id = ctx.author.id

    # Check if the user has a card
    if user_id not in users_with_cards or not users_with_cards[user_id]:
        await ctx.send(f"{ctx.author.mention}, you need a card to battle an NPC!")
        return

    # Randomly select an NPC card
    npc_card = draw_card()

    # Simulate the battle outcome
    battle_outcome = random.choice(["win", "lose"])  # 50/50 chance to win or lose

    # Initialize the embed for the battle result
    embed = discord.Embed(
        title="NPC Battle Result",
        description=f"{ctx.author.mention}, you battled an NPC!",
        color=discord.Color.blue()
    )

    if battle_outcome == "win":
        # Update user stats for win
        user_stats[user_id]["wins"] += 1
        user_stats[user_id]["gold"] += 25  # Reward user with gold for winning

        # Update profile balance accordingly
        current_balance = user_stats[user_id]["gold"]

        # 2% chance to upgrade to a Zeus or Hades card
        if random.random() < 0.02:
            upgrade_card_name = random.choice(["Zeus", "Hades"])  # Randomly choose between Zeus and Hades
            new_card = next(card for card in cards if card["name"] == upgrade_card_name)

            # Add new card to user's collection
            users_with_cards[user_id].append(new_card)  
            embed.add_field(name="Result", value="You won the battle and upgraded your card!", inline=False)
            embed.add_field(name="New Card", value=new_card["name"], inline=False)
            embed.set_image(url=new_card["image"])
        else:
            embed.add_field(name="Result", value="You won the battle!", inline=False)
            embed.add_field(name="NPC Card", value=npc_card["name"], inline=False)
            embed.set_image(url=npc_card["image"])

        # Add the gold earned to the embed message
        embed.add_field(name="Gold Earned", value="You earned 25 gold!", inline=False)
        embed.add_field(name="Total Gold", value=f"{current_balance} gold", inline=False)

    else:
        # Update user stats for loss
        user_stats[user_id]["losses"] += 1
        embed.add_field(name="Result", value="You lost the battle!", inline=False)
        embed.add_field(name="NPC Card", value=npc_card["name"], inline=False)
        embed.set_image(url=npc_card["image"])

        # 30% chance to lose the user's card
        if random.random() < 0.30:
            # Lose the user's card
            lost_card = users_with_cards[user_id][0]  # Get the first card in the user's list
            users_with_cards[user_id].remove(lost_card)  # Remove the lost card
            embed.add_field(name="Card Lost", value=f"You lost your card: {lost_card['name']}!", inline=False)

    # Send the embed message to the user
    message = await ctx.send(embed=embed)  # Send the embed and store the message

    # Update profile balance to reflect changes immediately after the battle
    await update_user_profile_balance(ctx.author)  # Function to update the user's profile

    await asyncio.sleep(30)  # Wait for 30 seconds
    await message.delete()  # Delete the message after 30 seconds

async def update_user_profile_balance(user: discord.Member):
    """Function to update the user's profile balance."""
    user_id = user.id
    current_balance = user_stats[user_id]["gold"]
    



@bot.command(name="duel")
async def duel(ctx, opponent: discord.Member):
    user_id = ctx.author.id
    opponent_id = opponent.id

    # Check if both users have cards
    if user_id not in users_with_cards or not users_with_cards[user_id]:
        await ctx.send(f"{ctx.author.mention}, you need a card to duel!")
        return

    if opponent_id not in users_with_cards or not users_with_cards[opponent_id]:
        await ctx.send(f"{opponent.mention} needs a card to duel!")
        return

    # Get the users' cards
    user_card = users_with_cards[user_id][0]  # Assuming first card is used
    opponent_card = users_with_cards[opponent_id][0]  # Assuming first card is used

    # Determine win probabilities (including Zeus and Hades logic)
    user_wins = False
    if "Zeus" in user_card["name"] or "Hades" in user_card["name"]:
        # User has Zeus or Hades: 65% chance to win against non-Zeus/Hades
        user_wins = random.random() < (0.65 if not ("Zeus" in opponent_card["name"] or "Hades" in opponent_card["name"]) else 0.5)
    else:
        user_wins = random.random() < 0.5  # Normal 50% chance

    # Prepare embed for duel result
    embed = discord.Embed(
        title="Duel Result",
        description=f"{ctx.author.mention} duelled {opponent.mention}!",
        color=discord.Color.red()
    )

    if user_wins:
        # User wins
        user_stats[user_id]["wins"] += 1
        user_stats[opponent_id]["losses"] += 1
        embed.add_field(name="Result", value="You won the duel!", inline=False)
        embed.add_field(name="Your Card", value=user_card["name"], inline=False)
        embed.set_image(url=user_card["image"])

        # 2% chance to upgrade card
        if random.random() < 0.02:
            new_card = draw_card()  # Function to get a new card
            users_with_cards[user_id].append(new_card)  # Add new card to user's collection
            embed.add_field(name="Upgraded Card", value=f"You've upgraded to {new_card['name']}!", inline=False)
            embed.set_image(url=new_card["image"])

    else:
        # User loses
        user_stats[user_id]["losses"] += 1
        user_stats[opponent_id]["wins"] += 1
        embed.add_field(name="Result", value="You lost the duel!", inline=False)
        embed.add_field(name="Opponent's Card", value=opponent_card["name"], inline=False)
        embed.set_image(url=opponent_card["image"])

        # 30% chance to lose their card
        if random.random() < 0.30:
            lost_card = users_with_cards[user_id][0]  # Get the first card in the user's list
            users_with_cards[user_id].remove(lost_card)  # Remove the lost card
            embed.add_field(name="Card Lost", value=f"You lost your card: {lost_card['name']}!", inline=False)

    await ctx.send(embed=embed)  # Send the embed message


@bot.command(name="p")
async def p(ctx):
    user_id = ctx.author.id

    # Ensure the user has an entry in user_stats
    if user_id not in user_stats:
        await ctx.send(f"{ctx.author.mention}, you don't have a profile yet!")
        return

    # Get user stats and balance
    user_data = user_stats[user_id]
    gold_balance = user_data.get("gold", 0)
    wins = user_data.get("wins", 0)
    losses = user_data.get("losses", 0)

    # Get cards owned by the user
    user_cards = users_with_cards.get(user_id, [])
    card_names = ", ".join(card["name"] for card in user_cards) if user_cards else "No cards owned"

    # Create an embed for the profile
    embed = discord.Embed(
        title=f"{ctx.author.name}'s Profile",
        description="Here are your current stats:",
        color=discord.Color.green()
    )
    embed.add_field(name="Gold", value=f"{gold_balance} coins", inline=False)
    embed.add_field(name="Wins", value=wins, inline=False)
    embed.add_field(name="Losses", value=losses, inline=False)
    embed.add_field(name="Cards Owned", value=card_names, inline=False)

    await ctx.send(embed=embed)



# Dictionary to track the last claim time for each user
last_claim_time = {}

@bot.command(name="claim")
async def claim_card(ctx):
    user_id = ctx.author.id

    # Check if the user already has a card
    if user_id in users_with_cards and users_with_cards[user_id]:
        await ctx.send(f"{ctx.author.mention}, you already have a card! You cannot claim a new one.")
        return

    # Check the last claim time
    current_time = discord.utils.utcnow()  # Get the current time in UTC
    if user_id in last_claim_time:
        time_since_last_claim = (current_time - last_claim_time[user_id]).total_seconds()
        if time_since_last_claim < 86400:  # 86400 seconds in 24 hours
            remaining_time = 86400 - time_since_last_claim
            await ctx.send(f"{ctx.author.mention}, you need to wait {int(remaining_time // 3600)} hours and {int((remaining_time % 3600) // 60)} minutes before claiming again.")
            return

    # Claim a new card
    new_card = draw_card()
    users_with_cards[user_id] = [new_card]  # Assign the new card to the user

    # Update the last claim time
    last_claim_time[user_id] = current_time

    # Create an embedded message with the new card information
    embed = discord.Embed(
        title="You Claimed a New Card!",
        description=f"{ctx.author.mention}, congratulations on claiming a new card!",
        color=discord.Color.green()
    )
    embed.add_field(name="Card Name", value=new_card["name"], inline=False)
    embed.set_image(url=new_card["image"])
    if new_card["name"] == "Zeus":
        embed.add_field(name="Special Message", value="You Claimed Zeus, the mighty ruler of Olympus!", inline=False)
    embed.set_footer(text="Enjoy your new card!")

    await ctx.send(embed=embed)

# Function to send a message and delete it after a specified duration
async def send_and_delete(ctx, content, delete_after=30):
    message = await ctx.send(content)  # Send the message
    await asyncio.sleep(delete_after)  # Wait for the specified duration
    await message.delete()  # Delete the message

@bot.command(name="modgold")
@commands.is_owner()  # Only allow the bot owner to use this command
async def modgold(ctx, member: discord.Member, amount: int):
    user_id = member.id

    # Modify the user's gold balance
    if user_id not in user_balances:
        user_balances[user_id] = 0  # Initialize if not present

    user_balances[user_id] += amount  # Update the balance

    if amount > 0:
        await send_and_delete(ctx, f"Added {amount} gold to {member.mention}. New balance: {user_balances[user_id]} gold.")
    else:
        await send_and_delete(ctx, f"Removed {-amount} gold from {member.mention}. New balance: {user_balances[user_id]} gold.")

@bot.command(name="modcard")
@commands.is_owner()  # Only allow the bot owner to use this command
async def modcard(ctx, member: discord.Member, card_id: int = None):
    user_id = member.id

    if card_id is None:
        # Give a random card to the specified member
        card = draw_card()
        if user_id not in users_with_cards:
            users_with_cards[user_id] = []  # Initialize user's card list if it doesn't exist
        
        users_with_cards[user_id].append(card)  # Add the new card to the user's collection

        # Create an embedded message with the card information
        embed = discord.Embed(
            title="You Received a New Card!",
            description=f"{member.mention}, congratulations on receiving a new card!",
            color=discord.Color.green()
        )
        embed.add_field(name="Card Name", value=card["name"], inline=False)
        embed.set_image(url=card["image"])
        await ctx.send(embed=embed)
        
    else:
        # Take away a card from the specified member by card_id
        if user_id in users_with_cards:
            # Find and remove the card with the specified ID
            card_to_remove = next((card for card in users_with_cards[user_id] if card["id"] == card_id), None)
            if card_to_remove:
                users_with_cards[user_id].remove(card_to_remove)
                await send_and_delete(ctx, f"Removed card '{card_to_remove['name']}' from {member.mention}.")
            else:
                await send_and_delete(ctx, f"{member.mention} does not have a card with ID {card_id}.")
        else:
            await send_and_delete(ctx, f"{member.mention} has no cards.")

# Start the bot
bot.run('')
