import discord
from discord.ext import commands, tasks
import asyncio
import datetime
import os
from dotenv import load_dotenv
from keep_alive import keep_alive  # If you have this defined somewhere

#comment
load_dotenv()
# Constants
SUGGESTION_CHANNEL_ID = 1382808669250388102
TARGET_USER_ID = 290888605516431362

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)
@bot.event
async def on_ready():
    print(f"{bot.user} is online.")
    time_checker.start()

@tasks.loop(minutes=1)
async def time_checker():
    now = datetime.datetime.now()
    if now.hour == 0 and now.minute == 0:
        print("It's midnight — shutting down.")
        await bot.close()
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if any(user.id == TARGET_USER_ID for user in message.mentions):
        embed = discord.Embed(
            title="You've summoned them!",
            description=f"{message.author.mention} mentioned <@{TARGET_USER_ID}> 👀",
            color=discord.Color.purple()
        )
        gif_path = r"lalo-salamanca-lalo.gif"
        file = discord.File(fp=gif_path, filename="summon.gif")
        embed.set_image(url="attachment://summon.gif")
        embed.set_footer(text="Careful who you tag...")

        await message.channel.send(embed=embed, file=file)

    await bot.process_commands(message)

@bot.command()
async def suggestion(ctx, *, suggestion_text: str):
    channel = bot.get_channel(SUGGESTION_CHANNEL_ID)
    if channel is None:
        await ctx.send("Suggestions channel not found! Contact an admin.")
        return

    embed = discord.Embed(
        title="New Suggestion",
        description=suggestion_text,
        color=0x00ff00,
        timestamp=ctx.message.created_at
    )
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)

    msg = await channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    await ctx.send(f"Your suggestion has been posted in {channel.mention}!")

@bot.command()
async def poll(ctx):
    def check_author(m):
        return m.author == ctx.author and m.channel == ctx.channel

    # Replace mention tags with display names for the title
    def replace_mentions_with_names(text, mentions):
        for member in mentions:
            text = text.replace(f"<@{member.id}>", member.display_name)
            text = text.replace(f"<@!{member.id}>", member.display_name)
        return text

    await ctx.send("📨 Which channel should the poll be posted in? (mention it or type its name)")
    while True:
        try:
            chan_msg = await bot.wait_for("message", check=check_author, timeout=60.0)
            if chan_msg.channel_mentions:
                target_channel = chan_msg.channel_mentions[0]
            else:
                target_channel = discord.utils.get(ctx.guild.text_channels, name=chan_msg.content.strip().lower())
            if target_channel:
                break
            else:
                await ctx.send("❌ Couldn't find that channel. Try again.")
        except asyncio.TimeoutError:
            await ctx.send("⏰ You took too long. Try the command again.")
            return

    await ctx.send("📝 What is the **title** of your poll?")
    title_msg = await bot.wait_for("message", check=check_author, timeout=60.0)
    title = replace_mentions_with_names(title_msg.content, title_msg.mentions)

    await ctx.send("📋 What is the **description** of the poll?")
    desc_msg = await bot.wait_for("message", check=check_author, timeout=60.0)
    description = desc_msg.content  # You can also do mention replacement here if you want

    await ctx.send("🔢 How many **options** will this poll have? (Max: 20)")
    while True:
        try:
            opt_msg = await bot.wait_for("message", check=check_author, timeout=60.0)
            num_options = int(opt_msg.content)
            if 1 <= num_options <= 20:
                break
            else:
                await ctx.send("Please enter a number between 1 and 20.")
        except ValueError:
            await ctx.send("Please enter a valid number.")

    option_emojis = [chr(0x1F1E6 + i) for i in range(num_options)]  # 🇦 to 🇹
    options = []

    for i, emoji in enumerate(option_emojis, 1):
        await ctx.send(f"✏️ Enter text for **option {i}**:")
        option_msg = await bot.wait_for("message", check=check_author, timeout=60.0)
        # Optional: replace mentions in options if you want
        option_text = option_msg.content
        options.append((emoji, option_text))

    # Build poll embed
    embed = discord.Embed(title=title, description=description, color=0x3498db)
    for emoji, opt_text in options:
        embed.add_field(name=emoji, value=opt_text, inline=False)

    poll_message = await target_channel.send(embed=embed)

    for emoji, _ in options:
        await poll_message.add_reaction(emoji)

    await target_channel.send("✅ Poll created! Voting ends in 5 minutes.")
    await asyncio.sleep(300)

    # Re-fetch the message to count votes
    poll_message = await target_channel.fetch_message(poll_message.id)
    counts = {emoji: 0 for emoji, _ in options}

    for reaction in poll_message.reactions:
        if reaction.emoji in counts:
            users = [u async for u in reaction.users() if not u.bot]
            counts[reaction.emoji] = len(users)

    winner_emoji = max(counts, key=counts.get)
    winner_name = dict(options)[winner_emoji]
    tie = list(counts.values()).count(counts[winner_emoji]) > 1

    if tie:
        await target_channel.send("⚠️ It's a tie! No winner determined.")
    else:
        await target_channel.send(f"🏆 **{winner_name}** wins with **{counts[winner_emoji]}** vote(s)!")

# Keep alive for Replit
keep_alive()
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)