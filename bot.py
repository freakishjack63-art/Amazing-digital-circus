import os
import json
import random
import discord
from datetime import datetime
from discord import app_commands
from discord.ext import commands, tasks
from keep_alive import keep_alive

CUSTOM_CHAR_IMAGE = "https://raw.githubusercontent.com/freakishjack63-art/Amazing-digital-circus/main/images/unknown.png"
COLLECTION_PER_PAGE = 5

def generate_char_id() -> str:
    return ''.join(random.choices('0123456789ABCDEF', k=7))

def _parse_entry(entry, idx: int = 0) -> dict:
    if isinstance(entry, str):
        return {"key": entry, "id": f"OLD{idx:04X}", "atk_bonus": 0, "hp_bonus": 0, "caught": "Unknown", "event": None}
    return entry

CUSTOM_CHARS_FILE = "custom_chars.json"
DATA_FILE          = "data.json"

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

def _save_data():
    """Persist all mutable bot state (collections, admins, events, stats…) to data.json."""
    try:
        payload = {
            "collections":        {str(k): v for k, v in _collections.items()},
            "admins":             list(_admins),
            "blacklisted":        list(_blacklisted),
            "user_stats":         {str(k): v for k, v in _user_stats.items()},
            "all_events":         _all_events,
            "spawn_channel_id":   _spawn_channel_id,
            "auto_spawn_enabled": _auto_spawn_enabled,
        }
        with open(DATA_FILE, "w") as f:
            json.dump(payload, f, indent=2)
    except Exception as e:
        print(f"[WARN] Could not save data: {e}")

def _load_data():
    """Restore mutable bot state from data.json on startup."""
    global _collections, _admins, _blacklisted, _user_stats, _all_events, _spawn_channel_id, _auto_spawn_enabled
    try:
        with open(DATA_FILE, "r") as f:
            d = json.load(f)
        _collections      = {int(k): v for k, v in d.get("collections", {}).items()}
        _admins           = set(d.get("admins", []))
        _blacklisted      = set(d.get("blacklisted", []))
        _user_stats       = {int(k): v for k, v in d.get("user_stats", {}).items()}
        _all_events       = d.get("all_events", [])
        _spawn_channel_id = d.get("spawn_channel_id")
        _auto_spawn_enabled = d.get("auto_spawn_enabled", False)
        print(f"[INFO] Loaded data.json — {len(_collections)} collectors, "
              f"{len(_admins)} admins, {len(_all_events)} events, "
              f"auto-spawn={'ON' if _auto_spawn_enabled else 'OFF'}.")
    except FileNotFoundError:
        print("[INFO] No data.json found — starting fresh.")
    except Exception as e:
        print(f"[WARN] Could not load data: {e}")

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
    _load_data()
    # Resume auto-spawn task if it was running before restart
    if _auto_spawn_enabled and _spawn_channel_id:
        if not auto_spawn_task.is_running():
            auto_spawn_task.start()
        print(f"[INFO] Auto-spawn resumed (channel {_spawn_channel_id}).")
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


_GAME_LOCATIONS = {
    "carousel": {
        "emoji": "🎠", "label": "The Carousel",
        "events": [
            ("You hop on and it starts spinning. And spinning. *And spinning.*\nKinger waves from the centre. He's been there for hours.", "🌀 **Dizzy Souvenir** — a ticket stub that won't stop rotating"),
            ("Ragatha is here, keeping the little ones calm. She smiles. It almost reaches her eyes.", "🌸 **Warm Feeling** — it fades quickly, but it was nice"),
            ("You find a shiny lever. You pull it. The carousel goes *faster.*\nCaine applauds from somewhere unseen.", "⚙️ **Mystery Lever** — definitely shouldn't have pulled it"),
            ("Something falls out of a pocket mid-spin: a crumpled note that reads *'they can hear you think.'*\nYou put it back.", "📝 **Ominous Note** — you chose not to read the rest"),
        ],
    },
    "funhouse": {
        "emoji": "🏰", "label": "The Funhouse",
        "events": [
            ("Jax is here. He rearranges the mirrors so every reflection is slightly wrong.\n'You're welcome,' he says, and leaves.", "🪞 **Warped Mirror Shard** — your reflection winks first"),
            ("You solve a puzzle box! Inside is another puzzle box.\nInside *that* one is a tiny scroll that says *'gotcha.'*", "🧩 **Puzzle Box** — infinite recursion, finite patience"),
            ("A room full of doors. One leads out. You spend 45 minutes picking.\nYou choose the correct one! ...It leads to more doors.", "🚪 **False Exit Token** — Caine had it framed"),
            ("You find Gangle crying at a mirror because her comedy mask fell off.\nYou pick it up. She hugs you. It feels real.", "🎭 **Comedy Mask Fragment** — warm to the touch"),
        ],
    },
    "void": {
        "emoji": "🌀", "label": "The Void Corridor",
        "events": [
            ("You walk in. The corridor has no end.\nPomni is already here, pacing.\n'How long have you been here?' 'I don't know.' Neither do you.", "🔦 **Pomni's Flashlight** — borrowed indefinitely"),
            ("Something in the void hands you a glowing orb.\nYou ask what it does. It dissolves. Classic void.", "🔮 **Dissolved Orb Residue** — smells like static"),
            ("You find a door labelled EXIT. You grab the handle.\nIt says *'just kidding'* and vanishes.\nCaine's laughter echoes from nowhere.", "🚪 **Exit Handle** — doesn't open anything. Still yours."),
            ("The void is completely silent.\nThen Kinger runs past screaming about chess.\nThe silence returns. You feel better, somehow.", "♟️ **Kinger's Spare Pawn** — he dropped it running"),
        ],
    },
    "stage": {
        "emoji": "🎭", "label": "The Stage",
        "events": [
            ("Caine is rehearsing a play. He casts you as the lead.\nYou have no lines. He says that's the *point.*\nThe audience applauds. You didn't see them arrive.", "📜 **Mystery Script** — entirely blank"),
            ("You perform a number nobody asked for.\nCaine gives you a standing ovation for 4 minutes.\n'BRAVO! ...Now do it again but sadder.'", "🌟 **Golden Star Sticker** — Caine insists it's prestigious"),
            ("Zooble is stagehanding and deeply unhappy about it.\nYou help move a backdrop. They say 'thanks' like it physically hurt them.", "🔧 **Zooble's Spare Bolt** — they'll want that back"),
            ("The curtains rise on an empty stage.\nYou stand there for a moment.\nSomewhere, someone is crying. Could be Gangle. Could be you.", "🎪 **Empty Stage Pass** — admits one, to nowhere"),
        ],
    },
}

