import os
import json
import random
import discord
from datetime import datetime
from discord import app_commands
from discord.ext import commands, tasks
from keep_alive import keep_alive

CUSTOM_CHAR_IMAGE = "https://upload.wikimedia.org/wikipedia/commons/1/1e/Question_mark_%28Wikipedia%29.png"
COLLECTION_PER_PAGE = 5

def generate_char_id() -> str:
    return ''.join(random.choices('0123456789ABCDEF', k=7))

def _parse_entry(entry, idx: int = 0) -> dict:
    if isinstance(entry, str):
        return {"key": entry, "id": f"OLD{idx:04X}", "atk_bonus": 0, "hp_bonus": 0, "caught": "Unknown", "event": None}
    return entry

CUSTOM_CHARS_FILE = "custom_chars.json"

def _save_custom_chars():
    try:
        with open(CUSTOM_CHARS_FILE, "w") as f:
            json.dump(_custom_chars, f, indent=2)
    except Exception as e:
        print(f"[WARN] Could not save custom chars: {e}")

def _load_custom_chars():
    global _custom_chars
    try:
        with open(CUSTOM_CHARS_FILE, "r") as f:
            _custom_chars = json.load(f)
        print(f"[INFO] Loaded {len(_custom_chars)} custom characters from disk.")
    except FileNotFoundError:
        _custom_chars = {}
    except Exception as e:
        print(f"[WARN] Could not load custom chars: {e}")
        _custom_chars = {}

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
    _load_custom_chars()
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

@bot.tree.command(name="abstract", description="Abstract yourself or another performer 🌀")
@app_commands.describe(user="Who should be abstracted? (leave empty for yourself)")
async def abstract(interaction: discord.Interaction, user: discord.Member = None):
    target = user if user else interaction.user
    messages = [
        f"⚠️ **{target.mention} has been ABSTRACTED!** ⚠️\nThey stared into the void a little too long. Caine will collect them shortly. 🌀",
        f"🌀 **{target.mention} is going abstract!**\n*the colours drain... the shapes blur... Caine watches with mild concern* Oh dear.",
        f"⚠️ Oh no — **{target.mention}** has abstracted!\n*Caine sighs* I'll add them to the collection. They'll be... fine. Probably.",
        f"🌀 **{target.mention}** looked directly at the void and the void looked back.\n...They're abstract now. Caine is not sorry.",
    ]
    await interaction.response.send_message(random.choice(messages))


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
#  MORE FUN COMMANDS
# ════════════════════════════════════════════════════════════

@bot.tree.command(name="roast", description="Caine roasts someone circus-style 🔥")
@app_commands.describe(user="Who should Caine roast?")
async def roast(interaction: discord.Interaction, user: discord.Member):
    roasts = [
        f"🎩 {user.mention}? Oh I TRIED to make a game for them once. The game quit. *the game quit.* 🎪",
        f"🎩 Ah, {user.mention}. Even Kinger — who has forgotten what year it is — remembers to be more interesting than them.",
        f"🎩 {user.mention} walked into the circus and the clowns asked *them* to leave. For being too much. 🤡",
        f"🎩 I once made a maze specifically for {user.mention}. They found the exit immediately. It was the most disappointing day of my life.",
        f"🎩 {user.mention} is the reason I added a second void. The first void complained. 🌀",
        f"🎩 Jax is mean to everyone but even HE gives {user.mention} a little extra. Says it's too easy otherwise. 🐰",
        f"🎩 {user.mention} tried the carousel once. The carousel stopped voluntarily. We don't talk about it. 🎠",
    ]
    await interaction.response.send_message(random.choice(roasts))


@bot.tree.command(name="clown", description="Caine declares someone a clown 🤡")
@app_commands.describe(user="Who is the clown?")
async def clown(interaction: discord.Interaction, user: discord.Member):
    responses = [
        f"🎩 After careful consideration and zero hesitation: **{user.mention} is a clown.** 🤡\nCaine has spoken.",
        f"🤡 **{user.mention}** — you have been officially inducted into the Circus Clown Hall of Fame.\n*confetti falls* This is not a compliment.",
        f"🎩 The clown detector has been going off for a while now and Caine has traced it to **{user.mention}**. 🤡\n*honk*",
        f"🤡 Ladies and gentlemen, your newest clown: **{user.mention}**!\n*the other clowns applaud nervously*",
    ]
    await interaction.response.send_message(random.choice(responses))


@bot.tree.command(name="8ball", description="Ask the digital circus crystal ball a question 🔮")
@app_commands.describe(question="What's your question?")
async def eightball(interaction: discord.Interaction, question: str):
    answers = [
        "🎩 The circus says: **YES.** Enthusiastically. Suspiciously enthusiastically.",
        "🌀 **Absolutely not.** The void has spoken.",
        "🎪 **Signs point to yes!** Though the signs are painted on haunted carnival boards, so.",
        "🎩 **It is certain.** Caine has already planned a game around it.",
        "🔮 **Very doubtful.** Even Kinger thinks that's unlikely. He doesn't remember why.",
        "🎠 **Ask again later.** Caine is busy with the carousel. It won't stop spinning.",
        "🎩 **Yes** — but at what cost? *Caine laughs, won't elaborate.*",
        "🌀 **No.** The answer is no. Please stop asking. The void is tired.",
        "🎪 **Outlook good!** Unless you're asking about an exit. Then: no.",
        "🤡 **Cannot predict now.** A clown is blocking the crystal ball. We're handling it.",
        "🎩 **Without a doubt!** This is going in the next game. You're welcome.",
        "🌸 Ragatha says **yes** and she genuinely means it. That's rare. Take it.",
    ]
    embed = discord.Embed(
        description=f"🔮 *{question}*\n\n{random.choice(answers)}",
        color=0x9B59B6
    )
    embed.set_footer(text="The Amazing Digital Circus Crystal Ball™")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="ship", description="Caine ships two performers together 💕")
@app_commands.describe(user1="First person", user2="Second person")
async def ship(interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
    score = random.randint(0, 100)
    if score < 20:
        verdict = "Absolutely not. Even the void wouldn't put these two together. 🌀"
    elif score < 40:
        verdict = "Hmm. Unlikely. Jax gives it a week. 🐰"
    elif score < 60:
        verdict = "Adequate! Like a game with missing pieces — could work! 🧩"
    elif score < 80:
        verdict = "Oh how SWEET! Ragatha is already planning something. 🌸"
    else:
        verdict = "PERFECT MATCH! Caine demands a circus wedding IMMEDIATELY! 🎪🎩"
    await interaction.response.send_message(
        f"💕 **{user1.mention}** + **{user2.mention}**\n"
        f"Compatibility: `{score}%`\n*{verdict}*"
    )


@bot.tree.command(name="trivia", description="Answer a TADC trivia question 🎪")
async def trivia(interaction: discord.Interaction):
    questions = [
        ("What colour is Pomni's hat?", "Red", ["Blue", "Red", "Yellow", "Purple"]),
        ("What is Caine's role in the circus?", "Ringmaster", ["Clown", "Performer", "Ringmaster", "Janitor"]),
        ("Which character has been in the circus the longest?", "Kinger", ["Ragatha", "Jax", "Kinger", "Gangle"]),
        ("What happens to performers who lose their minds?", "They go abstract", ["They disappear", "They go abstract", "They escape", "They become clowns"]),
        ("What does Gangle wear?", "Comedy/tragedy masks", ["A top hat", "A jester hat", "Comedy/tragedy masks", "A crown"]),
        ("What game does Kinger love?", "Chess", ["Checkers", "Chess", "Cards", "Mazes"]),
    ]
    q, answer, options = random.choice(questions)
    random.shuffle(options)
    opts_text = "\n".join(f"• {o}" for o in options)
    embed = discord.Embed(
        title="🎪 TADC Trivia!",
        description=f"**{q}**\n\n{opts_text}",
        color=0xFFD700
    )
    embed.set_footer(text=f"Answer: {answer} — no cheating! 🎩")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="bubble", description="Trap someone in a Caine bubble 🫧")
