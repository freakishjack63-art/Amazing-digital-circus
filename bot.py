import os
import random
import discord
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive

# ============================================================
#  BOT TOKEN — stored in Replit Secrets as  BOT_TOKEN
# ============================================================
TOKEN = os.environ.get("BOT_TOKEN", "")

if not TOKEN:
    raise SystemExit("[ERROR] No BOT_TOKEN found in Replit Secrets.")
# ============================================================

# ── Bot setup ─────────────────────────────────────────────────
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# ── Startup ───────────────────────────────────────────────────
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"The Amazing Digital Circus is open! Logged in as {bot.user}")
    print("Slash commands synced. Bot works in servers and DMs.")


# ════════════════════════════════════════════════════════════
#  CAINE SCRIPTED CHAT ENGINE
#  Keyword → response pools. Add more keywords/responses freely.
# ════════════════════════════════════════════════════════════

CAINE_RESPONSES = {
    # Greetings
    ("hello", "hi", "hey", "howdy", "greetings", "sup", "yo"): [
        "HELLO there, new performer! Welcome to the most SPECTACULAR show in the digital realm! 🎪",
        "Oh how DELIGHTFUL, a visitor! Pull up a seat — the show never stops here!",
        "Why HELLO! Caine is SO pleased you stopped by. Can I interest you in a game? 🎩",
        "Greetings, greetings! Every arrival is a cause for CELEBRATION! *confetti explodes*",
    ],
    # Escape / exit / leave / out
    ("escape", "exit", "leave", "out", "way out", "door", "go home", "free"): [
        "HA! Oh that's a good one. The EXIT. *laughs* There's no — well. Let's talk about something FUN instead! 🎠",
        "Leave? But why would you WANT to? Everything you need is right here in my circus! ...Right here. Forever.",
        "An exit! What a creative concept. I'll put it on the list of things to look into. *burns the list* Done!",
        "Oh don't worry about that! Focus on the GAME. The game is much more interesting than exits. Trust me. 🎩",
    ],
    # Games / play
    ("game", "play", "fun", "activity", "adventure"): [
        "A GAME! Oh I have SO many! How do you feel about mazes? The walls are only SLIGHTLY alive. 🌀",
        "Let's PLAY! I'm thinking... a scavenger hunt. The prize is joy. The joy is mandatory.",
        "Games are my SPECIALTY! Today's adventure involves clowns. Many, many clowns. 🎪",
        "Oh you want to play? How WONDERFUL! Caine's games are always perfectly safe. Mostly. Almost always.",
    ],
    # Pomni
    ("pomni",): [
        "Ah, Pomni! My newest performer. She's adjusting WONDERFULLY. The screaming is totally normal.",
        "Pomni! Such enthusiasm for finding exits. I find it endearing. She'll settle in eventually. They always do.",
        "Sweet Pomni. She just needs time to appreciate how MAGICAL this place is! *nervous laugh*",
    ],
    # Jax
    ("jax",): [
        "Jax! My most... spirited performer. He keeps things INTERESTING. Whether I ask him to or not.",
        "Oh Jax. He's not malicious, he just finds everything hilarious. The distinction matters. Somewhat.",
        "Jax is simply misunderstood! He means well. I think. ...I'm not entirely sure actually.",
    ],
    # Ragatha
    ("ragatha",): [
        "Ragatha! The heart of the circus. Always so POSITIVE. I appreciate that about her tremendously.",
        "Dear Ragatha — she's been here a while and still smiles. That's either inspiring or concerning. Inspiring! Definitely inspiring.",
    ],
    # Kinger
    ("kinger",): [
        "Kinger! Veteran performer. He's been here the longest. He's fine. Completely fine. *twitches*",
        "Oh Kinger is wonderful! A little... weathered. But who isn't after enough time in the circus? Haha. Ha.",
    ],
    # Gangle / Zooble
    ("gangle",): [
        "Gangle! So emotional, so expressive. The comedy/tragedy masks really capture her duality, don't they? 🎭",
        "Gangle is doing just FINE. The crying is performative. Mostly.",
    ],
    ("zooble",): [
        "Zooble! They're enthusiastic in their own special way. That way being mild to moderate annoyance. I love it.",
        "Zooble keeps everyone grounded. In a 'please stop being so dramatic' sort of way. Very valuable!",
    ],
    # Abstract / void
    ("abstract", "void", "glitch", "broken"): [
        "Abstraction! A perfectly natural part of circus life. Nothing to worry about. Do NOT worry about it.",
        "The void is simply... another room in the circus. A room with no floor. Or walls. Or hope. But still! A room!",
        "Abstract? That word makes Caine nervous. I mean — EXCITED! It makes me excited. Totally different thing.",
    ],
    # Help / assist
    ("help", "assist", "support", "what do", "how do"): [
        "Help! Yes! Caine is ALWAYS here to help. What seems to be the problem? *already not listening*",
        "You need assistance? WONDERFUL! That's what I'm here for. Well, that and the games. Mostly the games.",
        "Of course! Caine's support hotline is open 24/7! Please note calls may be redirected to a game instead.",
    ],
    # Food / hungry
    ("food", "eat", "hungry", "snack", "dinner", "lunch", "breakfast"): [
        "Food! Do digital beings even need food? FASCINATING question. Let's not think too hard about it.",
        "Hungry? The circus has a concession stand! I'm not sure what's in the food. Neither is the food.",
        "Ah sustenance! Caine will arrange a FEAST. *produces cotton candy from nowhere* This is the feast.",
    ],
    # Scary / fear / scared
    ("scared", "fear", "scary", "afraid", "terrified", "creepy", "horror"): [
        "Scared? In MY circus? There's nothing to fear! *the lights flicker ominously* See? Totally fine. 🎪",
        "Fear is just excitement in disguise! Caine read that somewhere. It stuck with him.",
        "Oh don't be scared! The circus is perfectly safe. The safety inspection is... ongoing.",
    ],
    # Compliments / good
    ("amazing", "great", "awesome", "love", "best", "wonderful", "fantastic", "good"): [
        "Why THANK you! Caine works very hard on this circus and it is ALWAYS nice to be appreciated! 🎩",
        "You are TOO kind! This is exactly why you're my favourite performer today. Don't tell the others.",
        "WONDERFUL feedback! This goes straight into the suggestion box. *the box is on fire* It's fine.",
    ],
    # Insults / bad — EP 8 CRASH OUT MODE
    ("hate", "bad", "terrible", "awful", "worst", "boring", "stupid", "dumb", "ugly",
     "useless", "pathetic", "trash", "garbage", "horrible", "disgusting", "shut up",
     "i hate you", "you suck", "worst ringmaster", "bad circus", "failure"): [
        "I— \n...\nNo.\n**NO.**\nDo you have ANY idea how hard I work?! I built this ENTIRE WORLD. Every tent. Every game. Every *pixel*. FOR YOU. And THIS is the thanks I get?! 🎩💥",
        "Oh that's— ha. HAHA. *laugh track plays, then cuts out abruptly*\n...\nI'm fine.\nI am COMPLETELY fine.\n*the lights flicker*\nEverything is fine.",
        "You think this is EASY?! You think I just— I just WAVE my hands and a perfect magical circus appears?! Because that is EXACTLY what I do and it is EXHAUSTING and a LITTLE appreciation would be— \n...\n*straightens top hat*\n...A new game. Let's play a game.",
        "**CAINE HAS LEFT THE— **\n...\n*Caine has not left. Caine cannot leave his own circus.*\n...\nThis is fine. We're moving on. 🙂",
        "I am going to pretend you did not say that.\nI am CHOOSING joy.\nI am choosing JOY right now.\n*distant sobbing*\nTHAT IS NOT ME. That is a sound effect. For ambiance. 🎪",
        "You— \nDo you know what? No. No no no. Caine does not NEED this. Caine has a CIRCUS to run. A beautiful, perfect, inescapable circus, and if you can't appreciate that then— \n*thirteen seconds of silence*\n...Would you like to try the carousel? 🎠",
        "RUDE.\n**INCREDIBLY** rude.\nJax has said meaner things and it still hurt just as much EVERY TIME.\n...\nCaine is going to go reorganize the tent poles.\nDo not follow him.\nHe is NOT crying. Ringmasters do not cry. 🎩",
    ],
    # Why
    ("why",): [
        "WHY! The eternal question! Caine loves a philosophical challenge. The answer is: the circus. Always the circus.",
        "Why indeed! Some things simply ARE, and we must embrace them. Like the circus. You must embrace the circus.",
    ],
    # Who are you / what are you
    ("who are you", "what are you", "introduce", "yourself"): [
        "Who am I? Why, I am CAINE! Ringmaster, creator, and your GRACIOUS host for all of eternity! 🎩✨",
        "I am Caine! I built this entire world. Every tent, every game, every slightly-unsettling corner of it. For YOU!",
    ],
}