_GAME_EXTRA = {
    "search": [
        ("You dig under the bleachers and find Kinger's lost chess piece. He's been looking for it for *years.*\nYou hand it back. He cries. Good tears, you think.", "♟️ **Recovered Chess Piece** — Kinger's gratitude is priceless"),
        ("You find a vending machine labelled 'DIGITAL SNACKS'.\nEverything inside is labelled 'EXISTENTIAL CRISIS FLAVOR.'\nYou get one anyway.", "🍬 **Existential Crisis Candy** — tastes like nothing, means everything"),
        ("Behind a tent you find a small door. It opens onto a brick wall.\nA note is taped to the bricks: *'Nice try. — C'*", "📮 **Caine's Rejection Note** — hand-signed. Framed-worthy."),
        ("You search your own pockets. You find a coin with Caine's face on both sides.\nYou didn't have pockets when you arrived.", "🪙 **Trick Coin** — Caine's face, both sides. Always."),
    ],
    "caine": [
        ("Caine materialises immediately.\n'I KNEW you'd come! I've been waiting! The game is— well, I haven't *designed* it yet but the *ENTHUSIASM* is there!'", "🎩 **Caine's Unfinished Game Manifest** — mostly doodles"),
        ("Caine is surprisingly quiet today.\nHe hands you a small envelope. Inside: a receipt for 'one (1) digital existence.'\n'Hold onto that,' he says, and disappears.", "📄 **Existence Receipt** — non-refundable"),
        ("Caine is in the middle of constructing a new tent.\nIt folds into itself when he's done.\n'*Magnificent!*' he says. You nod. You have no idea.", "🏕️ **Blueprint Scrap** — doesn't match any tent you've seen"),
        ("You find Caine staring at a wall.\nHe doesn't notice you for three minutes.\nThen: 'Oh! Hello! How long have YOU been abstract?'\nYou are not abstract. He seems unsure.", "🌀 **Abstract Diagnosis Slip** — probably wrong"),
    ],
}


