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

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)



# Database setup
conn = sqlite3.connect('user_data.db')
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
w3 = Web3(Web3.HTTPProvider('https://example.binance.org/'))

# Define the ID of the game-data channel
GAME_DATA_CHANNEL_ID = 0000000000000000000  # Replace with your channel ID

# Shop setup
SHOP_BNB_ADDRESS = "0000000000000000000"
ROLE_ID = 00000000000000000000  # Replace with your actual role ID
ROLE_COST_GOLD = 5_000_000_000  # 5B Gold
FISH_TO_GOLD_RATE = 25  # 1 fish = 25 gold
WOOD_TO_GOLD_RATE = 50  # 1 wood = 50 gold
ORE_TO_GOLD_RATE = 50   # 1 ore = 50 gold
BNB_TO_GOLD_RATE = 10_000_000_000  # 1 BNB = 10B gold
BNB_TO_GOLD_RATE_STR = f"{BNB_TO_GOLD_RATE // 1_000_000_000}B"

def get_user_data(user_id):
    c.execute('SELECT * FROM users WHERE user_id=?', (user_id,))
    row = c.fetchone()
    if row is None:
        c.execute('INSERT INTO users (user_id) VALUES (?)', (user_id,))
        conn.commit()
        return {"level": 1, "xp": 0, "gold": 0, "win_streak": 0, "wins": 0, "losses": 0, "troops": 0, "fish": 0, "wood": 0, "ore": 0, "bnb_address": None, "bnb_private_key": None, "bnb_balance": 0}
    return {"level": row[1], "xp": row[2], "gold": row[3], "win_streak": row[4], "wins": row[5], "losses": row[6], "troops": row[7], "fish": row[8], "wood": row[9], "ore": row[10], "bnb_address": row[11], "bnb_private_key": row[12], "bnb_balance": row[13]}

def update_user_data(user_id, data):
    c.execute('''
        UPDATE users
        SET level=?, xp=?, gold=?, win_streak=?, wins=?, losses=?, troops=?, fish=?, wood=?, ore=?, bnb_address=?, bnb_private_key=?, bnb_balance=?
        WHERE user_id=?
    ''', (data["level"], data["xp"], data["gold"], data["win_streak"], data["wins"], data["losses"], data["troops"], data["fish"], data["wood"], data["ore"], data["bnb_address"], data["bnb_private_key"], data["bnb_balance"], user_id))
    conn.commit()

def add_xp(user_id, amount):
    data = get_user_data(user_id)
    data["xp"] += amount
    while data["xp"] >= data["level"] * 100:
        data["xp"] -= data["level"] * 100
        data["level"] += 1
    update_user_data(user_id, data)

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
        data = get_user_data(user_id)
        
        if field not in data:
            await ctx.send("Invalid field.")
            await delete_user_command(ctx)
            return
        
        data[field] += value
        update_user_data(user_id, data)
        
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