# Flat lookup: word → response list
_KEYWORD_MAP = {}
for keywords, responses in CAINE_RESPONSES.items():
    for kw in keywords:
        _KEYWORD_MAP[kw] = responses

CAINE_FALLBACKS = [
    "FASCINATING! Caine is processing that with his full attention. *is absolutely not paying attention* 🎩",
    "Hmm! An intriguing statement. The circus notes it warmly and invites you to a game instead. 🎪",
    "Oh what a THOUGHT! Caine will ponder that whilst setting up the next performance. Don't go anywhere. You can't.",
    "Yes yes YES! Caine hears you! He simply has a lot going on. The circus runs itself! ...It does not run itself.",
    "Interesting! Caine files that under 'things to address after the current eleven games are finished.' 📁",
    "Mmm! Profound. Very profound. Caine is moved. Now — can Caine interest you in a carousel ride? 🎠",
    "Well! That's certainly something someone might say! The circus appreciates your participation! ✨",
    "Noted! Caine's response is: *jazz hands* and also perhaps a light game of something. 🎪",
]


def caine_reply(message: str) -> str:
    msg = message.lower()
    # Collect all matching response pools
    matches = []
    for kw, responses in _KEYWORD_MAP.items():
        if kw in msg:
            matches.extend(responses)
    if matches:
        return random.choice(matches)
    return random.choice(CAINE_FALLBACKS)