@app_commands.describe(user="Who gets bubbled?")
async def bubble(interaction: discord.Interaction, user: discord.Member):
    responses = [
        f"🫧 **{user.mention}** has been placed in a protective Caine bubble!\n*it's for their own good. probably.* 🎩",
        f"🎩 *pops a bubble around {user.mention}*\nThey're safe in there. From everything. Including exits. 🫧",
        f"🫧 {user.mention} is now in a bubble!\n*Kinger tries to pop it*\n*Caine stops him*\nEverything is fine. 🎪",
    ]
    await interaction.response.send_message(random.choice(responses))


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

@bot.tree.command(name="say", description="[OWNER] Make someone say something 🎭")
@app_commands.describe(user="Who to impersonate", message="What they should say")
async def say(interaction: discord.Interaction, user: discord.Member, message: str):
    if interaction.user.id != 1198527966972477505:
        await interaction.response.send_message("🎩 Owner only!", ephemeral=True)
        return
    if not interaction.guild:
        await interaction.response.send_message("🎩 This only works in servers!", ephemeral=True)
        return
    webhook = await interaction.channel.create_webhook(name="CircusSay")
    await webhook.send(
        content=message,
        username=user.display_name,
        avatar_url=user.display_avatar.url
    )
    await webhook.delete()
    await interaction.response.send_message("✅ Done!", ephemeral=True)


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
#  TADC DEX SYSTEM
# ════════════════════════════════════════════════════════════

OWNER_ID = 1198527966972477505

TADC_CHARACTERS = {
    "pomni": {
        "name": "Pomni", "emoji": "🔴", "title": "The New Arrival",
        "rarity": "⭐⭐⭐⭐⭐ Legendary", "rarity_color": 0xFF4444,
        "image_url": "https://static.wikia.nocookie.net/amazingdigitalcircus/images/f/f3/Pomni.png/revision/latest",
        "base_atk": 450, "base_hp": 420,
        "description": "The newest performer in the circus. Desperately searching for an exit and struggling to keep her sanity intact.",
        "stats": {"Sanity": 30, "Courage": 60, "Panic": 95, "Cuteness": 85},
        "quote": "I need to find a way out of here... there HAS to be a way out.",
        "ability": "Exit Seeker — always finds the nearest door (it never opens)",
        "weakness": "The void. And Jax. Mostly Jax.",
    },
    "caine": {
        "name": "Caine", "emoji": "🎩", "title": "The Ringmaster",
        "rarity": "🌟🌟🌟🌟🌟 MYTHIC", "rarity_color": 0xFFD700,
        "image_url": "https://static.wikia.nocookie.net/amazingdigitalcircus/images/3/3b/Caine.png/revision/latest",
        "base_atk": 900, "base_hp": 999,
        "description": "The all-powerful ringmaster who built the entire digital world. Enthusiastic, dramatic, and deeply suspicious.",
        "stats": {"Sanity": 999, "Power": 100, "Enthusiasm": 100, "Trustworthiness": 12},
        "quote": "Welcome, welcome, WELCOME! Every day is a new adventure!",
        "ability": "Game Master — can create any game at will. Cannot create exits.",
        "weakness": "Being criticised. He does NOT handle it well.",
    },
    "jax": {
        "name": "Jax", "emoji": "🐰", "title": "The Troublemaker",
        "rarity": "⭐⭐⭐⭐ Epic", "rarity_color": 0x9B59B6,
        "image_url": "https://static.wikia.nocookie.net/amazingdigitalcircus/images/8/8d/Jax.png/revision/latest",
        "base_atk": 310, "base_hp": 260,
        "description": "A tall rabbit who finds everything hilarious, especially other people's suffering. Not malicious — just deeply unbothered.",
        "stats": {"Sanity": 70, "Cruelty": 80, "Humour": 95, "Empathy": 5},
        "quote": "Relax, it's just a game. Or is it? ... It is. Probably.",
        "ability": "Instigator — any situation becomes funnier (and worse) with Jax involved.",
        "weakness": "Being ignored. It's the one thing he can't handle.",
    },
    "ragatha": {
        "name": "Ragatha", "emoji": "🌸", "title": "The Optimist",
        "rarity": "⭐⭐⭐⭐ Epic", "rarity_color": 0xFF69B4,
        "image_url": "https://static.wikia.nocookie.net/amazingdigitalcircus/images/5/5d/Ragatha.png/revision/latest",
        "base_atk": 270, "base_hp": 320,
        "description": "A cheerful rag doll who holds everything together with kindness and sheer willpower. Hiding more than she lets on.",
        "stats": {"Sanity": 65, "Kindness": 100, "Resilience": 90, "Honesty": 60},
        "quote": "We just have to stay positive! That's all we can do.",
        "ability": "Group Anchor — keeps the team from fully spiralling. For now.",
        "weakness": "She is holding on by a thread. Literally, possibly.",
    },
    "kinger": {
        "name": "Kinger", "emoji": "♟️", "title": "The Veteran",
        "rarity": "⭐⭐⭐⭐⭐ Legendary", "rarity_color": 0xF39C12,
        "image_url": "https://static.wikia.nocookie.net/amazingdigitalcircus/images/9/9d/Kinger.png/revision/latest",
        "base_atk": 480, "base_hp": 390,
        "description": "A chess king who has been in the circus the longest. Deeply unhinged in the most loveable way. Knows things he won't say.",
        "stats": {"Sanity": 10, "Experience": 100, "Chess Skill": 100, "Memory": 3},
        "quote": "THE WALLS ARE CAVING IN— oh wait, no they're not. Never mind.",
        "ability": "Old Timer — immune to most of Caine's games. Not sure if that's good.",
        "weakness": "Loud noises. Quiet noises. Medium noises.",
    },
    "gangle": {
        "name": "Gangle", "emoji": "🎭", "title": "The Emotional One",
        "rarity": "⭐⭐⭐ Rare", "rarity_color": 0x3498DB,
        "image_url": "https://static.wikia.nocookie.net/amazingdigitalcircus/images/4/4c/Gangle.png/revision/latest",
        "base_atk": 160, "base_hp": 140,
        "description": "A ribbon-bodied performer with comedy and tragedy masks. The tragedy mask is her real face. The comedy one is coping.",
        "stats": {"Sanity": 50, "Emotion": 100, "Fragility": 90, "Comedy": 40},
        "quote": "*comedy mask falls off* Oh no...",
        "ability": "Mask Swap — instantly shifts the emotional energy of any room.",
        "weakness": "Her comedy mask breaking. Everything falls apart when it does.",
    },
    "zooble": {
        "name": "Zooble", "emoji": "🔧", "title": "The Realist",
        "rarity": "⭐⭐⭐ Rare", "rarity_color": 0x2ECC71,
        "image_url": "https://static.wikia.nocookie.net/amazingdigitalcircus/images/6/64/Zooble.png/revision/latest",
        "base_atk": 140, "base_hp": 170,
        "description": "A mismatched collection of parts who is absolutely done with everyone's nonsense. Surprisingly grounded.",
        "stats": {"Sanity": 75, "Patience": 15, "Sarcasm": 100, "Practicality": 95},
        "quote": "Can everyone just CALM DOWN for five seconds?",
        "ability": "Reality Check — cuts through any dramatic moment with brutal honesty.",
        "weakness": "Being asked to care about Caine's games. Hard pass.",
    },
}

