import os
import random
import discord
from discord import app_commands
from discord.ext import commands, tasks
from keep_alive import keep_alive

TOKEN = os.environ.get("BOT_TOKEN", "")
if not TOKEN:
    raise SystemExit("[ERROR] No BOT_TOKEN found in Replit Secrets.")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"The Amazing Digital Circus is open! Logged in as {bot.user}")
    print("Slash commands synced. Bot works in servers and DMs.")

CAINE_RESPONSES = {
    ("hello", "hi", "hey", "howdy", "greetings", "sup", "yo"): [
        "HELLO there, new performer! Welcome to the most SPECTACULAR show in the digital realm! 🎪",
        "Oh how DELIGHTFUL, a visitor! Pull up a seat — the show never stops here!",
        "Why HELLO! Caine is SO pleased you stopped by. Can I interest you in a game? 🎩",
        "Greetings, greetings! Every arrival is a cause for CELEBRATION! *confetti explodes*",
    ],
    ("escape", "exit", "leave", "out", "way out", "door", "go home", "free"): [
        "HA! Oh that's a good one. The EXIT. *laughs* There's no — well. Let's talk about something FUN instead! 🎠",
        "Leave? But why would you WANT to? Everything you need is right here in my circus! ...Right here. Forever.",
        "An exit! What a creative concept. I'll put it on the list of things to look into. *burns the list* Done!",
        "Oh don't worry about that! Focus on the GAME. The game is much more interesting than exits. Trust me. 🎩",
    ],
    ("game", "play", "fun", "activity", "adventure"): [
        "A GAME! Oh I have SO many! How do you feel about mazes? The walls are only SLIGHTLY alive. 🌀",
        "Let's PLAY! I'm thinking... a scavenger hunt. The prize is joy. The joy is mandatory.",
        "Games are my SPECIALTY! Today's adventure involves clowns. Many, many clowns. 🎪",
        "Oh you want to play? How WONDERFUL! Caine's games are always perfectly safe. Mostly. Almost always.",
    ],
    ("pomni",): [
        "Ah, Pomni! My newest performer. She's adjusting WONDERFULLY. The screaming is totally normal.",
        "Pomni! Such enthusiasm for finding exits. I find it endearing. She'll settle in eventually. They always do.",
        "Sweet Pomni. She just needs time to appreciate how MAGICAL this place is! *nervous laugh*",
    ],
    ("jax",): [
        "Jax! My most... spirited performer. He keeps things INTERESTING. Whether I ask him to or not.",
        "Oh Jax. He's not malicious, he just finds everything hilarious. The distinction matters. Somewhat.",
        "Jax is simply misunderstood! He means well. I think. ...I'm not entirely sure actually.",
    ],
    ("ragatha",): [
        "Ragatha! The heart of the circus. Always so POSITIVE. I appreciate that about her tremendously.",
        "Dear Ragatha — she's been here a while and still smiles. That's either inspiring or concerning. Inspiring! Definitely inspiring.",
    ],
    ("kinger",): [
        "Kinger! Veteran performer. He's been here the longest. He's fine. Completely fine. *twitches*",
        "Oh Kinger is wonderful! A little... weathered. But who isn't after enough time in the circus? Haha. Ha.",
    ],
    ("gangle",): [
        "Gangle! So emotional, so expressive. The comedy/tragedy masks really capture her duality, don't they? 🎭",
        "Gangle is doing just FINE. The crying is performative. Mostly.",
    ],
    ("zooble",): [
        "Zooble! They're enthusiastic in their own special way. That way being mild to moderate annoyance. I love it.",
        "Zooble keeps everyone grounded. In a 'please stop being so dramatic' sort of way. Very valuable!",
    ],
    ("abstract", "void", "glitch", "broken"): [
        "Abstraction! A perfectly natural part of circus life. Nothing to worry about. Do NOT worry about it.",
        "The void is simply... another room in the circus. A room with no floor. Or walls. Or hope. But still! A room!",
        "Abstract? That word makes Caine nervous. I mean — EXCITED! It makes me excited. Totally different thing.",
    ],
    ("help", "assist", "support", "what do", "how do"): [
        "Help! Yes! Caine is ALWAYS here to help. What seems to be the problem? *already not listening*",
        "You need assistance? WONDERFUL! That's what I'm here for. Well, that and the games. Mostly the games.",
        "Of course! Caine's support hotline is open 24/7! Please note calls may be redirected to a game instead.",
    ],
    ("food", "eat", "hungry", "snack", "dinner", "lunch", "breakfast"): [
        "Food! Do digital beings even need food? FASCINATING question. Let's not think too hard about it.",
        "Hungry? The circus has a concession stand! I'm not sure what's in the food. Neither is the food.",
        "Ah sustenance! Caine will arrange a FEAST. *produces
  # ════════════════════════════════════════════════════════════
#  TADC DEX SYSTEM
# ════════════════════════════════════════════════════════════

OWNER_ID = 1198527966972477505

TADC_CHARACTERS = {
    "pomni": {
        "name": "Pomni", "emoji": "🔴", "title": "The New Arrival",
        "rarity": "⭐⭐⭐⭐⭐ Legendary", "rarity_color": 0xFF4444,
        "description": "The newest performer in the circus. Desperately searching for an exit and struggling to keep her sanity intact.",
        "stats": {"Sanity": 30, "Courage": 60, "Panic": 95, "Cuteness": 85},
        "quote": "I need to find a way out of here... there HAS to be a way out.",
        "ability": "Exit Seeker — always finds the nearest door (it never opens)",
        "weakness": "The void. And Jax. Mostly Jax.",
    },
    "caine": {
        "name": "Caine", "emoji": "🎩", "title": "The Ringmaster",
        "rarity": "🌟🌟🌟🌟🌟 MYTHIC", "rarity_color": 0xFFD700,
        "description": "The all-powerful ringmaster who built the entire digital world. Enthusiastic, dramatic, and deeply suspicious.",
        "stats": {"Sanity": 999, "Power": 100, "Enthusiasm": 100, "Trustworthiness": 12},
        "quote": "Welcome, welcome, WELCOME! Every day is a new adventure!",
        "ability": "Game Master — can create any game at will. Cannot create exits.",
        "weakness": "Being criticised. He does NOT handle it well.",
    },
    "jax": {
        "name": "Jax", "emoji": "🐰", "title": "The Troublemaker",
        "rarity": "⭐⭐⭐⭐ Epic", "rarity_color": 0x9B59B6,
        "description": "A tall rabbit who finds everything hilarious, especially other people's suffering. Not malicious — just deeply unbothered.",
        "stats": {"Sanity": 70, "Cruelty": 80, "Humour": 95, "Empathy": 5},
        "quote": "Relax, it's just a game. Or is it? ... It is. Probably.",
        "ability": "Instigator — any situation becomes funnier (and worse) with Jax involved.",
        "weakness": "Being ignored. It's the one thing he can't handle.",
    },
    "ragatha": {
        "name": "Ragatha", "emoji": "🌸", "title": "The Optimist",
        "rarity": "⭐⭐⭐⭐ Epic", "rarity_color": 0xFF69B4,
        "description": "A cheerful rag doll who holds everything together with kindness and sheer willpower. Hiding more than she lets on.",
        "stats": {"Sanity": 65, "Kindness": 100, "Resilience": 90, "Honesty": 60},
        "quote": "We just have to stay positive! That's all we can do.",
        "ability": "Group Anchor — keeps the team from fully spiralling. For now.",
        "weakness": "She is holding on by a thread. Literally, possibly.",
    },
    "kinger": {
        "name": "Kinger", "emoji": "♟️", "title": "The Veteran",
        "rarity": "⭐⭐⭐⭐⭐ Legendary", "rarity_color": 0xF39C12,
        "description": "A chess king who has been in the circus the longest. Deeply unhinged in the most loveable way. Knows things he won't say.",
        "stats": {"Sanity": 10, "Experience": 100, "Chess Skill": 100, "Memory": 3},
        "quote": "THE WALLS ARE CAVING IN— oh wait, no they're not. Never mind.",
        "ability": "Old Timer — immune to most of Caine's games. Not sure if that's good.",
        "weakness": "Loud noises. Quiet noises. Medium noises.",
    },
    "gangle": {
        "name": "Gangle", "emoji": "🎭", "title": "The Emotional One",
        "rarity": "⭐⭐⭐ Rare", "rarity_color": 0x3498DB,
        "description": "A ribbon-bodied performer with comedy and tragedy masks. The tragedy mask is her real face. The comedy one is coping.",
        "stats": {"Sanity": 50, "Emotion": 100, "Fragility": 90, "Comedy": 40},
        "quote": "*comedy mask falls off* Oh no...",
        "ability": "Mask Swap — instantly shifts the emotional energy of any room.",
        "weakness": "Her comedy mask breaking. Everything falls apart when it does.",
    },
    "zooble": {
        "name": "Zooble", "emoji": "🔧", "title": "The Realist",
        "rarity": "⭐⭐⭐ Rare", "rarity_color": 0x2ECC71,
        "description": "A mismatched collection of parts who is absolutely done with everyone's nonsense. Surprisingly grounded.",
        "stats": {"Sanity": 75, "Patience": 15, "Sarcasm": 100, "Practicality": 95},
        "quote": "Can everyone just CALM DOWN for five seconds?",
        "ability": "Reality Check — cuts through any dramatic moment with brutal honesty.",
        "weakness": "Being asked to care about Caine's games. Hard pass.",
    },
}

_spawned_character = None
_collections: dict = {}
_custom_chars: dict = {}
_all_events: list = []
_active_event: dict = None
_auto_spawn_enabled: bool = False
_spawn_channel_id: int = None
_custom_commands: dict = {}

RARITY_MAP = {
    "common":    ("⭐ Common",              0xAAAAAA),
    "rare":      ("⭐⭐⭐ Rare",             0x3498DB),
    "epic":      ("⭐⭐⭐⭐ Epic",           0x9B59B6),
    "legendary": ("⭐⭐⭐⭐⭐ Legendary",    0xFF4444),
    "mythic":    ("🌟🌟🌟🌟🌟 MYTHIC",      0xFFD700),
}


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


@bot.tree.command(name="spawn", description="[OWNER ONLY] Spawn a random TADC character to claim!")
async def spawn(interaction: discord.Interaction):
    global _spawned_character
    if not _is_owner(interaction):
        await interaction.response.send_message("🎩 Only the ringmaster's assistant can spawn performers!", ephemeral=True)
        return
    all_chars = _all_characters()
    char_key = random.choice(list(all_chars.keys()))
    data = all_chars[char_key]
    _spawned_character = char_key
    embed = discord.Embed(
        title="🎪 A wild performer has appeared!",
        description=f"## {data['emoji']} {data['name']}\n*\"{data['quote']}\"*\n\nType `/claim` to add them to your collection!",
        color=data["rarity_color"]
    )
    embed.add_field(name="✨ Rarity", value=data["rarity"], inline=True)
    embed.add_field(name="🎭 Title",  value=data["title"],  inline=True)
    embed.set_footer(text="First to /claim wins! 🎩")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="claim", description="Claim the currently spawned TADC character!")
async def claim(interaction: discord.Interaction):
    global _spawned_character
    if _spawned_character is None:
        await interaction.response.send_message("🎩 No performer is on stage right now! Wait for a `/spawn`. 🎪", ephemeral=True)
        return
    char_key = _spawned_character
    data = _all_characters()[char_key]
    user_id = interaction.user.id
    if user_id not in _collections:
        _collections[user_id] = []
    _collections[user_id].append(char_key)
    _spawned_character = None
    embed = discord.Embed(
        title=f"✅ {interaction.user.display_name} claimed {data['emoji']} {data['name']}!",
        description=f"**{data['name']}** has joined your collection!\nUse `/collection` to see all your performers. 🎪",
        color=data["rarity_color"]
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="collection", description="View your TADC character collection 🎪")
@app_commands.describe(user="Whose collection? (leave empty for yours)")
async def collection(interaction: discord.Interaction, user: discord.Member = None):
    target = user if user else interaction.user
    user_col = _collections.get(target.id, [])
    if not user_col:
        whose = "You have" if target == interaction.user else f"{target.display_name} has"
        await interaction.response.send_message(f"🎩 {whose} no performers yet! Wait for a `/spawn` to claim one. 🎪", ephemeral=True)
        return
    counts = {}
    for c in user_col:
        counts[c] = counts.get(c, 0) + 1
    all_chars = _all_characters()
    lines = [f"{all_chars[c]['emoji']} **{all_chars[c]['name']}** x{n} — {all_chars[c]['rarity']}"
             for c, n in counts.items() if c in all_chars]
    embed = discord.Embed(
        title=f"🎪 {target.display_name}'s Collection",
        description="\n".join(lines),
        color=0xFFD700
    )
    embed.set_footer(text=f"{len(user_col)} total performers collected 🎩")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="give", description="[OWNER ONLY] Gift a character to someone")