class GameView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.steps = 0
        self.items: list[str] = []

    def _only_user(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    def _result_embed(self, location: str, event_text: str, item: str) -> discord.Embed:
        self.items.append(item)
        self.steps += 1
        embed = discord.Embed(
            title=f"{location} 🎪",
            description=event_text,
            color=0x9B59B6,
        )
        embed.add_field(name="🎒 Found", value=item, inline=False)
        if self.steps >= 3:
            bag = "\n".join(f"• {i}" for i in self.items)
            embed.add_field(name=f"🎒 Your haul ({len(self.items)} items)", value=bag, inline=False)
            embed.set_footer(text="Adventure complete! Caine is mildly impressed. 🎩")
        else:
            embed.set_footer(text=f"Step {self.steps}/3 — keep exploring! 🎪")
        return embed

    def _disable_all(self):
        for item in self.children:
            item.disabled = True

    async def _pick_location(self, interaction: discord.Interaction, loc_key: str):
        if not self._only_user(interaction):
            await interaction.response.send_message("🎩 This adventure belongs to someone else!", ephemeral=True)
            return
        loc = _GAME_LOCATIONS[loc_key]
        event_text, item = random.choice(loc["events"])
        embed = self._result_embed(f"{loc['emoji']} {loc['label']}", event_text, item)
        if self.steps >= 3:
            self._disable_all()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            view = GameExploreView(self)
            await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🎠 Carousel",        style=discord.ButtonStyle.primary)
    async def go_carousel(self, i, b): await self._pick_location(i, "carousel")

    @discord.ui.button(label="🏰 Funhouse",        style=discord.ButtonStyle.primary)
    async def go_funhouse(self, i, b): await self._pick_location(i, "funhouse")

    @discord.ui.button(label="🌀 Void Corridor",   style=discord.ButtonStyle.danger)
    async def go_void(self, i, b): await self._pick_location(i, "void")

    @discord.ui.button(label="🎭 The Stage",       style=discord.ButtonStyle.secondary)
    async def go_stage(self, i, b): await self._pick_location(i, "stage")

    async def on_timeout(self):
        self._disable_all()


class GameExploreView(discord.ui.View):
    """Shown after visiting a location — offers more exploration options."""
    def __init__(self, state: GameView):
        super().__init__(timeout=120)
        self.state = state

    @discord.ui.button(label="🗺️ Explore more",    style=discord.ButtonStyle.primary)
    async def explore_more(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.state._only_user(interaction):
            await interaction.response.send_message("🎩 Not your adventure!", ephemeral=True)
            return
        self._disable_all()
        view = GameView.__new__(GameView)
        discord.ui.View.__init__(view, timeout=120)
        view.user_id = self.state.user_id
        view.steps   = self.state.steps
        view.items   = self.state.items
        GameView.go_carousel.__set_name__(view, "go_carousel")
        view = GameView(self.state.user_id)
        view.steps = self.state.steps
        view.items = self.state.items
        embed = discord.Embed(
            title="🎪 Where to next?",
            description="*The circus stretches in every direction. Caine watches from above.*",
            color=0xFFD700,
        )
        embed.set_footer(text=f"Step {self.state.steps}/3 complete • Keep exploring! 🎩")
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🔍 Search the area", style=discord.ButtonStyle.secondary)
    async def search_area(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.state._only_user(interaction):
            await interaction.response.send_message("🎩 Not your adventure!", ephemeral=True)
            return
        self._disable_all()
        event_text, item = random.choice(_GAME_EXTRA["search"])
        embed = self.state._result_embed("🔍 Searching...", event_text, item)
        if self.state.steps >= 3:
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            await interaction.response.edit_message(embed=embed, view=GameExploreView(self.state))

    @discord.ui.button(label="🎩 Find Caine",      style=discord.ButtonStyle.success)
    async def find_caine(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.state._only_user(interaction):
            await interaction.response.send_message("🎩 Not your adventure!", ephemeral=True)
            return
        self._disable_all()
        event_text, item = random.choice(_GAME_EXTRA["caine"])
        embed = self.state._result_embed("🎩 Caine Encounter!", event_text, item)
        if self.state.steps >= 3:
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            await interaction.response.edit_message(embed=embed, view=GameExploreView(self.state))

    @discord.ui.button(label="🏠 Return to tent",  style=discord.ButtonStyle.danger)
    async def return_tent(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.state._only_user(interaction):
            await interaction.response.send_message("🎩 Not your adventure!", ephemeral=True)
            return
        self._disable_all()
        bag = ("\n".join(f"• {i}" for i in self.state.items)) if self.state.items else "*You came back empty-handed. Caine is disappointed.*"
        embed = discord.Embed(
            title="🏠 Back in your tent",
            description="You collapse onto a circus cot that's somehow both too soft and deeply unsettling.\nCaine's voice echoes: *'Good adventure! Same time tomorrow!'*",
            color=0x2ECC71,
        )
        embed.add_field(name=f"🎒 Items collected ({len(self.state.items)})", value=bag, inline=False)
        embed.set_footer(text="Adventure over! Use /game again anytime. 🎪")
        await interaction.response.edit_message(embed=embed, view=self)

    def _disable_all(self):
        for item in self.children:
            item.disabled = True

    async def on_timeout(self):
        self._disable_all()


@bot.tree.command(name="game", description="Explore the Amazing Digital Circus! 🎪")
async def game(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎪 Welcome to the Amazing Digital Circus!",
        description=(
            "Caine grins and gestures grandly at the glittering chaos around you.\n\n"
            "*'A new ADVENTURE begins! Every tent, every corridor — full of WONDERS! "
            "And definitely not danger. Mostly not danger.'*\n\n"
            "**Where do you explore first?**"
        ),
        color=0x9B59B6,
    )
    embed.set_footer(text="3 locations to visit • items to find • Caine is watching 🎩")
    await interaction.response.send_message(embed=embed, view=GameView(interaction.user.id))


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


_TRIVIA_QUESTIONS = [
    ("What colour is Pomni's hat?",                      "Red",                  ["Blue", "Red", "Yellow", "Purple"]),
    ("What is Caine's role in the circus?",              "Ringmaster",           ["Clown", "Performer", "Ringmaster", "Janitor"]),
    ("Which character has been in the circus longest?",  "Kinger",               ["Ragatha", "Jax", "Kinger", "Gangle"]),
    ("What happens to performers who lose their minds?", "They go abstract",     ["They disappear", "They go abstract", "They escape", "They become clowns"]),
    ("What does Gangle wear?",                           "Comedy/tragedy masks", ["A top hat", "A jester hat", "Comedy/tragedy masks", "A crown"]),
    ("What game does Kinger love?",                      "Chess",                ["Checkers", "Chess", "Cards", "Mazes"]),
    ("What colour is Jax?",                              "Purple",               ["Blue", "Purple", "Pink", "Red"]),
    ("Who is the newest arrival in the circus?",         "Pomni",                ["Ragatha", "Zooble", "Pomni", "Gangle"]),
    ("What shape is Zooble made of?",                    "Mixed shapes",         ["A circle", "Mixed shapes", "A cube", "A triangle"]),
    ("What does Caine wear on his head?",                "A top hat",            ["A crown", "A top hat", "A bowler hat", "Nothing"]),
    ("What emotion does Gangle's tragedy mask show?",    "Sadness",              ["Anger", "Sadness", "Fear", "Surprise"]),
    ("What does 'abstract' mean in the circus?",         "Going insane",         ["Escaping", "Going insane", "Becoming a clown", "Winning a game"]),
]


class TriviaView(discord.ui.View):
    def __init__(self, question: str, answer: str, options: list[str], asker_id: int):
        super().__init__(timeout=30)
        self.question  = question
        self.answer    = answer
        self.options   = options
        self.asker_id  = asker_id
        self.answered  = False
        for i, opt in enumerate(options, 1):
            btn = discord.ui.Button(label=str(i), style=discord.ButtonStyle.primary)
            btn.callback = self._make_callback(i, opt)
            self.add_item(btn)

    def _make_callback(self, num: int, chosen: str):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.asker_id:
                await interaction.response.send_message("🎩 This trivia is someone else's!", ephemeral=True)
                return
            if self.answered:
                await interaction.response.send_message("🎩 Already answered!", ephemeral=True)
                return
            self.answered = True
            self.stop()
            for item in self.children:
                item.disabled = True
            correct = chosen == self.answer
            opts_text = "\n".join(
                f"{'✅' if o == self.answer else ('❌' if o == chosen and not correct else '▫️')} **{i}.** {o}"
                for i, o in enumerate(self.options, 1)
            )
            if correct:
                result = f"🎉 **Correct!** Caine is impressed.\n\n{opts_text}"
                color  = 0x2ECC71
                footer = "Well done! Even Kinger got that one eventually. 🎩"
            else:
                result = f"❌ **Wrong!** The correct answer was **{self.answer}**.\n\n{opts_text}"
                color  = 0xFF4444
                footer = "The circus judges harshly. Try again with /trivia! 🎪"
            embed = discord.Embed(
                title="🎪 TADC Trivia — Result!",
                description=f"**{self.question}**\n\n{result}",
                color=color,
            )
            embed.set_footer(text=footer)
            await interaction.response.edit_message(embed=embed, view=self)
        return callback

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


@bot.tree.command(name="trivia", description="Answer a TADC trivia question 🎪")
async def trivia(interaction: discord.Interaction):
    q, answer, raw_options = random.choice(_TRIVIA_QUESTIONS)
    options = raw_options[:]
    random.shuffle(options)
    opts_text = "\n".join(f"**{i}.** {o}" for i, o in enumerate(options, 1))
    embed = discord.Embed(
        title="🎪 TADC Trivia!",
        description=f"**{q}**\n\n{opts_text}\n\n*Click the number of your answer below!*",
        color=0xFFD700,
    )
    embed.set_footer(text="⏳ 30 seconds to answer! 🎩")
    await interaction.response.send_message(embed=embed, view=TriviaView(q, answer, options, interaction.user.id))


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
        "image_url": "https://raw.githubusercontent.com/freakishjack63-art/Amazing-digital-circus/main/images/pomni.jpeg",
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
        "image_url": "https://raw.githubusercontent.com/freakishjack63-art/Amazing-digital-circus/main/images/caine.webp",
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
        "image_url": "https://raw.githubusercontent.com/freakishjack63-art/Amazing-digital-circus/main/images/jax.jpeg",
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
        "image_url": "https://raw.githubusercontent.com/freakishjack63-art/Amazing-digital-circus/main/images/ragatha.webp",
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
        "image_url": "https://raw.githubusercontent.com/freakishjack63-art/Amazing-digital-circus/main/images/kinger.webp",
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
        "image_url": "https://raw.githubusercontent.com/freakishjack63-art/Amazing-digital-circus/main/images/gangle.jpeg",
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
        "image_url": "https://raw.githubusercontent.com/freakishjack63-art/Amazing-digital-circus/main/images/zooble.jpeg",
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
_admins: set = set()
_blacklisted: set = set()
_user_stats: dict = {}   # uid -> {"strength": str, "weakness": str}

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

    @discord.ui.button(label="Catch me", style=discord.ButtonStyle.secondary)
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
        already_had = uid in _collections and any(
            _parse_entry(e, i).get("key") == char_key
            for i, e in enumerate(_collections[uid])
        )
        if uid not in _collections:
            _collections[uid] = []
        _collections[uid].append(entry)
        _save_data()
        atk_str = f"{atk_bonus:+}%"
        hp_str  = f"{hp_bonus:+}%"
        await interaction.response.edit_message(view=self)
        if already_had:
            status_line = f"Added to your collection again! *(you already have a {char_data['name']})*"
        else:
            status_line = f"🎉 **New character added to your collection!**"
        if _active_event:
            msg = (
                f"{interaction.user.mention}, **{char_data['name']}** secured! "
                f"(`#{char_id}` {atk_str}/{hp_str})\n"
                f"{status_line}\n"
                f"🌟 *{_active_event['description']}*"
            )
        else:
            msg = (
                f"{interaction.user.mention}, **{char_data['name']}** secured! "
                f"(`#{char_id}` {atk_str}/{hp_str})\n"
                f"{status_line}"
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

def _is_admin(interaction: discord.Interaction) -> bool:
    return interaction.user.id == OWNER_ID or interaction.user.id in _admins

@bot.tree.interaction_check
async def global_blacklist_check(interaction: discord.Interaction) -> bool:
    if interaction.user.id in _blacklisted:
        await interaction.response.send_message(
            "🎩 You've been removed from the circus by the ringmaster. 🚫", ephemeral=True
        )
        return False
    return True


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


def _build_spawn_embed(data: dict) -> discord.Embed:
    """Ballsdex-style spawn embed — just the character image, nothing else."""
    image_url = data.get("image_url") or CUSTOM_CHAR_IMAGE
    embed = discord.Embed(color=data.get("rarity_color", 0xFFD700))
    embed.set_image(url=image_url)
    return embed


async def _do_auto_spawn():
    """Pick a random character and post a spawn message in the configured channel."""
    if not _spawn_channel_id:
        return
    channel = bot.get_channel(_spawn_channel_id)
    if not channel:
        return
    all_chars = _all_characters()
    if not all_chars:
        return
    char_key = random.choice(list(all_chars.keys()))
    data = all_chars[char_key]
    embed = _build_spawn_embed(data)
    view = CatchView([char_key], {char_key: data})
    await channel.send(
        content=f"A wild **{data['emoji']} {data['name']}** appeared!",
        embed=embed,
        view=view,
    )


@tasks.loop(minutes=10)
async def auto_spawn_task():
    if _auto_spawn_enabled:
        await _do_auto_spawn()


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
    embed = _build_spawn_embed(data)
    view = CatchView(pool, char_data_map)
    if amount == 1:
        content = f"A wild **{data['emoji']} {data['name']}** appeared!"
    else:
        unique: dict = {}
        for k in pool:
            unique[k] = unique.get(k, 0) + 1
        parts = ", ".join(
            f"{all_chars[k]['emoji']} **{all_chars[k]['name']}** ×{n}" for k, n in unique.items()
        )
        content = f"✨ **{amount} performers appeared!** — {parts}\n*{amount} catches available — be quick!*"
    await interaction.response.send_message(content=content, embed=embed, view=view)


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
    _save_data()
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
    _save_data()
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
    _save_data()
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
    _save_data()
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

def _col_has_key(col: list, key: str) -> bool:
    """Check if a collection (list of dicts) contains an entry with the given character key."""
    return any(_parse_entry(e, i).get("key") == key for i, e in enumerate(col))

def _col_pop_key(col: list, key: str) -> dict | None:
    """Remove and return the first entry matching key, or None if not found."""
    for i, e in enumerate(col):
        entry = _parse_entry(e, i)
        if entry.get("key") == key:
            col.pop(i)
            return entry
    return None


class TradeView(discord.ui.View):
    def __init__(self, initiator: discord.Member, target: discord.Member,
                 offer_entry: dict, want_key: str, offer_data: dict, want_data: dict):
        super().__init__(timeout=120)
        self.initiator_id  = initiator.id
        self.target_id     = target.id
        self.offer_entry   = offer_entry   # full dict that will physically move
        self.want_key      = want_key
        self.offer_data    = offer_data
        self.want_data     = want_data
        self.completed     = False

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
        target_col    = _collections.get(self.target_id,    [])
        # Re-verify the offered entry still exists (initiator may have traded it away)
        offer_key     = self.offer_entry.get("key", "")
        if not _col_has_key(initiator_col, offer_key):
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
        want_entry = _col_pop_key(target_col, self.want_key)
        if want_entry is None:
            await interaction.response.send_message(
                f"🎩 You don't have {self.want_data['emoji']} **{self.want_data['name']}** in your collection to trade!",
                ephemeral=True
            )
            return
        # Remove offered entry from initiator and hand to target; hand want_entry to initiator
        _col_pop_key(initiator_col, offer_key)
        initiator_col.append(want_entry)
        target_col.append(self.offer_entry)
        self.completed = True
        self.stop()
        for item in self.children:
            item.disabled = True
        _save_data()
        offer_id = self.offer_entry.get("id", "?")
        want_id  = want_entry.get("id", "?")
        success_embed = discord.Embed(
            title="🤝 Trade Complete! The circus approves!",
            description=(
                f"{self.offer_data['emoji']} **{self.offer_data['name']}** `#{offer_id}` ➜ <@{self.target_id}>\n"
                f"{self.want_data['emoji']} **{self.want_data['name']}** `#{want_id}` ➜ <@{self.initiator_id}>"
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
    if not _col_has_key(my_col, offer_key):
        await interaction.response.send_message(
            f"🎩 You don't have {offer_data['emoji']} **{offer_data['name']}** in your collection to offer!", ephemeral=True
        )
        return
    their_col = _collections.get(user.id, [])
    if not _col_has_key(their_col, want_key):
        await interaction.response.send_message(
            f"🎩 {user.display_name} doesn't have {want_data['emoji']} **{want_data['name']}** to trade!", ephemeral=True
        )
        return
    # Grab the actual entry dict that will be moved on accept
    offer_entry = next(
        (_parse_entry(e, i) for i, e in enumerate(my_col) if _parse_entry(e, i).get("key") == offer_key), {}
    )
    view = TradeView(interaction.user, user, offer_entry, want_key, offer_data, want_data)
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
        a_stats = _user_stats.get(self.fighter_a.id, {})
        b_stats = _user_stats.get(self.fighter_b.id, {})
        a_str = a_stats.get("strength", "")
        a_wk  = a_stats.get("weakness", "")
        b_str = b_stats.get("strength", "")
        b_wk  = b_stats.get("weakness", "")
        def _stat_lines(strength, weakness):
            parts = []
            if strength: parts.append(f"💪 *{strength}*")
            if weakness: parts.append(f"💀 *{weakness}*")
            return "\n".join(parts) if parts else "\u200b"
        embed.add_field(
            name=f"{a_data['emoji']} {self.fighter_a.display_name}",
            value=f"`#{a_entry['id']}` **{a_data['name']}**\nATK {a_atk} • HP {a_hp}\n{_stat_lines(a_str, a_wk)}",
            inline=True,
        )
        embed.add_field(name="⚔️ VS", value="\u200b", inline=True)
        embed.add_field(
            name=f"{b_data['emoji']} {self.fighter_b.display_name}",
            value=f"`#{b_entry['id']}` **{b_data['name']}**\nATK {b_atk} • HP {b_hp}\n{_stat_lines(b_str, b_wk)}",
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
#  ADMIN SYSTEM  (owner-only management)
# ════════════════════════════════════════════════════════════

@bot.tree.command(name="addadmin", description="[OWNER] Promote a user to circus admin")
@app_commands.describe(user="User to make an admin")
async def addadmin(interaction: discord.Interaction, user: discord.Member):
    if not _is_owner(interaction):
        await interaction.response.send_message("🎩 Only the ringmaster can appoint admins!", ephemeral=True)
        return
    if user.id == OWNER_ID:
        await interaction.response.send_message("🎩 You're already the ringmaster!", ephemeral=True)
        return
    if user.bot:
        await interaction.response.send_message("🎩 Bots can't be admins!", ephemeral=True)
        return
    _admins.add(user.id)
    _save_data()
    await interaction.response.send_message(
        f"🎩 **{user.display_name}** is now a circus admin! They can use owner-level commands. 🎪"
    )


@bot.tree.command(name="removeadmin", description="[OWNER] Remove a user's admin status")
@app_commands.describe(user="User to demote")
async def removeadmin(interaction: discord.Interaction, user: discord.Member):
    if not _is_owner(interaction):
        await interaction.response.send_message("🎩 Only the ringmaster can demote admins!", ephemeral=True)
        return
    if user.id not in _admins:
        await interaction.response.send_message(f"🎩 **{user.display_name}** isn't an admin!", ephemeral=True)
        return
    _admins.discard(user.id)
    _save_data()
    await interaction.response.send_message(
        f"🎩 **{user.display_name}**'s admin status has been removed. 🎪"
    )


@bot.tree.command(name="listadmins", description="List all current circus admins")
async def listadmins(interaction: discord.Interaction):
    if not _admins:
        await interaction.response.send_message("🎩 No admins yet! Owner can add one with `/addadmin`. 🎪", ephemeral=True)
        return
    lines = []
    for uid in _admins:
        try:
            u = bot.get_user(uid) or await bot.fetch_user(uid)
            lines.append(f"🎩 {u.display_name}")
        except Exception:
            lines.append(f"🎩 `#{uid}`")
    embed = discord.Embed(title="🎪 Circus Admins", description="\n".join(lines), color=0xFFD700)
    embed.set_footer(text="Admins can use boss fights, spawn, and moderation commands.")
    await interaction.response.send_message(embed=embed)


# ════════════════════════════════════════════════════════════
#  BLACKLIST SYSTEM  (owner + admin)
# ════════════════════════════════════════════════════════════

@bot.tree.command(name="blacklist", description="[ADMIN] Ban a user from using the bot")
@app_commands.describe(user="User to blacklist")
async def blacklist_cmd(interaction: discord.Interaction, user: discord.Member):
    if not _is_admin(interaction):
        await interaction.response.send_message("🎩 Admin only!", ephemeral=True)
        return
    if user.id == OWNER_ID or user.id in _admins:
        await interaction.response.send_message("🎩 You can't blacklist an admin or the owner!", ephemeral=True)
        return
    if user.bot:
        await interaction.response.send_message("🎩 Bots aren't circus performers to ban!", ephemeral=True)
        return
    _blacklisted.add(user.id)
    _save_data()
    await interaction.response.send_message(
        f"🚫 **{user.display_name}** has been removed from the circus. They can no longer use bot commands. 🎪"
    )


@bot.tree.command(name="unblacklist", description="[ADMIN] Restore a user's access to the bot")
@app_commands.describe(user="User to unblacklist")
async def unblacklist_cmd(interaction: discord.Interaction, user: discord.Member):
    if not _is_admin(interaction):
        await interaction.response.send_message("🎩 Admin only!", ephemeral=True)
        return
    if user.id not in _blacklisted:
        await interaction.response.send_message(f"🎩 **{user.display_name}** isn't blacklisted!", ephemeral=True)
        return
    _blacklisted.discard(user.id)
    _save_data()
    await interaction.response.send_message(
        f"✅ **{user.display_name}** has been welcomed back to the circus! 🎪"
    )


# ════════════════════════════════════════════════════════════
#  BATTLE STATS  (set personal strength / weakness)
# ════════════════════════════════════════════════════════════

@bot.tree.command(name="setstrength", description="Set your battle strength description (shown in battles!)")
@app_commands.describe(text="Your fighter's strength (e.g. 'Fast attacker', 'Never gives up')")
async def setstrength(interaction: discord.Interaction, text: str):
    if len(text) > 60:
        await interaction.response.send_message("🎩 Keep it under 60 characters!", ephemeral=True)
        return
    if interaction.user.id not in _user_stats:
        _user_stats[interaction.user.id] = {}
    _user_stats[interaction.user.id]["strength"] = text
    _save_data()
    await interaction.response.send_message(
        f"💪 Battle strength set: **{text}**\nThis will now appear when you fight! ⚔️", ephemeral=True
    )


@bot.tree.command(name="setweakness", description="Set your battle weakness description (shown in battles!)")
@app_commands.describe(text="Your fighter's weakness (e.g. 'Slow starter', 'Freezes under pressure')")
async def setweakness(interaction: discord.Interaction, text: str):
    if len(text) > 60:
        await interaction.response.send_message("🎩 Keep it under 60 characters!", ephemeral=True)
        return
    if interaction.user.id not in _user_stats:
        _user_stats[interaction.user.id] = {}
    _user_stats[interaction.user.id]["weakness"] = text
    _save_data()
    await interaction.response.send_message(
        f"💀 Battle weakness set: **{text}**\nThis will now appear when you fight! ⚔️", ephemeral=True
    )


@bot.tree.command(name="mystats", description="View your current battle strength and weakness")
async def mystats(interaction: discord.Interaction):
    stats = _user_stats.get(interaction.user.id, {})
    strength = stats.get("strength", "*Not set — use `/setstrength`*")
    weakness = stats.get("weakness", "*Not set — use `/setweakness`*")
    embed = discord.Embed(
        title=f"⚔️ {interaction.user.display_name}'s Battle Profile",
        color=0x9B59B6,
    )
    embed.add_field(name="💪 Strength", value=strength, inline=False)
    embed.add_field(name="💀 Weakness", value=weakness, inline=False)
    embed.set_footer(text="Stats appear in battle results for everyone to see! 🎪")
    await interaction.response.send_message(embed=embed)


# ════════════════════════════════════════════════════════════
#  BOSS FIGHT SYSTEM  (owner + admin only)
# ════════════════════════════════════════════════════════════

class BossView(discord.ui.View):
    def __init__(self, boss_name: str, boss_emoji: str, max_hp: int, reward_key: str, reward_data: dict):
        super().__init__(timeout=300)
        self.boss_name   = boss_name
        self.boss_emoji  = boss_emoji
        self.max_hp      = max_hp
        self.current_hp  = max_hp
        self.reward_key  = reward_key
        self.reward_data = reward_data
        self.attackers: dict = {}   # uid -> total dmg
        self.defeated    = False

    def _hp_bar(self) -> str:
        ratio  = max(0, self.current_hp / self.max_hp)
        filled = round(ratio * 12)
        return f"{'█' * filled}{'░' * (12 - filled)}  `{self.current_hp:,}/{self.max_hp:,} HP`"

    def _build_embed(self, latest: str = "") -> discord.Embed:
        pct   = self.current_hp / self.max_hp
        color = 0xFF0000 if pct > 0.5 else (0xFF6600 if pct > 0.25 else 0xFFAA00)
        desc  = f"**{self._hp_bar()}**"
        if latest:
            desc += f"\n\n{latest}"
        embed = discord.Embed(
            title=f"⚠️ BOSS FIGHT: {self.boss_emoji} {self.boss_name}!",
            description=desc,
            color=color,
        )
        embed.add_field(
            name="🏆 Reward",
            value=f"{self.reward_data['emoji']} **{self.reward_data['name']}** for all who deal damage!",
            inline=True,
        )
        embed.add_field(name="⚔️ Attackers", value=str(len(self.attackers)), inline=True)
        embed.set_footer(text="Click ⚔️ Attack! to deal damage — everyone who attacks earns a reward! 🎪")
        return embed

    @discord.ui.button(label="⚔️ Attack!", style=discord.ButtonStyle.red, emoji="⚔️")
    async def attack_boss(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.defeated:
            await interaction.response.send_message("🎩 The boss is already defeated!", ephemeral=True)
            return
        uid  = interaction.user.id
        dmg  = random.randint(15, 60)
        self.current_hp            = max(0, self.current_hp - dmg)
        self.attackers[uid]        = self.attackers.get(uid, 0) + dmg
        latest = f"**{interaction.user.display_name}** dealt **{dmg}** damage! 🗡️"
        if self.current_hp <= 0:
            self.defeated = True
            self.stop()
            button.disabled = True
            button.label    = "Defeated! 💀"
            # Give reward to every attacker
            all_chars = _all_characters()
            now       = datetime.now().strftime("%Y/%m/%d | %H:%M")
            winner_lines = []
            for a_id, dmg_dealt in sorted(self.attackers.items(), key=lambda x: x[1], reverse=True):
                entry = {
                    "key":       self.reward_key,
                    "id":        generate_char_id(),
                    "atk_bonus": random.randint(0, 25),   # Boss rewards always positive!
                    "hp_bonus":  random.randint(0, 25),
                    "caught":    now,
                    "event":     "Boss Reward",
                }
                if a_id not in _collections:
                    _collections[a_id] = []
                _collections[a_id].append(entry)
                _save_data()
                try:
                    u    = bot.get_user(a_id) or await bot.fetch_user(a_id)
                    name = u.display_name
                except Exception:
                    name = f"#{a_id}"
                winner_lines.append(f"🏆 **{name}** — {dmg_dealt:,} total dmg")
            top5 = "\n".join(winner_lines[:5])
            if len(winner_lines) > 5:
                top5 += f"\n*…and {len(winner_lines)-5} more!*"
            embed = discord.Embed(
                title=f"💀 {self.boss_emoji} {self.boss_name} has been DEFEATED!",
                description=(
                    f"**{len(self.attackers)} heroes** brought down the boss!\n\n"
                    f"**Top attackers:**\n{top5}\n\n"
                    f"Everyone who attacked received a "
                    f"{self.reward_data['emoji']} **{self.reward_data['name']}**! 🎉"
                ),
                color=0x2ECC71,
            )
            embed.set_footer(text="Check your /collection to see your boss reward! 🎪")
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=self._build_embed(latest), view=self)

    async def on_timeout(self):
        self.attack_boss.disabled = True
        self.attack_boss.label    = "Time's up! ⏰"


@bot.tree.command(name="bossfight", description="[ADMIN] Spawn a boss fight that the whole server can join!")
@app_commands.describe(
    name="Boss name",
    emoji="Boss emoji",
    hp="Boss HP (suggested: 500–5000)",
    reward="Reward character key (e.g. caine, pomni, kinger)",
)
async def bossfight(interaction: discord.Interaction, name: str, emoji: str, hp: int, reward: str):
    if not _is_admin(interaction):
        await interaction.response.send_message("🎩 Only admins can start boss fights!", ephemeral=True)
        return
    all_chars  = _all_characters()
    reward_key = next(
        (k for k, v in all_chars.items() if k == reward.lower() or v["name"].lower() == reward.lower()), None
    )
    if not reward_key:
        names = ", ".join(f"`{v['name']}`" for v in all_chars.values())
        await interaction.response.send_message(f"🎩 Unknown reward character! Try: {names}", ephemeral=True)
        return
    hp = max(100, min(hp, 50000))
    reward_data = all_chars[reward_key]
    view  = BossView(name, emoji, hp, reward_key, reward_data)
    embed = view._build_embed()
    embed.description = (
        f"**{view._hp_bar()}**\n\n"
        f"*The boss has appeared! Everyone attack to earn a "
        f"{reward_data['emoji']} **{reward_data['name']}**!*"
    )
    await interaction.response.send_message(
        content="@everyone ⚠️ A boss has appeared! Attack now!",
        embed=embed,
        view=view,
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
    embed.add_field(name="📖 Dex",        value="`/dex <character>` • `/listchars` • `/collection [@user]`", inline=False)
    embed.add_field(name="⚔️ Battle",     value="`/battle @user` — challenge to a character battle!\n`/setstrength <text>` `/setweakness <text>` `/mystats` — your fighter profile", inline=False)
    embed.add_field(name="💀 Boss Fights", value="`/bossfight` — *Admin only* — spawn a server-wide boss everyone can attack for rewards!", inline=False)
    embed.add_field(name="🤝 Trading",    value="`/trade @user offer:<char> want:<char>` — propose a character trade", inline=False)
    embed.add_field(name="🎟️ Events",     value="`/events` — see all events\n*(Admin: `/addevent` `/startevent` `/endevent`)*", inline=False)
    embed.add_field(name="🎪 Spawning",   value="`/togglespawn` — turn auto-spawning on/off (anyone!)\n*(Admin: `/setspawnchannel` `/spawn` `/give @user char`)*", inline=False)
    embed.add_field(name="🏆 Leaderboard", value="`/leaderboard` — top collectors in the circus!", inline=False)
    embed.add_field(name="💬 Chat",       value="`/chat <message>` — talk to Caine in character!", inline=False)
    embed.add_field(name="🔊 Voice",      value="`/joinvc` `/leavevc`", inline=False)
    embed.add_field(name="🛡️ Admin",      value="*(Owner: `/addadmin` `/removeadmin` `/listadmins`)*\n*(Admin: `/blacklist @user` `/unblacklist @user`)*\n*(Owner: `/addchar` `/addcmd` `/removecmd`)*", inline=False)
    embed.set_footer(text="Every day is a new adventure. (You can't leave.) 🎪")
    await interaction.response.send_message(embed=embed)


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
    _save_data()
    await interaction.response.send_message(
        f"✅ Spawn channel set to {channel.mention}!\nUse `/togglespawn` to turn auto-spawning on. 🎪"
    )


@bot.tree.command(name="togglespawn", description="Turn auto-spawning on or off (anyone can use!)")
async def togglespawn(interaction: discord.Interaction):
    global _auto_spawn_enabled
    if not _spawn_channel_id:
        await interaction.response.send_message(
            "🎩 No spawn channel set yet! An admin must use `/setspawnchannel` first.", ephemeral=True
        )
        return
    _auto_spawn_enabled = not _auto_spawn_enabled
    _save_data()
    if _auto_spawn_enabled:
        if not auto_spawn_task.is_running():
            auto_spawn_task.start()
        channel = bot.get_channel(_spawn_channel_id)
        await interaction.response.send_message(
            f"✅ **Auto-spawn is ON!** 🎪\nA performer appears in {channel.mention} every **10 minutes**.\n"
            f"*Spawning one right now...*"
        )
        await _do_auto_spawn()
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