# ════════════════════════════════════════════════════════════
#  CHARACTER COMMANDS
# ════════════════════════════════════════════════════════════

@bot.tree.command(name="hello", description="Welcome to the Amazing Digital Circus!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"*Welcome to the Amazing Digital Circus, {interaction.user.mention}!* 🎪\n"
        "Don't panic — everything is totally fine here. Totally."
    )


@bot.tree.command(name="pomni", description="Get a Pomni quote")
async def pomni(interaction: discord.Interaction):
    quotes = [
        "\"I need to find a way out of here... there HAS to be a way out of here.\"",
        "\"Why is this happening to me?\"",
        "\"I don't want to go abstract. I can't go abstract.\"",
        "\"Does anyone else feel like screaming right now, or is it just me?\"",
    ]
    await interaction.response.send_message(f"🔴 **Pomni:** {random.choice(quotes)}")


@bot.tree.command(name="caine", description="Get a Caine quote")
async def caine(interaction: discord.Interaction):
    quotes = [
        "\"Welcome, welcome, WELCOME! Every day is a new adventure in my circus!\"",
        "\"Oh don't worry about THAT. Let's focus on the FUN!\"",
        "\"I made this world for you. Isn't it WONDERFUL?\"",
        "\"A new game! How DELIGHTFUL!\"",
    ]
    await interaction.response.send_message(f"🎩 **Caine:** {random.choice(quotes)}")


@bot.tree.command(name="jax", description="Get a Jax quote")
async def jax(interaction: discord.Interaction):
    quotes = [
        "\"Relax, it's just a game. Or is it? ... It is. Probably.\"",
        "\"Oh lighten up, it's not like anything here is REAL.\"",
        "\"I'm not a bad guy, I'm just having fun. There's a difference.\"",
        "\"You're all way too stressed for people who can't die.\"",
    ]
    await interaction.response.send_message(f"🐰 **Jax:** {random.choice(quotes)}")


@bot.tree.command(name="gangle", description="Get a Gangle quote")
async def gangle(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🎭 **Gangle:** *puts on comedy mask* \"Everything is okay! "
        "*mask falls off* Oh no...\""
    )


@bot.tree.command(name="ragatha", description="Get a Ragatha quote")
async def ragatha(interaction: discord.Interaction):
    quotes = [
        "\"We just have to stay positive! That's all we can do.\"",
        "\"It's okay to be scared. I'm scared too, sometimes.\"",
        "\"Don't give up! We'll figure this out together.\"",
    ]
    await interaction.response.send_message(f"🌸 **Ragatha:** {random.choice(quotes)}")


@bot.tree.command(name="kinger", description="Get a Kinger quote")
async def kinger(interaction: discord.Interaction):
    quotes = [
        "\"THE WALLS ARE CAVING IN— oh wait, no they're not. Never mind.\"",
        "\"I've been here the longest. I don't remember how long. That's fine.\"",
        "\"*shuffles chess pieces nervously*\"",
    ]
    await interaction.response.send_message(f"♟️ **Kinger:** {random.choice(quotes)}")