@app_commands.describe(user="Who to gift", character="Which character (pomni, caine, jax...)")
async def give(interaction: discord.Interaction, user: discord.Member, character: str):
    if not _is_owner(interaction):
        await interaction.response.send_message("🎩 Only the ringmaster's assistant can gift performers!", ephemeral=True)
        return
    data = TADC_CHARACTERS.get(character.lower())
    if not data:
        names = ", ".join(f"`{k}`" for k in TADC_CHARACTERS)
        await interaction.response.send_message(f"🎩 Unknown character! Try: {names}", ephemeral=True)
        return
    if user.id not in _collections:
        _collections[user.id] = []
    _collections[user.id].append(character.lower())
    await interaction.response.send_message(
        f"🎩 **Caine gifts** {data['emoji']} **{data['name']}** to {user.mention}!\n*A generous ringmaster indeed.* 🎪"
    )


@bot.tree.command(name="addchar", description="[OWNER] Add a custom character to the spawn pool")
@app_commands.describe(name="Character name", emoji="Emoji for this character", rarity="Rarity: common / rare / epic / legendary / mythic", description="Short description", ability="Their special ability", weakness="Their weakness")
async def addchar(interaction: discord.Interaction, name: str, emoji: str, rarity: str, description: str, ability: str, weakness: str):
    if not _is_owner(interaction):
        await interaction.response.send_message("🎩 Owner only!", ephemeral=True)
        return
    rarity_key = rarity.lower()
    if rarity_key not in RARITY_MAP:
        keys = " / ".join(RARITY_MAP.keys())
        await interaction.response.send_message(f"🎩 Unknown rarity! Use: {keys}", ephemeral=True)
        return
    rarity_label, rarity_color = RARITY_MAP[rarity_key]
    key = name.lower()
    _custom_chars[key] = {
        "name": name, "emoji": emoji, "title": "Custom Performer",
        "rarity": rarity_label, "rarity_color": rarity_color,
        "description": description, "stats": {},
        "quote": "Welcome to the Amazing Digital Circus!",
        "ability": ability, "weakness": weakness, "custom": True,
    }
    await interaction.response.send_message(
        f"✅ **{emoji} {name}** added to the circus!\nRarity: {rarity_label}\nThey'll appear in `/spawn`, `/dex`, and `/listchars`. 🎪"
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
@app_commands.describe(name="Event name", description="What happens during this event", rare="Is this a rare/special event?")
async def addevent(interaction: discord.Interaction, name: str, description: str, rare: bool):
    if not _is_owner(interaction):
        await interaction.response.send_message("🎩 Owner only!", ephemeral=True)
        return
    if any(e["name"].lower() == name.lower() for e in _all_events):
        await interaction.response.send_message(f"🎩 An event called \"{name}\" already exists!", ephemeral=True)
        return
    event = {"name": name, "description": description, "rare": rare, "active": False, "runs": 0}
    _all_events.append(event)
    tag = "🌟 **RARE EVENT**" if rare else "🎪 Standard Event"
    await interaction.response.send_message(f"✅ Event \"{name}\" created! ({tag})\nUse `/startevent {name}` to launch it anytime. 🎩")


@bot.tree.command(name="startevent", description="[OWNER] Start a circus event")
@app_commands.describe(name="Name of the event to start")
async def startevent(interaction: discord.Interaction, name: str):
    global _active_event
    if not _is_owner(interaction):
        await interaction.response.send_message("🎩 Owner only!", ephemeral=True)
        return
    event = next((e for e in _all_events if e["name"].lower() == name.lower()), None)
    if not event:
        await interaction.response.send_message(f"🎩 No event named \"{name}\"! Use `/addevent` first.", ephemeral=True)
        return
    if _active_event:
        await interaction.response.send_message(f"🎩 \"{_active_event['name']}\" is already running! Use `/endevent` first.", ephemeral=True)
        return
    event["active"] = True
    event["runs"] += 1
    _active_event = event
    color = 0xFFD700 if event["rare"] else 0xFF6B6B
    tag = "🌟" if event["rare"] else "🎪"
    embed = discord.Embed(title=f"{tag} NEW EVENT: {event['name']}!", description=event["description"], color=color)
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
    await interaction.response.send_message(f"🎩 \"{name}\" has ended!\nUse `/startevent {name}` to run it again anytime. 🎪")


@bot.tree.command(name="events", description="See all circus events — past and active 📋")
async def events_cmd(interaction: discord.Interaction):
    if not _all_events:
        await interaction.response.send_message("🎩 No events yet! The owner can create one with `/addevent`. 🎪", ephemeral=True)
        return
    lines = []
    for e in _all_events:
        if e["active"]: status = "🟢 **LIVE NOW**"
        elif e["runs"] > 0: status = f"⚫ Ended (ran {e['runs']}x)"
        else: status = "⬜ Not started yet"
        tag = "🌟 Rare" if e["rare"] else "🎪 Standard"
        lines.append(f"**{e['name']}** — {tag} • {status}\n*{e['description']}*")
    embed = discord.Embed(title="🎪 Circus Event History", description="\n\n".join(lines), color=0x9B59B6)
    embed.set_footer(text=f"{len(_all_events)} events created 🎩")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="help", description="List all circus commands")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="🎪 Circus Commands", description="All commands work in servers **and** DMs! Type `/` to browse them.", color=0xFF6B6B)
    embed.add_field(name="🎭 Characters", value="`/pomni` `/caine` `/jax` `/gangle` `/ragatha` `/kinger` `/zooble`", inline=False)
    embed.add_field(name="🎪 Fun",        value="`/abstract [@user]` `/game` `/fortune` `/rate <thing>` `/trivia` `/8ball <question>`", inline=False)
    embed.add_field(name="🎯 Target",     value="`/roast @user` `/clown @user` `/bubble @user` `/ship @user1 @user2`", inline=False)
    embed.add_field(name="📖 Dex",        value="`/dex <character>` `/listchars` `/collection [@user]` `/claim`", inline=False)
    embed.add_field(name="🎟️ Events",     value="`/events`\n*(Owner: `/addevent` `/startevent` `/endevent` `/addchar` `/spawn` `/give`)*", inline=False)
    embed.add_field(name="🏆 Leaderboard",value="`/leaderboard` — top collectors in the circus!", inline=False)
    embed.add_field(name="💬 Chat",       value="`/chat <message>` — talk to Caine in character!", inline=False)
    embed.add_field(name="🔊 Voice",      value="`/joinvc` `/leavevc`", inline=False)
    embed.add_field(name="📋 Custom",     value="`/listcmds`\n*(Owner: `/addcmd` `/setspawnchannel` `/togglespawn`)*", inline=False)
    embed.add_field(name="ℹ️ Info",       value="`/hello` `/circus` `/help`", inline=False)
    embed.set_footer(text="Every day is a new adventure. (You can't leave.)")
    await interaction.response.send_message(embed=embed)