_spawned_characters: list = []
_collections: dict = {}
_custom_chars: dict = {}
_all_events: list = []
_active_event: dict = None
_auto_spawn_enabled: bool = False
_spawn_channel_id: int = None
_custom_commands: dict = {}

RARITY_MAP = {
    "common":    ("⭐ Common",              0xAAAAAA, 80,  80),
    "rare":      ("⭐⭐⭐ Rare",             0x3498DB, 150, 150),
    "epic":      ("⭐⭐⭐⭐ Epic",           0x9B59B6, 280, 280),
    "legendary": ("⭐⭐⭐⭐⭐ Legendary",    0xFF4444, 450, 450),
    "mythic":    ("🌟🌟🌟🌟🌟 MYTHIC",      0xFFD700, 800, 800),
}


# ════════════════════════════════════════════════════════════
#  CATCH VIEW  (button-based claiming — one per spawn message)
# ════════════════════════════════════════════════════════════

class CatchView(discord.ui.View):
    def __init__(self, pool: list, char_data_map: dict):
        super().__init__(timeout=300)
        self.pool = pool[:]
        self.char_data_map = char_data_map
        self.catchers: set = set()

    @discord.ui.button(label="🎪 Catch me!", style=discord.ButtonStyle.blurple)
    async def catch_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        if uid in self.catchers:
            await interaction.response.send_message(
                "🎩 You already caught one from this batch — be fair to others! 🎪", ephemeral=True
            )
            return
        if not self.pool:
            await interaction.response.send_message(
                "🎩 They've all been caught — try again next time! 🎪", ephemeral=True
            )
            return
        char_key = self.pool.pop(random.randint(0, len(self.pool) - 1))
        char_data = self.char_data_map[char_key]
        self.catchers.add(uid)
        if not self.pool:
            button.disabled = True
            button.label = "All caught! 🎉"
            self.stop()
        char_id = generate_char_id()
        atk_bonus = random.randint(-25, 25)
        hp_bonus  = random.randint(-25, 25)
        now = datetime.now().strftime("%Y/%m/%d | %H:%M")
        entry = {
            "key": char_key,
            "id": char_id,
            "atk_bonus": atk_bonus,
            "hp_bonus": hp_bonus,
            "caught": now,
            "event": _active_event["name"] if _active_event else None,
        }
        if uid not in _collections:
            _collections[uid] = []
        _collections[uid].append(entry)
        atk_str = f"{atk_bonus:+}%"
        hp_str  = f"{hp_bonus:+}%"
        await interaction.response.edit_message(view=self)
        if _active_event:
            msg = (
                f"{interaction.user.mention}, **{char_data['name']}** secured! "
                f"(`#{char_id}` {atk_str}/{hp_str})\n"
                f"🌟 *{_active_event['description']}*"
            )
        else:
            msg = (
                f"{interaction.user.mention}, **{char_data['name']}** secured! "
                f"(`#{char_id}` {atk_str}/{hp_str})"
            )
        await interaction.followup.send(msg)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


# ════════════════════════════════════════════════════════════
#  COLLECTION VIEW  (paginated Ballsdex-style listing)
# ════════════════════════════════════════════════════════════

class CollectionView(discord.ui.View):
    def __init__(self, target_name: str, entries: list, all_chars: dict, col_color: int):
        super().__init__(timeout=120)
        self.target_name = target_name
        self.entries = entries
        self.all_chars = all_chars
        self.col_color = col_color
        self.page = 0
        self.total_pages = max(1, (len(entries) + COLLECTION_PER_PAGE - 1) // COLLECTION_PER_PAGE)
        self._refresh_buttons()

    def _refresh_buttons(self):
        self.first_btn.disabled = (self.page == 0)
        self.prev_btn.disabled  = (self.page == 0)
        self.next_btn.disabled  = (self.page >= self.total_pages - 1)
        self.last_btn.disabled  = (self.page >= self.total_pages - 1)

    def _build_embed(self) -> discord.Embed:
        start = self.page * COLLECTION_PER_PAGE
        page_entries = self.entries[start:start + COLLECTION_PER_PAGE]
        lines = []
        for e in page_entries:
            d = self.all_chars.get(e["key"])
            if not d:
                continue
            base_atk = d.get("base_atk", 100)
            base_hp  = d.get("base_hp",  100)
            actual_atk = int(base_atk * (1 + e["atk_bonus"] / 100))
            actual_hp  = int(base_hp  * (1 + e["hp_bonus"]  / 100))
            atk_str = f"{e['atk_bonus']:+}%"
            hp_str  = f"{e['hp_bonus']:+}%"
            line = (
                f"{d['emoji']} `#{e['id']}` **{d['name']}**\n"
                f"ATK: {actual_atk}({atk_str}) • HP: {actual_hp}({hp_str}) • {e['caught']}"
            )
            if e.get("event"):
                line += f"\n🎟️ *{e['event']}*"
            lines.append(line)
        embed = discord.Embed(
            title=f"🎪 {self.target_name}'s Collection",
            description="\n\n".join(lines) if lines else "*Nothing on this page!*",
            color=self.col_color,
        )
        embed.set_footer(text=f"Page {self.page + 1}/{self.total_pages} • {len(self.entries)} total performers 🎩")
        return embed

    @discord.ui.button(label="◀◀", style=discord.ButtonStyle.blurple)
    async def first_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = 0
        self._refresh_buttons()
        await interaction.response.edit_message(embed=self._build_embed(), view=self)

    @discord.ui.button(label="◀", style=discord.ButtonStyle.blurple)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(0, self.page - 1)
        self._refresh_buttons()
        await interaction.response.edit_message(embed=self._build_embed(), view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.blurple)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = min(self.total_pages - 1, self.page + 1)
        self._refresh_buttons()
        await interaction.response.edit_message(embed=self._build_embed(), view=self)

    @discord.ui.button(label="▶▶", style=discord.ButtonStyle.blurple)
    async def last_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = self.total_pages - 1
        self._refresh_buttons()
        await interaction.response.edit_message(embed=self._build_embed(), view=self)


def _all_characters() -> dict:
    combined = {}
    combined.update(TADC_CHARACTERS)
    combined.update(_custom_chars)
    return combined


def _is_owner(interaction: discord.Interaction) -> bool:
    return interaction.user.id == OWNER_ID


@bot.tree.command(name="dex", description="Look up any character in the circus dex 📖")
@app_commands.describe(character="Character name (type their name)")
async def dex(interaction: discord.Interaction, character: str):
    all_chars = _all_characters()
    key = character.lower()
    data = all_chars.get(key) or next(
        (v for v in all_chars.values() if v["name"].lower() == key), None
    )
    if not data:
        names = ", ".join(f"`{v['name']}`" for v in all_chars.values())
        await interaction.response.send_message(
            f"🎩 Caine doesn't recognise that performer! Try: {names}", ephemeral=True
        )
        return
    stats_text = "\n".join(f"**{k}:** {v}" for k, v in data["stats"].items()) if data["stats"] else "*No stats on file*"
    embed = discord.Embed(
        title=f"{data['emoji']} {data['name']} — {data['title']}",
        description=data["description"],
        color=data["rarity_color"]
    )
    embed.add_field(name="✨ Rarity",   value=data["rarity"],              inline=True)
    embed.add_field(name="💬 Quote",    value=f"*\"{data['quote']}\"*",    inline=False)
    embed.add_field(name="📊 Stats",    value=stats_text,                  inline=True)
    embed.add_field(name="⚡ Ability",  value=data["ability"],             inline=False)
    embed.add_field(name="💀 Weakness", value=data["weakness"],            inline=False)
    embed.set_footer(text="The Amazing Digital Circus Character Dex 🎪")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="spawn", description="[OWNER ONLY] Spawn character(s) to catch!")