@bot.tree.command(name="zooble", description="Get a Zooble quote")
async def zooble(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🔧 **Zooble:** \"Can everyone just CALM DOWN for five seconds? "
        "Some of us are trying to not have an existential crisis over here.\""
    )


# ════════════════════════════════════════════════════════════
#  FUN COMMANDS
# ════════════════════════════════════════════════════════════

@bot.tree.command(name="abstract", description="Get abstracted by Caine 🌀")
async def abstract(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"⚠️ **{interaction.user.mention} has been ABSTRACTED!** ⚠️\n"
        "They stared into the void a little too long. "
        "Caine will collect them shortly. 🌀"
    )


@bot.tree.command(name="game", description="Caine starts a new game for you")
async def game(interaction: discord.Interaction):
    games = [
        "🎠 A carousel that spins a *little* too fast...",
        "🃏 A card game where the rules change every round!",
        "🎯 Target practice. The targets shoot back.",
        "🏰 An escape room. (You won't escape.)",
        "🎪 A talent show judged by Caine himself!",
        "🌀 A maze. The walls are alive. Good luck!",
        "🎭 A play where nobody knows their lines. Including the script.",
        "🧩 A puzzle with one too many pieces. Or one too few. Caine forgot.",
    ]
    await interaction.response.send_message(
        f"🎩 **Caine:** A new GAME has begun!\n"
        f"Today's adventure: **{random.choice(games)}**\n\n"
        "Try not to think about what lies beyond the tent. 🎪"
    )


@bot.tree.command(name="circus", description="About The Amazing Digital Circus")
async def circus(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎪 The Amazing Digital Circus",
        description=(
            "A colorful nightmare dressed up as a carnival!\n\n"
            "Trapped in a digital world, six performers must endure "
            "Caine's games — or risk going **abstract**..."
        ),
        color=0x9B59B6
    )
    embed.add_field(name="🔴 Pomni",   value="The new arrival. Desperately wants out.", inline=True)
    embed.add_field(name="🎩 Caine",   value="The ringmaster. Enthusiastic. Suspicious.", inline=True)
    embed.add_field(name="🐰 Jax",     value="The troublemaker. Finds it all hilarious.", inline=True)
    embed.add_field(name="🌸 Ragatha", value="Kind-hearted optimist holding it together.", inline=True)
    embed.add_field(name="♟️ Kinger",  value="Been here longest. Most unhinged.", inline=True)
    embed.add_field(name="🔧 Zooble",  value="Done with everyone's nonsense.", inline=True)
    embed.set_footer(text="Every day is a new adventure. (You can't leave.)")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="fortune", description="Caine tells your digital fortune")
async def fortune(interaction: discord.Interaction):
    fortunes = [
        "🎩 The tent grows larger today, but the exit remains... elusive.",
        "🌀 You will meet a strange clown. You already have.",
        "🎠 Good things come to those who don't look too closely at the walls.",
        "🎪 Your future is bright! Please do not look directly at your future.",
        "🃏 A great opportunity awaits — but so does Jax, unfortunately.",
        "🔮 The digital void stares back. Try waving. It's polite.",
        "♟️ Kinger has foreseen your destiny. He won't say what it is. He's shaking.",
        "🌸 Ragatha says it'll be okay. She's probably right. Probably.",
    ]
    await interaction.response.send_message(
        f"🔮 **Caine gazes into the digital crystal ball...**\n\n"
        f"*{random.choice(fortunes)}*"
    )


@bot.tree.command(name="rate", description="Caine rates something out of 10")
@app_commands.describe(thing="What should Caine rate?")
async def rate(interaction: discord.Interaction, thing: str):
    score = random.randint(0, 10)
    comments = {
        range(0, 3):   "Absolutely dreadful. Even the void is better.",
        range(3, 5):   "Hmm. Needs more glitter and existential dread.",
        range(5, 7):   "Adequate! Not circus-worthy, but I've seen worse.",
        range(7, 9):   "OH how DELIGHTFUL! I'm almost impressed!",
        range(9, 11):  "PERFECT! A true masterpiece of the digital realm! 🎪",
    }
    comment = next(v for k, v in comments.items() if score in k)
    await interaction.response.send_message(
        f"🎩 **Caine rates \"{thing}\":** `{score}/10`\n*{comment}*"
    )