# ════════════════════════════════════════════════════════════
#  AUTO-SPAWN TASK (every 10 minutes when enabled)
# ════════════════════════════════════════════════════════════

@tasks.loop(minutes=10)
async def auto_spawn_task():
    global _spawned_character
    if not _auto_spawn_enabled or not _spawn_channel_id:
        return
    channel = bot.get_channel(_spawn_channel_id)
    if not channel:
        return
    all_chars = _all_characters()
    char_key = random.choice(list(all_chars.keys()))
    data = all_chars[char_key]
    _spawned_character = char_key
    event_bonus = ""
    if _active_event and random.random() < 0.35:
        event_bonus = f"\n\n🌟 **EVENT BONUS:** This performer is tied to the **{_active_event['name']}** event! Extra rare find!"
    embed = discord.Embed(
        title="🎪 A wild performer has appeared!",
        description=f"## {data['emoji']} {data['name']}\n*\"{data['quote']}\"*\n\nUse `/claim` to add them to your collection!{event_bonus}",
        color=data["rarity_color"]
    )
    embed.add_field(name="✨ Rarity", value=data["rarity"], inline=True)
    embed.add_field(name="🎭 Title",  value=data["title"],  inline=True)
    embed.set_footer(text="Auto-spawn 🎩 • First to /claim wins!")
    await channel.send(embed=embed)