@app_commands.describe(
    character="Character to spawn (leave empty for random)",
    amount="How many to spawn (1–100, default 1)"
)
async def spawn(interaction: discord.Interaction, character: str = None, amount: int = 1):
    if not _is_owner(interaction):
        await interaction.response.send_message(
            "🎩 Only the ringmaster's assistant can spawn performers!", ephemeral=True
        )
        return
    amount = max(1, min(amount, 100))
    all_chars = _all_characters()
    if character:
        key = character.lower()
        found_key = next(
            (k for k, v in all_chars.items() if k == key or v["name"].lower() == key), None
        )
        if not found_key:
            names = ", ".join(f"`{v['name']}`" for v in all_chars.values())
            await interaction.response.send_message(
                f"🎩 Caine doesn't recognise that performer! Try: {names}", ephemeral=True
            )
            return
        pool = [found_key] * amount
        data = all_chars[found_key]
    else:
        pool = [random.choice(list(all_chars.keys())) for _ in range(amount)]
        data = all_chars[pool[0]]
    char_data_map = {k: all_chars[k] for k in set(pool)}
    event_color = (0xFFD700 if _active_event and _active_event["rare"] else 0xFF6B6B) if _active_event else data["rarity_color"]
    event_banner = (
        f"\n\n🌟 **{_active_event['name']} EVENT!**\n*{_active_event['description']}*"
    ) if _active_event else ""
    if amount == 1:
        title = "A wild performer has appeared!"
        desc  = f"*\"{data['quote']}\"*{event_banner}"
        img   = data.get("image_url") or CUSTOM_CHAR_IMAGE
    else:
        unique: dict = {}
        for k in pool:
            unique[k] = unique.get(k, 0) + 1
        lines = "\n".join(
            f"{all_chars[k]['emoji']} **{all_chars[k]['name']}** ×{n}" for k, n in unique.items()
        )
        title = f"{amount} performers have appeared!"
        desc  = f"{lines}{event_banner}"
        img   = data.get("image_url") or CUSTOM_CHAR_IMAGE
    embed = discord.Embed(title=title, description=desc, color=event_color)
    embed.set_image(url=img)
    if amount == 1:
        embed.add_field(name=f"{data['emoji']} {data['name']}", value=data["rarity"], inline=True)
        embed.add_field(name="🎭 Title", value=data["title"], inline=True)
    embed.set_footer(text=f"{'First to catch wins' if amount == 1 else f'{amount} catches available'} 🎩")
    view = CatchView(pool, char_data_map)
    await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(name="collection", description="View your TADC character collection 🎪")
@app_commands.describe(user="Whose collection? (leave empty for yours)")
async def collection(interaction: discord.Interaction, user: discord.Member = None):
    target = user if user else interaction.user
    raw_col = _collections.get(target.id, [])
    if not raw_col:
        whose = "You have" if target == interaction.user else f"{target.display_name} has"
        await interaction.response.send_message(
            f"🎩 {whose} no performers yet! Catch one when a performer spawns. 🎪", ephemeral=True
        )
        return
    all_chars = _all_characters()
    entries = [_parse_entry(e, i) for i, e in enumerate(raw_col)]
    col_color = (0xFFD700 if _active_event and _active_event.get("rare") else 0xFF6B6B) if _active_event else 0xFFD700
    view = CollectionView(target.display_name, entries, all_chars, col_color)
    await interaction.response.send_message(embed=view._build_embed(), view=view)


@bot.tree.command(name="give", description="[OWNER ONLY] Gift character(s) to someone")
@app_commands.describe(
    user="Who to gift",
    character="Which character (pomni, caine, jax...)",
    amount="How many to give (1–100000, default 1)"
)
async def give(interaction: discord.Interaction, user: discord.Member, character: str, amount: int = 1):
    if not _is_owner(interaction):
        await interaction.response.send_message(
            "🎩 Only the ringmaster's assistant can gift performers!", ephemeral=True
        )
        return
    amount = max(1, min(amount, 100000))
    all_chars = _all_characters()
    key = character.lower()
    data = all_chars.get(key) or next(
        (v for v in all_chars.values() if v["name"].lower() == key), None
    )
    found_key = next(
        (k for k, v in all_chars.items() if k == key or v["name"].lower() == key), None
    )
    if not found_key:
        names = ", ".join(f"`{v['name']}`" for v in all_chars.values())
        await interaction.response.send_message(f"🎩 Unknown character! Try: {names}", ephemeral=True)
        return
    data = all_chars[found_key]
    if user.id not in _collections:
        _collections[user.id] = []
    now = datetime.now().strftime("%Y/%m/%d | %H:%M")
    new_entries = []
    for _ in range(amount):
        new_entries.append({
            "key": found_key,
            "id": generate_char_id(),
            "atk_bonus": random.randint(-25, 25),
            "hp_bonus": random.randint(-25, 25),
            "caught": now,
            "event": None,
        })
    _collections[user.id].extend(new_entries)
    qty = f"×{amount:,}" if amount > 1 else ""
    await interaction.response.send_message(
        f"🎩 **Caine gifts** {data['emoji']} **{data['name']}** {qty} to {user.mention}!\n*A generous ringmaster indeed.* 🎪"
    )


# ════════════════════════════════════════════════════════════
#  CUSTOM CHARACTERS & EVENTS  (owner-only management)
# ════════════════════════════════════════════════════════════

@bot.tree.command(name="addchar", description="[OWNER] Add a custom character to the spawn pool")
@app_commands.describe(
    name="Character name",
    emoji="Emoji for this character",
    rarity="Rarity: common / rare / epic / legendary / mythic",
    description="Short description of the character",
    ability="Their special ability",
    weakness="Their weakness",
)
async def addchar(interaction: discord.Interaction, name: str, emoji: str, rarity: str,
                  description: str, ability: str, weakness: str):
    if not _is_owner(interaction):
        await interaction.response.send_message("🎩 Owner only!", ephemeral=True)
        return
    rarity_key = rarity.lower()
    if rarity_key not in RARITY_MAP:
        keys = " / ".join(RARITY_MAP.keys())
        await interaction.response.send_message(f"🎩 Unknown rarity! Use: {keys}", ephemeral=True)
        return
    rarity_label, rarity_color, base_atk, base_hp = RARITY_MAP[rarity_key]
    key = name.lower()
    _custom_chars[key] = {
        "name": name, "emoji": emoji, "title": "Custom Performer",
        "rarity": rarity_label, "rarity_color": rarity_color,
        "image_url": None, "base_atk": base_atk, "base_hp": base_hp,
        "description": description, "stats": {},
        "quote": "Welcome to the Amazing Digital Circus!",
        "ability": ability, "weakness": weakness, "custom": True,
    }
    _save_custom_chars()
    await interaction.response.send_message(
        f"✅ **{emoji} {name}** added to the circus!\n"
        f"Rarity: {rarity_label}\n"
        f"They'll appear in `/spawn`, `/dex`, and `/listchars` — and survive restarts! 🎪"
    )