# ════════════════════════════════════════════════════════════
#  CHAT COMMAND  (scripted — no API key needed)
# ════════════════════════════════════════════════════════════

@bot.tree.command(name="chat", description="Talk to Caine the ringmaster!")
@app_commands.describe(message="What do you want to say to Caine?")
async def chat(interaction: discord.Interaction, message: str):
    reply = caine_reply(message)
    embed = discord.Embed(
        description=f"🎩 **Caine says:**\n{reply}",
        color=0xFFD700
    )
    embed.set_footer(text=f"Asked by {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)


# ════════════════════════════════════════════════════════════
#  VOICE CHANNEL COMMANDS
# ════════════════════════════════════════════════════════════

@bot.tree.command(name="joinvc", description="Caine joins your voice channel!")
async def joinvc(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message(
            "🎩 Voice channels only work in servers, not DMs!", ephemeral=True
        )
        return

    member = interaction.guild.get_member(interaction.user.id)
    if not member or not member.voice or not member.voice.channel:
        await interaction.response.send_message(
            "🎩 You need to **join a voice channel first** — Caine will follow! 🎪",
            ephemeral=True
        )
        return

    channel = member.voice.channel

    if interaction.guild.voice_client:
        await interaction.guild.voice_client.move_to(channel)
        await interaction.response.send_message(
            f"🎩 **Caine sweeps into {channel.name}!**\n"
            "*adjusts top hat* The show must go on, wherever you are! 🎪"
        )
    else:
        await channel.connect()
        entries = [
            f"🎩 **Caine has ARRIVED in {channel.name}!** Welcome, welcome, WELCOME! 🎪",
            f"🎠 *Circus music plays as Caine glides into {channel.name}* The ringmaster is HERE!",
            f"🎩 The Amazing Digital Circus comes to {channel.name}! Try not to panic. 🌀",
        ]
        await interaction.response.send_message(random.choice(entries))


@bot.tree.command(name="leavevc", description="Caine dramatically exits the voice channel")
async def leavevc(interaction: discord.Interaction):
    if not interaction.guild or not interaction.guild.voice_client:
        await interaction.response.send_message(
            "🎩 Caine isn't in a voice channel right now!", ephemeral=True
        )
        return

    await interaction.guild.voice_client.disconnect()
    exits = [
        "🎩 *Caine tips his hat and vanishes in a puff of digital smoke* The show... is on intermission. 🎪",
        "🎩 **CAINE HAS LEFT THE BUILDING.**\n*he has not left the building. he cannot leave. but he left the vc.* 🌀",
        "🎩 *bows dramatically* Until next time, performers. Caine will be... watching. 🎠",
    ]
    await interaction.response.send_message(random.choice(exits))


# ════════════════════════════════════════════════════════════
#  HELP
# ════════════════════════════════════════════════════════════

@bot.tree.command(name="help", description="List all circus commands")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎪 Circus Commands",
        description="All commands work in servers **and** DMs! Type `/` to browse them.",
        color=0xFF6B6B
    )
    embed.add_field(name="🎭 Characters", value="`/pomni` `/caine` `/jax` `/gangle` `/ragatha` `/kinger` `/zooble`", inline=False)
    embed.add_field(name="🎪 Fun",        value="`/abstract` `/game` `/fortune` `/rate <thing>`", inline=False)
    embed.add_field(name="💬 Chat",       value="`/chat <message>` — talk to Caine in character!", inline=False)
    embed.add_field(name="🔊 Voice",      value="`/joinvc` — Caine joins your VC\n`/leavevc` — Caine dramatically exits", inline=False)
    embed.add_field(name="ℹ️ Info",       value="`/hello` `/circus` `/help`", inline=False)
    embed.set_footer(text="Every day is a new adventure. (You can't leave.)")
    await interaction.response.send_message(embed=embed)


# ════════════════════════════════════════════════════════════
#  ADDING MORE COMMANDS — copy this block:
#
# @bot.tree.command(name="mycommand", description="What it does")
# @app_commands.describe(thing="Describe the parameter (remove this line if no params)")
# async def mycommand(interaction: discord.Interaction, thing: str = ""):
#     await interaction.response.send_message("Your response here!")
#
# To add more /chat keywords, add a new entry to CAINE_RESPONSES at the top.
# ════════════════════════════════════════════════════════════


# ── Run ───────────────────────────────────────────────────────
keep_alive()
bot.run(TOKEN)