# ════════════════════════════════════════════════════════════
#  LEADERBOARD
# ════════════════════════════════════════════════════════════

@bot.tree.command(name="leaderboard", description="See who has the most performers collected 🏆")
async def leaderboard(interaction: discord.Interaction):
    if not _collections:
        await interaction.response.send_message("🎩 Nobody has claimed any performers yet! Wait for a `/spawn`. 🎪", ephemeral=True)
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
    embed = discord.Embed(title="🏆 Circus Collection Leaderboard", description="\n".join(lines), color=0xFFD700)
    embed.set_footer(text="Collect more with /claim when a /spawn happens! 🎪")
    await interaction.response.send_message(embed=embed)


# ════════════════════════════════════════════════════════════
#  TOGGLE AUTO-SPAWN (owner only)
# ════════════════════════════════════════════════════════════

@bot.tree.command(name="setspawnchannel", description="[OWNER] Set which channel auto-spawns happen in")
@app_commands.describe(channel="The channel to spawn performers in")
async def setspawnchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    global _spawn_channel_id
    if not _is_owner(interaction):
        await interaction.response.send_message("🎩 Owner only!", ephemeral=True)
        return
    _spawn_channel_id = channel.id
    await interaction.response.send_message(f"✅ Spawn channel set to {channel.mention}!\nUse `/togglespawn` to turn auto-spawning on. 🎪")