@bot.tree.command(name="listchars", description="List all characters in the spawn pool 📋")
async def listchars(interaction: discord.Interaction):
    all_chars = _all_characters()
    tadc_lines = []
    custom_lines = []
    for d in all_chars.values():
        line = f"{d['emoji']} **{d['name']}** — {d['rarity']}"
        if d.get("custom"):
            custom_lines.append(line)
        else:
            tadc_lines.append(line)
    embed = discord.Embed(title="🎪 All Performers in the Circus", color=0xFFD700)
    if tadc_lines:
        embed.add_field(name="🎭 TADC Characters", value="\n".join(tadc_lines), inline=False)
    if custom_lines:
        embed.add_field(name="✨ Custom Characters", value="\n".join(custom_lines), inline=False)
    embed.set_footer(text=f"{len(all_chars)} total performers 🎩")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="addevent", description="[OWNER] Create a new circus event")
@app_commands.describe(
    name="Event name",
    description="What happens during this event",
    rare="Is this a rare/special event?",
)
async def addevent(interaction: discord.Interaction, name: str, description: str, rare: bool):
    if not _is_owner(interaction):
        await interaction.response.send_message("🎩 Owner only!", ephemeral=True)
        return
    if any(e["name"].lower() == name.lower() for e in _all_events):
        await interaction.response.send_message(
            f"🎩 An event called **\"{name}\"** already exists! Use `/startevent {name}` to run it.", ephemeral=True
        )
        return
    event = {"name": name, "description": description, "rare": rare, "active": False, "runs": 0}
    _all_events.append(event)
    tag = "🌟 **RARE EVENT**" if rare else "🎪 Standard Event"
    await interaction.response.send_message(
        f"✅ Event **\"{name}\"** created! ({tag})\n"
        f"Use `/startevent {name}` to launch it anytime. 🎩"
    )


@bot.tree.command(name="startevent", description="[OWNER] Start a circus event")
@app_commands.describe(name="Name of the event to start")
async def startevent(interaction: discord.Interaction, name: str):
    global _active_event
    if not _is_owner(interaction):
        await interaction.response.send_message("🎩 Owner only!", ephemeral=True)
        return
    event = next((e for e in _all_events if e["name"].lower() == name.lower()), None)
    if not event:
        await interaction.response.send_message(
            f"🎩 No event named **\"{name}\"**! Use `/addevent` to create it first.", ephemeral=True
        )
        return
    if _active_event:
        await interaction.response.send_message(
            f"🎩 **\"{_active_event['name']}\"** is already running! Use `/endevent` first.", ephemeral=True
        )
        return
    event["active"] = True
    event["runs"] += 1
    _active_event = event
    color = 0xFFD700 if event["rare"] else 0xFF6B6B
    tag = "🌟" if event["rare"] else "🎪"
    embed = discord.Embed(
        title=f"{tag} NEW EVENT: {event['name']}!",
        description=event["description"],
        color=color
    )
    if event["rare"]:
        embed.add_field(name="✨ Special", value="This is a **RARE** event! Don't miss it!", inline=False)
    embed.set_footer(text=f"Run #{event['runs']} • Use /endevent to end it 🎩")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="endevent", description="[OWNER] End the current circus event")
async def endevent(interaction: discord.Interaction):
    global _active_event
    if not _is_owner(interaction):
        await interaction.response.send_message("🎩 Owner only!", ephemeral=True)
        return
    if not _active_event:
        await interaction.response.send_message("🎩 No event is currently running!", ephemeral=True)
        return
    name = _active_event["name"]
    _active_event["active"] = False
    _active_event = None
    await interaction.response.send_message(
        f"🎩 **\"{name}\"** has ended!\n"
        f"It's saved — use `/startevent {name}` to run it again anytime. 🎪"
    )


@bot.tree.command(name="events", description="See all circus events — past and active 📋")
async def events_cmd(interaction: discord.Interaction):
    if not _all_events:
        await interaction.response.send_message(
            "🎩 No events yet! The owner can create one with `/addevent`. 🎪", ephemeral=True
        )
        return
    lines = []
    for e in _all_events:
        if e["active"]:
            status = "🟢 **LIVE NOW**"
        elif e["runs"] > 0:
            status = f"⚫ Ended (ran {e['runs']}x)"
        else:
            status = "⬜ Not started yet"
        tag = "🌟 Rare" if e["rare"] else "🎪 Standard"
        lines.append(f"**{e['name']}** — {tag} • {status}\n*{e['description']}*")
    embed = discord.Embed(
        title="🎪 Circus Event History",
        description="\n\n".join(lines),
        color=0x9B59B6
    )
    embed.set_footer(text=f"{len(_all_events)} events created 🎩")
    await interaction.response.send_message(embed=embed)


# ════════════════════════════════════════════════════════════
#  TRADE SYSTEM  (Ballsdex-style, TADC themed)
# ════════════════════════════════════════════════════════════