@bot.command(name="hunt")
async def hunt(ctx):
    try:
        user_id = ctx.author.id
        gold = random.randint(50, 500)
        xp = random.randint(8, 36)
        add_xp(user_id, xp)
        data = get_user_data(user_id)
        data["gold"] += gold
        update_user_data(user_id, data)
        embed = discord.Embed(
            title="🏹 Hunt Result",
            description=f"You hunted a monster and received **{gold}** gold!\n"
                        f"XP: **{data['xp']}/{data['level']*100}** (Level {data['level']})\n"
                        f"**{xp}** XP gained!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
        await delete_user_command(ctx)
    except Exception as e:
        await send_error_to_channel(ctx, str(e))

@bot.command(name="fish")
async def fish(ctx):
    try:
        user_id = ctx.author.id
        fish = random.choice(["🐟 Salmon", "🐠 Trout", "🐡 Tuna"])
        xp = random.randint(8, 36)
        add_xp(user_id, xp)
        data = get_user_data(user_id)
        data["fish"] += 1
        update_user_data(user_id, data)
        embed = discord.Embed(
            title="🎣 Fishing Result",
            description=f"You caught a {fish}!\n"
                        f"XP: **{data['xp']}/{data['level']*100}** (Level {data['level']})\n"
                        f"**{xp}** XP gained!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
        await delete_user_command(ctx)
    except Exception as e:
        await send_error_to_channel(ctx, str(e))

@bot.command(name="chop")
async def chop(ctx):
    try:
        user_id = ctx.author.id
        wood = random.choice(["🌳 Oak", "🌲 Pine", "🍁 Maple"])
        xp = random.randint(8, 36)
        add_xp(user_id, xp)
        data = get_user_data(user_id)
        data["wood"] += 1
        update_user_data(user_id, data)
        embed = discord.Embed(
            title="🪓 Chopping Result",
            description=f"You chopped some {wood} wood!\n"
                        f"XP: **{data['xp']}/{data['level']*100}** (Level {data['level']})\n"
                        f"**{xp}** XP gained!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
        await delete_user_command(ctx)
    except Exception as e:
        await send_error_to_channel(ctx, str(e))

@bot.command(name="mine")
async def mine(ctx):
    try:
        user_id = ctx.author.id
        ore = random.choice(["⛏️ Iron", "🔨 Gold", "💎 Diamond"])
        xp = random.randint(8, 36)
        add_xp(user_id, xp)
        data = get_user_data(user_id)
        data["ore"] += 1
        update_user_data(user_id, data)
        embed = discord.Embed(
            title="🛠️ Mining Result",
            description=f"You mined some {ore} ore!\n"
                        f"XP: **{data['xp']}/{data['level']*100}** (Level {data['level']})\n"
                        f"**{xp}** XP gained!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
        await delete_user_command(ctx)
    except Exception as e:
        await send_error_to_channel(ctx, str(e))

@bot.command(name="bet")
async def bet(ctx, game: str, amount: int):
    try:
        if game.lower() == 'bj':
            await blackjack(ctx, amount)
        elif game.lower() == 'hi_low':
            await hi_low(ctx, amount)
        elif game.lower() == 'dice':
            await dice(ctx, amount)
    except Exception as e:
        await send_error_to_channel(ctx, str(e))

async def blackjack(ctx, amount):
    try:
        user_id = ctx.author.id
        data = get_user_data(user_id)
        
        if data["gold"] < amount:
            await ctx.send("You don't have enough gold to bet that amount.")
            await delete_user_command(ctx)
            return

        data["gold"] -= amount
        update_user_data(user_id, data)

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

    async def reward_gold(self, interaction, win=False, blackjack=False, tie=False):
        try:
            data = get_user_data(self.player_id)
            if tie:
                data["gold"] += self.bet_amount
                update_user_data(self.player_id, data)
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
                update_user_data(self.player_id, data)
                await interaction.response.edit_message(embed=self.create_embed(bonus_msg), view=None)
            else:
                data["losses"] += 1
                data["win_streak"] = 0
                update_user_data(self.player_id, data)
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
            while self.dealer_score < 17:
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

async def hi_low(ctx, amount):
    try:
        user_id = ctx.author.id
        data = get_user_data(user_id)
        
        if data["gold"] < amount:
            await ctx.send("You don't have enough gold to bet that amount.")
            await delete_user_command(ctx)
            return

        data["gold"] -= amount
        update_user_data(user_id, data)

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
            data = get_user_data(self.player_id)
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
                update_user_data(self.player_id, data)
                await interaction.response.edit_message(embed=self.create_embed(bonus_msg), view=None)
            else:
                data["losses"] += 1
                data["win_streak"] = 0
                update_user_data(self.player_id, data)
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
        data = get_user_data(user_id)
        
        if data["gold"] < amount:
            await ctx.send("You don't have enough gold to bet that amount.")
            await delete_user_command(ctx)
            return

        data["gold"] -= amount
        update_user_data(user_id, data)

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
            data = get_user_data(self.player_id)
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
                update_user_data(self.player_id, data)
                await interaction.response.edit_message(embed=self.create_embed(bonus_msg), view=None)
            elif player_roll < bot_roll:
                data["losses"] += 1
                data["win_streak"] = 0
                update_user_data(self.player_id, data)
                await interaction.response.edit_message(embed=self.create_embed(f"You rolled **{player_roll}**, I rolled **{bot_roll}**. I win!"), view=None)
            else:
                data["gold"] += self.bet_amount
                update_user_data(self.player_id, data)
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
        data = get_user_data(user.id)
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
        data = get_user_data(user.id)
        embed = discord.Embed(
            title=f"{user.name}'s Bag",
            description=f"**Fish**: {data['fish']} 🐟\n"
                        f"**Wood**: {data['wood']} 🌲\n"
                        f"**Ore**: {data['ore']} ⛏️",
            color=0x00ff00
        )
        embed.set_thumbnail(url=user.avatar.url)
        await ctx.send(embed=embed)
        await delete_user_command(ctx)
    except Exception as e:
        await send_error_to_channel(ctx, str(e))

@bot.command(name="buy_troops")
async def buy_troops(ctx, amount: int):
    try:
        user_id = ctx.author.id
        data = get_user_data(user_id)
        cost = amount * 10000
        if data["gold"] >= cost:
            data["gold"] -= cost
            data["troops"] += amount
            update_user_data(user_id, data)
            await ctx.send(f"You bought {amount} troops for {cost} gold.")
        else:
            await ctx.send("You don't have enough gold to buy that many troops.")
        await delete_user_command(ctx)
    except Exception as e:
        await send_error_to_channel(ctx, str(e))

@bot.command(name="battle")
async def battle(ctx, opponent: discord.Member, challenger_troops: int, gold: int):
    try:
        challenger_id = ctx.author.id
        opponent_id = opponent.id
        challenger_data = get_user_data(challenger_id)
        opponent_data = get_user_data(opponent_id)

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
                super().__init__()
                self.opponent = opponent
                self.max_troops = max_troops
                self.challenger_id = challenger_id
                self.opponent_id = opponent_id
                self.challenger_troops = challenger_troops
                self.gold = gold
                self.initial_message = None  # Initialize the initial message as None

            def set_initial_message(self, message):
                self.initial_message = message

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
        challenger_data = get_user_data(challenger_id)
        opponent_data = get_user_data(opponent_id)

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
        winner_data = get_user_data(winner_id)
        loser_data = get_user_data(loser_id)

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

        update_user_data(winner_id, winner_data)
        update_user_data(loser_id, loser_data)

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
    embed.add_field(name="!bet hi_low <amount>", value="Play a Hi and Low guessing game and bet gold.", inline=False)
    embed.add_field(name="!bet dice <amount>", value="Play a dice game and bet gold.", inline=False)
    embed.add_field(name="!profile [user]", value="View your profile or another user's profile.", inline=False)
    embed.add_field(name="!bag [user]", value="View your bag or another user's bag of resources.", inline=False)
    embed.add_field(name="!buy_troops <amount>", value="Buy troops for battle.", inline=False)
    embed.add_field(name="!battle <user> <troops> <gold>", value="Challenge another user to a battle.", inline=False)
    embed.add_field(name="!edit <user> <field> <value>", value="Edit user's attributes (admin only).", inline=False)
    embed.add_field(name="!shop", value="Open the shop to buy/sell resources and special roles.", inline=False)
    embed.add_field(name="!deposit", value="Generate a BNB deposit address.", inline=False)
    embed.add_field(name="!withdraw <amount> <address>", value="Withdraw BNB to an external address.", inline=False)
    embed.add_field(name="!bals", value="Check your BNB balance.", inline=False)
    embed.add_field(name="!fee", value="Check the current BNB transaction fee.", inline=False)
    embed.add_field(name="!tip <user> <amount>", value="Tip another user in BNB.", inline=False)
    await ctx.send(embed=embed)
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
            data = get_user_data(user_id)
            resource_amount = data[resource]

            if resource_amount <= 0:
                await interaction.response.send_message(f"You don't have any {resource} to sell.", ephemeral=True)
                return

            gold_earned = resource_amount * rate
            data["gold"] += gold_earned
            data[resource] = 0  # Set resource to 0 after selling

            update_user_data(user_id, data)

            await interaction.response.send_message(f"You sold all your {emoji} {resource} and earned **{gold_earned}** gold!", ephemeral=True)
        except Exception as e:
            await send_error_to_channel(interaction.message, str(e))

    async def buy_gold_with_bnb(self, interaction: discord.Interaction):
        try:
            user_id = interaction.user.id
            data = get_user_data(user_id)

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
            update_user_data(user_id, data)

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
        data = get_user_data(user_id)

        if data["bnb_address"] is None:
            account = Account.create()
            data["bnb_address"] = account.address
            data["bnb_private_key"] = account._private_key.hex()
            update_user_data(user_id, data)

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
        # Delete the user's command message immediately
        await ctx.message.delete()

        user_id = ctx.author.id
        data = get_user_data(user_id)

        # Normalize the token name to uppercase
        token = token.upper()

        if token not in TOKEN_CONTRACTS and token != 'BNB':
            await ctx.send(f"Unsupported token: {token}. Supported tokens are: BNB, {', '.join(TOKEN_CONTRACTS.keys())}")
            return

        # Calculate the gas fee for BNB or the transaction fee for BEP20 tokens
        gas_price = w3.eth.gas_price
        gas_limit = 21000  # Standard gas limit for a simple BNB transfer; adjust if needed for token transfers
        fee_wei = gas_price * gas_limit
        fee_bnb = float(w3.from_wei(fee_wei, 'ether'))

        # Calculate the 1% withdrawal fee
        transaction_fee_bnb = amount * 0.01  # Updated to 1%
        total_fee_bnb = fee_bnb + transaction_fee_bnb

        # Check if the user has enough balance
        if token == 'BNB' and data["bnb_balance"] < (amount + total_fee_bnb):
            await ctx.send(f"You don't have enough BNB to withdraw {amount} BNB. You need at least {amount + total_fee_bnb} BNB to cover the withdrawal and fee.")
            return
        elif token != 'BNB':
            token_contract = w3.eth.contract(address=Web3.to_checksum_address(TOKEN_CONTRACTS[token]), abi=ERC20_ABI)
            token_balance = token_contract.functions.balanceOf(data["bnb_address"]).call()
            token_balance_eth = float(w3.from_wei(token_balance, 'ether'))

            if token_balance_eth < amount:
                await ctx.send(f"You don't have enough {token} to withdraw {amount} {token}.")
                return

            # Ensure enough BNB for the transaction fee
            if data["bnb_balance"] < total_fee_bnb:
                await ctx.send(f"You don't have enough BNB to cover the transaction fee of {total_fee_bnb:.8f} BNB.")
                return

        def format_decimal(value):
            # Format the value to remove unnecessary trailing zeros
            return f"{value:.8f}".rstrip('0').rstrip('.')

        # Ask for confirmation
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

        # Wait for the user's response
        await view.wait()

        # After confirming or declining, delete the confirmation message
        await confirmation_message.delete()

        if view.confirmed:
            if token == 'BNB':
                # Deduct the total fee from the user's balance
                data["bnb_balance"] -= (amount + total_fee_bnb)

                # Prepare the transaction to send BNB to the recipient
                tx = {
                    'nonce': w3.eth.get_transaction_count(data["bnb_address"]),
                    'to': address,
                    'value': w3.to_wei(amount, 'ether'),
                    'gas': gas_limit,
                    'gasPrice': gas_price,
                }
                signed_tx = w3.eth.account.sign_transaction(tx, data["bnb_private_key"])
                tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

                # Send the 1% fee to the shop's BNB address
                fee_tx = {
                    'nonce': w3.eth.get_transaction_count(data["bnb_address"]) + 1,  # Increment nonce for the next transaction
                    'to': SHOP_BNB_ADDRESS,
                    'value': w3.to_wei(transaction_fee_bnb, 'ether'),
                    'gas': gas_limit,
                    'gasPrice': gas_price,
                }
                signed_fee_tx = w3.eth.account.sign_transaction(fee_tx, data["bnb_private_key"])
                fee_tx_hash = w3.eth.send_raw_transaction(signed_fee_tx.rawTransaction)

            else:
                # Proceed with the token transfer
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

                # Send the 1% fee to the shop's BNB address
                fee_tx = {
                    'nonce': w3.eth.get_transaction_count(data["bnb_address"]) + 1,  # Increment nonce for the next transaction
                    'to': SHOP_BNB_ADDRESS,
                    'value': w3.to_wei(transaction_fee_bnb, 'ether'),
                    'gas': gas_limit,
                    'gasPrice': gas_price,
                }
                signed_fee_tx = w3.eth.account.sign_transaction(fee_tx, data["bnb_private_key"])
                fee_tx_hash = w3.eth.send_raw_transaction(signed_fee_tx.rawTransaction)

            # Update the user's balance in the database
            if token == 'BNB':
                update_user_data(user_id, data)

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
        data = get_user_data(user_id)

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
        update_user_data(user_id, data)

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


@bot.command(name="fee")
async def fee(ctx, amount: float = None):
    try:
        gas_price = w3.eth.gas_price  # Get the current gas price
        gas_limit = 21000  # Standard gas limit for a simple BNB transfer
        fee_wei = gas_price * gas_limit
        fee_bnb = float(w3.from_wei(fee_wei, 'ether'))

        def format_decimal(value):
            # Format the value to remove unnecessary trailing zeros
            return f"{value:.8f}".rstrip('0').rstrip('.')

        # If an amount is provided, calculate the 1% transaction fee
        if amount is not None:
            transaction_fee_bnb = amount * 0.01  # 1% fee
            total_fee_bnb = fee_bnb + transaction_fee_bnb
            description = (
                f"To withdraw **{format_decimal(amount)} BNB**, the estimated fees are:\n\n"
                f"**Network Gas Fee:** {format_decimal(fee_bnb)} BNB\n"
                f"**Transaction Fee (1%):** {format_decimal(transaction_fee_bnb)} BNB\n"
                f"**Total Fee:** {format_decimal(total_fee_bnb)} BNB"
            )
        else:
            description = (
                f"The current estimated fee for a standard BNB transaction is:\n\n"
                f"**Network Gas Fee:** {format_decimal(fee_bnb)} BNB"
            )

        # Add the bot's transaction fee statement
        description += (
            f"\n\n**Bot Transaction Fee:** 1% of the withdrawal amount."
        )

        embed = discord.Embed(
            title="💸 Withdrawal Fee Estimate",
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
    'CAKE': '000000000000000000000000000000000000000000',
    'BUSD': '000000000000000000000000000000000000000000',
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

        data = get_user_data(user_id)
        recipient_data = get_user_data(recipient_id)

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

            update_user_data(user_id, data)
            update_user_data(recipient_id, recipient_data)

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
        raider_data = get_user_data(raider_id)
        target_data = get_user_data(target_id)

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
        update_user_data(raider_id, raider_data)
        update_user_data(target_id, target_data)

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
            data = get_user_data(user_id)
            data["fish"] += fish_collected
            data["wood"] += wood_collected
            data["ore"] += ore_collected
            update_user_data(user_id, data)

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
ROLE_ID = 0000000000000000  # Replace with your actual role ID

@bot.command(name="highroller")
async def highroller(ctx):
    try:
        user_id = ctx.author.id
        data = get_user_data(user_id)

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
        update_user_data(user_id, data)
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
            "options": ["Paris", "London", "Berlin", "Rome"],
            "correct_answer": "Paris"
        },
        {
            "question": "Which planet is known as the Red Planet?",
            "options": ["Mars", "Earth", "Jupiter", "Venus"],
            "correct_answer": "Mars"
        },
        {
         "question": "Who Was Known as The King of Pop?",
            "options": ["Michael Jackson", "Justin Timberlake", "Prince", "Harry Styles"],
            "correct_answer": "Michael Jackson"   
        },
        # Add more General Knowledge questions here
    ],
    "Science": [
        {
            "question": "What is the chemical symbol for water?",
            "options": ["H2O", "O2", "CO2", "N2"],
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
        # Add more Science questions here
    ],
    "History": [
        {
            "question": "Who was the first President of the United States?",
            "options": ["George Washington", "Thomas Jefferson", "Abraham Lincoln", "John Adams"],
            "correct_answer": "George Washington"
        },
        {
            "question": "What year did World War II end?",
            "options": ["1945", "1939", "1941", "1950"],
            "correct_answer": "1945"
        },
        {
            "question": "How Many Years Did The 100 Year War Last?",
            "options": ["121", "100", "116", "153"],
            "correct_answer": "116"
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
                data = get_user_data(ctx.author.id)

                # Delete the trivia question and user's answer
                await trivia_message.delete()
                await answer_message.delete()

                if answer_message.content.lower() == correct_answer.lower():
                    gold_reward = random.randint(100, 500)  # Random gold reward between 100 and 500
                    data["gold"] += gold_reward
                    data["wins"] += 1  # Increment wins for correct answer
                    data["win_streak"] += 1  # Increment win streak for correct answer
                    update_user_data(ctx.author.id, data)
                    
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
                    update_user_data(ctx.author.id, data)

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


# Start the bot
bot.run('')