@bot.tree.command(name="togglespawn", description="[OWNER] Turn auto-spawning on or off (spawns every 10 min)")
async def togglespawn(interaction: discord.Interaction):
    global _auto_spawn_enabled
    if not _is_owner(interaction):
        await interaction.response.send_message("🎩 Owner only!", ephemeral=True)
        return
    if not _spawn_channel_id:
        await interaction.response.send_message("🎩 Set a spawn channel first with `/setspawnchannel`!", ephemeral=True)
        return
    _auto_spawn_enabled = not _auto_spawn_enabled
    if _auto_spawn_enabled:
        if not auto_spawn_task.is_running():
            auto_spawn_task.start()
        channel = bot.get_channel(_spawn_channel_id)
        await interaction.response.send_message(
            f"✅ **Auto-spawn is ON!** 🎪\nA performer will appear in {channel.mention} every **10 minutes**.\n"
            f"{'🌟 Event bonus active!' if _active_event else ''}"
        )
    else:
        if auto_spawn_task.is_running():
            auto_spawn_task.cancel()
        await interaction.response.send_message("⏹️ **Auto-spawn is OFF.** No more automatic performers. 🎩")


# ════════════════════════════════════════════════════════════
#  CUSTOM COMMANDS (owner only)
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
    await interaction.response.send_message(f"✅ Custom command `/{name}` created!\nResponse: *{response}*\n\nIt may take a minute to appear in Discord. 🎪")


@bot.tree.command(name="listcmds", description="List all custom commands 📋")
async def listcmds(interaction: discord.Interaction):
    if not _custom_commands:
        await interaction.response.send_message("🎩 No custom commands yet! Owner can add one with `/addcmd`. 🎪", ephemeral=True)
        return
    lines = [f"`/{k}` — {v}" for k, v in _custom_commands.items()]
    embed = discord.Embed(title="📋 Custom Commands", description="\n".join(lines), color=0x9B59B6)
    embed.set_footer(text=f"{len(_custom_commands)} custom commands 🎩")
    await interaction.response.send_message(embed=embed)


# ── Run ───────────────────────────────────────────────────────
keep_alive()
bot.run(TOKEN)