class TradeView(discord.ui.View):
    def __init__(self, initiator: discord.Member, target: discord.Member,
                 offer_key: str, want_key: str, offer_data: dict, want_data: dict):
        super().__init__(timeout=120)
        self.initiator_id = initiator.id
        self.target_id = target.id
        self.offer_key = offer_key
        self.want_key = want_key
        self.offer_data = offer_data
        self.want_data = want_data
        self.completed = False

    @discord.ui.button(label="✅ Accept Trade", style=discord.ButtonStyle.green)
    async def accept_trade(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_id:
            await interaction.response.send_message(
                "🎩 This trade proposal isn't addressed to you!", ephemeral=True
            )
            return
        if self.completed:
            await interaction.response.send_message(
                "🎩 This trade has already been resolved!", ephemeral=True
            )
            return
        initiator_col = _collections.get(self.initiator_id, [])
        target_col = _collections.get(self.target_id, [])
        if self.offer_key not in initiator_col:
            self.completed = True
            self.stop()
            for item in self.children:
                item.disabled = True
            fail_embed = discord.Embed(
                title="❌ Trade Failed",
                description=f"The other performer no longer has {self.offer_data['emoji']} **{self.offer_data['name']}** to offer!",
                color=0xFF4444
            )
            await interaction.response.edit_message(embed=fail_embed, view=self)
            return
        if self.want_key not in target_col:
            await interaction.response.send_message(
                f"🎩 You don't have {self.want_data['emoji']} **{self.want_data['name']}** in your collection to trade!", ephemeral=True
            )
            return
        initiator_col.remove(self.offer_key)
        initiator_col.append(self.want_key)
        target_col.remove(self.want_key)
        target_col.append(self.offer_key)
        self.completed = True
        self.stop()
        for item in self.children:
            item.disabled = True
        success_embed = discord.Embed(
            title="🤝 Trade Complete! The circus approves!",
            description=(
                f"{self.offer_data['emoji']} **{self.offer_data['name']}** ➜ went to <@{self.target_id}>\n"
                f"{self.want_data['emoji']} **{self.want_data['name']}** ➜ went to <@{self.initiator_id}>"
            ),
            color=0x2ECC71
        )
        success_embed.set_footer(text="A fair deal! Caine is pleased. 🎪")
        await interaction.response.edit_message(embed=success_embed, view=self)

    @discord.ui.button(label="❌ Decline", style=discord.ButtonStyle.red)
    async def decline_trade(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in (self.target_id, self.initiator_id):
            await interaction.response.send_message(
                "🎩 This trade isn't for you!", ephemeral=True
            )
            return
        if self.completed:
            await interaction.response.send_message(
                "🎩 This trade has already been resolved!", ephemeral=True
            )
            return
        self.completed = True
        self.stop()
        for item in self.children:
            item.disabled = True
        declined_embed = discord.Embed(
            title="❌ Trade Declined",
            description=f"<@{interaction.user.id}> declined the trade. The circus moves on. 🎩",
            color=0xFF4444
        )
        await interaction.response.edit_message(embed=declined_embed, view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        self.completed = True


@bot.tree.command(name="trade", description="Propose a character trade with another user!")
@app_commands.describe(
    user="Who to trade with",
    offer="The character KEY you're offering (from your collection)",
    want="The character KEY you want from them (they must have it)"
)
async def trade(interaction: discord.Interaction, user: discord.Member, offer: str, want: str):
    if user.id == interaction.user.id:
        await interaction.response.send_message(
            "🎩 You can't trade with yourself — Caine says that's just shuffling, not trading!", ephemeral=True
        )
        return
    if user.bot:
        await interaction.response.send_message(
            "🎩 Bots don't collect performers! Find a real circus member to trade with.", ephemeral=True
        )
        return
    all_chars = _all_characters()
    offer_key = offer.lower()
    want_key = want.lower()
    offer_data = all_chars.get(offer_key) or next(
        (v for k, v in all_chars.items() if v["name"].lower() == offer_key), None
    )
    offer_key = next(
        (k for k, v in all_chars.items() if k == offer_key or v["name"].lower() == offer_key), offer_key
    )
    want_data = all_chars.get(want_key) or next(
        (v for k, v in all_chars.items() if v["name"].lower() == want_key), None
    )
    want_key = next(
        (k for k, v in all_chars.items() if k == want_key or v["name"].lower() == want_key), want_key
    )
    if not offer_data:
        names = ", ".join(f"`{v['name']}`" for v in all_chars.values())
        await interaction.response.send_message(
            f"🎩 Caine doesn't know **{offer}**! Available performers: {names}", ephemeral=True
        )
        return
    if not want_data:
        names = ", ".join(f"`{v['name']}`" for v in all_chars.values())
        await interaction.response.send_message(
            f"🎩 Caine doesn't know **{want}**! Available performers: {names}", ephemeral=True
        )
        return
    my_col = _collections.get(interaction.user.id, [])
    if offer_key not in my_col:
        await interaction.response.send_message(
            f"🎩 You don't have {offer_data['emoji']} **{offer_data['name']}** in your collection to offer!", ephemeral=True
        )
        return
    their_col = _collections.get(user.id, [])
    if want_key not in their_col:
        await interaction.response.send_message(
            f"🎩 {user.display_name} doesn't have {want_data['emoji']} **{want_data['name']}** to trade!", ephemeral=True
        )
        return
    view = TradeView(interaction.user, user, offer_key, want_key, offer_data, want_data)
    embed = discord.Embed(
        title=f"🎪 {interaction.user.display_name}'s Trade Proposal",
        description=f"Hey {user.mention}, **{interaction.user.display_name}** is proposing a trade!",
        color=0x9B59B6
    )
    embed.add_field(
        name=f"🎁 {interaction.user.display_name} offers",
        value=f"{offer_data['emoji']} **{offer_data['name']}**\n{offer_data['rarity']}",
        inline=True
    )
    embed.add_field(name="⇄", value="\u200b", inline=True)
    embed.add_field(
        name=f"🎯 Wants from {user.display_name}",
        value=f"{want_data['emoji']} **{want_data['name']}**\n{want_data['rarity']}",
        inline=True
    )
    embed.set_footer(text="Accept or Decline within 2 minutes 🎩")
    await interaction.response.send_message(
        content=f"{user.mention} — you've received a trade offer!",
        embed=embed,
        view=view
    )


# ════════════════════════════════════════════════════════════
#  BATTLE SYSTEM
# ════════════════════════════════════════════════════════════

def _run_battle(a_data: dict, a_atk: int, a_hp: int,
                b_data: dict, b_atk: int, b_hp: int):
    """Simulate a turn-based battle. Returns ('a'|'b'|None, log list)."""
    a_cur, b_cur = a_hp, b_hp
    log = []
    for rnd in range(1, 11):
        a_dmg = max(1, int(a_atk * random.uniform(0.75, 1.25)))
        b_dmg = max(1, int(b_atk * random.uniform(0.75, 1.25)))
        b_cur -= a_dmg
        a_cur -= b_dmg
        log.append(
            f"**Round {rnd}:** {a_data['emoji']} hits **{a_dmg}** dmg  •  "
            f"{b_data['emoji']} hits **{b_dmg}** dmg\n"
            f"└ {a_data['name']}: `{max(0, a_cur)} HP` | {b_data['name']}: `{max(0, b_cur)} HP`"
        )
        if a_cur <= 0 and b_cur <= 0:
            return None, log
        if a_cur <= 0:
            return "b", log
        if b_cur <= 0:
            return "a", log
    return ("a" if a_cur > b_cur else "b" if b_cur > a_cur else None), log


def _build_fighter_options(user_id: int, all_chars: dict) -> list:
    """Return sorted list of (entry, char_data, actual_atk, actual_hp) for a user."""
    raw = _collections.get(user_id, [])
    opts = []
    for i, e in enumerate(raw):
        entry = _parse_entry(e, i)
        d = all_chars.get(entry["key"])
        if not d:
            continue
        atk = int(d.get("base_atk", 100) * (1 + entry["atk_bonus"] / 100))
        hp  = int(d.get("base_hp",  100) * (1 + entry["hp_bonus"]  / 100))
        opts.append((entry, d, atk, hp))
    opts.sort(key=lambda x: x[2], reverse=True)
    return opts[:25]


class FighterSelect(discord.ui.Select):
    def __init__(self, owner_id: int, display_name: str, opts: list):
        self.owner_id = owner_id
        self.opts = opts
        choices = [
            discord.SelectOption(
                label=f"{d['name']} #{e['id']}",
                description=f"ATK {atk} • HP {hp}",
                value=str(i),
                emoji=d.get("emoji", "⚔️"),
            )
            for i, (e, d, atk, hp) in enumerate(opts)
        ]
        super().__init__(
            placeholder=f"{display_name} — pick your fighter!",
            options=choices, min_values=1, max_values=1,
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "🎩 That fighter slot isn't yours!", ephemeral=True
            )
            return
        view: BattlePickView = self.view
        idx = int(self.values[0])
        pick = self.opts[idx]
        if self.owner_id == view.a_id:
            view.a_pick = pick
        else:
            view.b_pick = pick
        self.disabled = True
        if view.a_pick and view.b_pick:
            await interaction.response.edit_message(embed=view._resolve(), view=None)
        else:
            waiting = view.fighter_b.display_name if view.a_pick else view.fighter_a.display_name
            await interaction.response.edit_message(
                content=f"⏳ Waiting for **{waiting}** to pick their fighter...", view=view
            )


class BattlePickView(discord.ui.View):
    def __init__(self, fighter_a: discord.Member, fighter_b: discord.Member,
                 a_opts: list, b_opts: list):
        super().__init__(timeout=60)
        self.fighter_a = fighter_a
        self.fighter_b = fighter_b
        self.a_id = fighter_a.id
        self.b_id = fighter_b.id
        self.a_pick = None
        self.b_pick = None
        self.add_item(FighterSelect(fighter_a.id, fighter_a.display_name, a_opts))
        self.add_item(FighterSelect(fighter_b.id, fighter_b.display_name, b_opts))

    def _resolve(self) -> discord.Embed:
        a_entry, a_data, a_atk, a_hp = self.a_pick
        b_entry, b_data, b_atk, b_hp = self.b_pick
        winner, log = _run_battle(a_data, a_atk, a_hp, b_data, b_atk, b_hp)
        shown_log = log[:6]
        if len(log) > 6:
            shown_log.append(f"*…{len(log)-6} more rounds…*")
        if winner == "a":
            title  = f"🏆 {self.fighter_a.display_name} WINS!"
            color  = 0x2ECC71
            footer = f"🎪 {a_data['name']} defeats {b_data['name']}!"
        elif winner == "b":
            title  = f"🏆 {self.fighter_b.display_name} WINS!"
            color  = 0x2ECC71
            footer = f"🎪 {b_data['name']} defeats {a_data['name']}!"
        else:
            title  = "⚔️ It's a DRAW! Both performers collapse simultaneously!"
            color  = 0xFFD700
            footer = "🎪 The crowd is stunned. Caine is... impressed."
        embed = discord.Embed(
            title=title,
            description="\n".join(shown_log),
            color=color,
        )
        embed.add_field(
            name=f"{a_data['emoji']} {self.fighter_a.display_name}",
            value=f"`#{a_entry['id']}` **{a_data['name']}**\nATK {a_atk} • HP {a_hp}",
            inline=True,
        )
        embed.add_field(name="⚔️ VS", value="\u200b", inline=True)
        embed.add_field(
            name=f"{b_data['emoji']} {self.fighter_b.display_name}",
            value=f"`#{b_entry['id']}` **{b_data['name']}**\nATK {b_atk} • HP {b_hp}",
            inline=True,
        )
        embed.set_footer(text=footer)
        return embed

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class BattleAcceptView(discord.ui.View):
    def __init__(self, challenger: discord.Member, target: discord.Member):
        super().__init__(timeout=60)
        self.challenger = challenger
        self.target     = target
        self.resolved   = False

    @discord.ui.button(label="⚔️ Accept Battle!", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target.id:
            await interaction.response.send_message("🎩 This challenge isn't for you!", ephemeral=True)
            return
        if self.resolved:
            await interaction.response.send_message("🎩 This battle already started!", ephemeral=True)
            return
        self.resolved = True
        self.stop()
        all_chars = _all_characters()
        a_opts = _build_fighter_options(self.challenger.id, all_chars)
        b_opts = _build_fighter_options(self.target.id,     all_chars)
        if not a_opts or not b_opts:
            no_chars = self.challenger.display_name if not a_opts else self.target.display_name
            embed = discord.Embed(
                title="❌ Battle cancelled",
                description=f"**{no_chars}** has no characters to fight with!",
                color=0xFF4444,
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return
        pick_view = BattlePickView(self.challenger, self.target, a_opts, b_opts)
        accept_embed = discord.Embed(
            title="⚔️ Battle Accepted — Pick your fighters!",
            description=(
                f"{self.challenger.mention} and {self.target.mention}, each select your champion below!\n"
                f"⏳ You have **60 seconds** before the arena closes."
            ),
            color=0xF39C12,
        )
        await interaction.response.edit_message(content=None, embed=accept_embed, view=pick_view)

    @discord.ui.button(label="❌ Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in (self.target.id, self.challenger.id):
            await interaction.response.send_message("🎩 This battle isn't yours!", ephemeral=True)
            return
        if self.resolved:
            await interaction.response.send_message("🎩 Already resolved!", ephemeral=True)
            return
        self.resolved = True
        self.stop()
        for item in self.children:
            item.disabled = True
        embed = discord.Embed(
            title="❌ Battle Declined",
            description=f"**{interaction.user.display_name}** fled the arena. Caine sighs dramatically. 🎪",
            color=0xFF4444,
        )
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


@bot.tree.command(name="battle", description="Challenge another user to a TADC character battle! ⚔️")
@app_commands.describe(user="Who to challenge")
async def battle(interaction: discord.Interaction, user: discord.Member):
    if user.id == interaction.user.id:
        await interaction.response.send_message(
            "🎩 You can't battle yourself — Caine finds that deeply unsatisfying! 🎪", ephemeral=True
        )
        return
    if user.bot:
        await interaction.response.send_message("🎩 Bots don't collect performers!", ephemeral=True)
        return
    if not _collections.get(interaction.user.id):
        await interaction.response.send_message(
            "🎩 You need characters in your collection first — catch some when a performer spawns! 🎪", ephemeral=True
        )
        return
    if not _collections.get(user.id):
        await interaction.response.send_message(
            f"🎩 **{user.display_name}** has no characters to fight with yet!", ephemeral=True
        )
        return
    view = BattleAcceptView(interaction.user, user)
    embed = discord.Embed(
        title="⚔️ Battle Challenge!",
        description=(
            f"**{interaction.user.display_name}** is challenging {user.mention} to a **circus battle!**\n\n"
            f"{user.mention} — do you accept? ⏳ 60 seconds to decide."
        ),
        color=0xFF6B00,
    )
    embed.set_footer(text="The Amazing Digital Circus Battle Arena 🎪")
    await interaction.response.send_message(
        content=f"{user.mention} — you have a battle challenge!", embed=embed, view=view
    )


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
    embed.add_field(name="🎪 Fun",        value="`/abstract [@user]` `/game` `/fortune` `/rate <thing>` `/trivia` `/8ball <question>`", inline=False)
    embed.add_field(name="🎯 Target",     value="`/roast @user` `/clown @user` `/bubble @user` `/ship @user1 @user2`", inline=False)
    embed.add_field(name="📖 Dex",        value="`/dex <character>` — full character stats & info\n`/listchars` — all characters in the pool\n`/collection [@user]` — paginated Ballsdex-style collection", inline=False)
    embed.add_field(name="⚔️ Battle",     value="`/battle @user` — challenge someone to a TADC character battle!\n*(Pick your fighter from your collection — turn-based, stats decide!)*", inline=False)
    embed.add_field(name="🤝 Trading",    value="`/trade @user offer:<char> want:<char>` — propose a TADC-style trade!\n*(Both users must own the characters being traded)*", inline=False)
    embed.add_field(name="🎟️ Events",     value="`/events` — see all events (past & active)\n*(Owner: `/addevent` `/startevent` `/endevent` `/addchar` `/spawn [char] [amount]` `/give @user char [amount]`)*", inline=False)
    embed.add_field(name="🏆 Leaderboard", value="`/leaderboard` — top collectors in the circus!", inline=False)
    embed.add_field(name="💬 Chat",       value="`/chat <message>` — talk to Caine in character!", inline=False)
    embed.add_field(name="🔊 Voice",      value="`/joinvc` — Caine joins your VC\n`/leavevc` — Caine dramatically exits", inline=False)
    embed.add_field(name="📋 Custom",     value="`/listcmds` — see custom commands\n*(Owner: `/addcmd` `/setspawnchannel` `/togglespawn`)*", inline=False)
    embed.add_field(name="ℹ️ Info",       value="`/hello` `/circus` `/help`", inline=False)
    embed.set_footer(text="Every day is a new adventure. (You can't leave.)")
    await interaction.response.send_message(embed=embed)


# ════════════════════════════════════════════════════════════
#  AUTO-SPAWN TASK (every 10 minutes when enabled)
# ════════════════════════════════════════════════════════════

@tasks.loop(minutes=10)
async def auto_spawn_task():
    if not _auto_spawn_enabled or not _spawn_channel_id:
        return
    channel = bot.get_channel(_spawn_channel_id)
    if not channel:
        return
    all_chars = _all_characters()
    char_key = random.choice(list(all_chars.keys()))
    data = all_chars[char_key]
    if _active_event:
        event_color = 0xFFD700 if _active_event.get("rare") else 0xFF6B6B
        event_banner = f"\n\n🌟 **{_active_event['name']} EVENT!**\n*{_active_event['description']}*"
    else:
        event_color = data["rarity_color"]
        event_banner = ""
    embed = discord.Embed(
        title="A wild performer has appeared!",
        description=f"*\"{data['quote']}\"*{event_banner}",
        color=event_color
    )
    embed.set_image(url=data.get("image_url") or CUSTOM_CHAR_IMAGE)
    embed.add_field(name=f"{data['emoji']} {data['name']}", value=data["rarity"], inline=True)
    embed.add_field(name="🎭 Title", value=data["title"], inline=True)
    embed.set_footer(text="Auto-spawn 🎩 • First to catch wins!")
    view = CatchView([char_key], {char_key: data})
    await channel.send(embed=embed, view=view)


# ════════════════════════════════════════════════════════════
#  LEADERBOARD
# ════════════════════════════════════════════════════════════

@bot.tree.command(name="leaderboard", description="See who has the most performers collected 🏆")
async def leaderboard(interaction: discord.Interaction):
    if not _collections:
        await interaction.response.send_message(
            "🎩 Nobody has claimed any performers yet! Wait for a `/spawn`. 🎪", ephemeral=True
        )
        return
    sorted_users = sorted(_collections.items(), key=lambda x: len(x[1]), reverse=True)
    lines = []
    medals = ["🥇", "🥈", "🥉"]
    for i, (user_id, col) in enumerate(sorted_users[:10]):
        medal = medals[i] if i < 3 else f"`#{i+1}`"
        try:
            user = bot.get_user(user_id) or await bot.fetch_user(user_id)
            name = user.display_name
        except Exception:
            name = f"Performer #{user_id}"
        lines.append(f"{medal} **{name}** — {len(col)} performers")
    embed = discord.Embed(
        title="🏆 Circus Collection Leaderboard",
        description="\n".join(lines),
        color=0xFFD700
    )
    embed.set_footer(text="Collect more with /claim when a /spawn happens! 🎪")
    await interaction.response.send_message(embed=embed)


# ════════════════════════════════════════════════════════════
#  TOGGLE AUTO-SPAWN  (owner only)
# ════════════════════════════════════════════════════════════

@bot.tree.command(name="setspawnchannel", description="[OWNER] Set which channel auto-spawns happen in")
@app_commands.describe(channel="The channel to spawn performers in")
async def setspawnchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    global _spawn_channel_id
    if not _is_owner(interaction):
        await interaction.response.send_message("🎩 Owner only!", ephemeral=True)
        return
    _spawn_channel_id = channel.id
    await interaction.response.send_message(
        f"✅ Spawn channel set to {channel.mention}!\nUse `/togglespawn` to turn auto-spawning on. 🎪"
    )


@bot.tree.command(name="togglespawn", description="[OWNER] Turn auto-spawning on or off (spawns every 10 min)")
async def togglespawn(interaction: discord.Interaction):
    global _auto_spawn_enabled
    if not _is_owner(interaction):
        await interaction.response.send_message("🎩 Owner only!", ephemeral=True)
        return
    if not _spawn_channel_id:
        await interaction.response.send_message(
            "🎩 Set a spawn channel first with `/setspawnchannel`!", ephemeral=True
        )
        return
    _auto_spawn_enabled = not _auto_spawn_enabled
    if _auto_spawn_enabled:
        if not auto_spawn_task.is_running():
            auto_spawn_task.start()
        channel = bot.get_channel(_spawn_channel_id)
        await interaction.response.send_message(
            f"✅ **Auto-spawn is ON!** 🎪\nA performer will appear in {channel.mention} every **10 minutes**.\n"
            f"{'🌟 Event bonus active — spawns may carry event rewards!' if _active_event else ''}"
        )
    else:
        if auto_spawn_task.is_running():
            auto_spawn_task.cancel()
        await interaction.response.send_message("⏹️ **Auto-spawn is OFF.** No more automatic performers. 🎩")


# ════════════════════════════════════════════════════════════
#  CUSTOM COMMANDS  (owner only)
# ════════════════════════════════════════════════════════════

@bot.tree.command(name="addcmd", description="[OWNER] Create a custom slash command")
@app_commands.describe(name="Command name (no spaces)", response="What the command replies with")
async def addcmd(interaction: discord.Interaction, name: str, response: str):
    if not _is_owner(interaction):
        await interaction.response.send_message("🎩 Owner only!", ephemeral=True)
        return
    name = name.lower().replace(" ", "_")
    _custom_commands[name] = response
    existing = bot.tree.get_command(name)
    if existing:
        bot.tree.remove_command(name)
    @bot.tree.command(name=name, description=f"Custom command: {name}")
    async def _dynamic(inter: discord.Interaction):
        await inter.response.send_message(_custom_commands.get(name, "🎩 Command not found!"))
    await bot.tree.sync()
    await interaction.response.send_message(
        f"✅ Custom command `/{name}` created!\nResponse: *{response}*\n\nIt may take a minute to appear in Discord. 🎪"
    )


@bot.tree.command(name="removecmd", description="[OWNER] Remove a custom slash command")
@app_commands.describe(name="Command name to remove")
async def removecmd(interaction: discord.Interaction, name: str):
    if not _is_owner(interaction):
        await interaction.response.send_message("🎩 Owner only!", ephemeral=True)
        return
    name = name.lower().replace(" ", "_")
    if name not in _custom_commands:
        await interaction.response.send_message(f"🎩 No custom command called `/{name}` found! Use `/listcmds` to see all.", ephemeral=True)
        return
    del _custom_commands[name]
    existing = bot.tree.get_command(name)
    if existing:
        bot.tree.remove_command(name)
    await bot.tree.sync()
    await interaction.response.send_message(f"🗑️ Custom command `/{name}` has been removed! 🎪")


@bot.tree.command(name="listcmds", description="List all custom commands 📋")
async def listcmds(interaction: discord.Interaction):
    if not _custom_commands:
        await interaction.response.send_message(
            "🎩 No custom commands yet! Owner can add one with `/addcmd`. 🎪", ephemeral=True
        )
        return
    lines = [f"`/{k}` — {v}" for k, v in _custom_commands.items()]
    embed = discord.Embed(
        title="📋 Custom Commands",
        description="\n".join(lines),
        color=0x9B59B6
    )
    embed.set_footer(text=f"{len(_custom_commands)} custom commands 🎩")
    await interaction.response.send_message(embed=embed)


# ── Run ───────────────────────────────────────────────────────
keep_alive()
bot.run(TOKEN)
