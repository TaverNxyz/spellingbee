import asyncio
import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import discord
from redbot.core import commands, Config, checks
from redbot.core.utils.chat_formatting import box, pagify
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
from redbot.core.utils.predicates import MessagePredicate

class SpellingBeeView(discord.ui.View):
    def __init__(self, cog, ctx, word_data: dict, difficulty: str, game_id: str):
        super().__init__(timeout=300)  # 5 minute timeout
        self.cog = cog
        self.ctx = ctx
        self.word_data = word_data
        self.difficulty = difficulty
        self.game_id = game_id
        self.current_word_index = 0
        self.score = 0
        self.hints_used = 0
        self.max_hints = 3
        self.words_correct = 0
        self.words_attempted = 0
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.ctx.author
        
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except:
            pass
            
    @discord.ui.button(label='🔊 Pronounce Word', style=discord.ButtonStyle.primary)
    async def pronounce_word(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_word_index >= len(self.word_data['words']):
            await interaction.response.send_message("Game completed!", ephemeral=True)
            return
            
        current_word = self.word_data['words'][self.current_word_index]
        pronunciation = current_word.get('pronunciation', f"/{current_word['word']}/")
        
        embed = discord.Embed(
            title="🔊 Word Pronunciation",
            description=f"**Pronunciation:** {pronunciation}",
            color=0x3498db
        )
        embed.add_field(name="Instructions", value="Type your spelling in chat!", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @discord.ui.button(label='📖 Definition', style=discord.ButtonStyle.secondary)
    async def get_definition(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_word_index >= len(self.word_data['words']):
            await interaction.response.send_message("Game completed!", ephemeral=True)
            return
            
        current_word = self.word_data['words'][self.current_word_index]
        definition = current_word.get('definition', 'Definition not available')
        
        embed = discord.Embed(
            title="📖 Word Definition",
            description=f"**Definition:** {definition}",
            color=0x9b59b6
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @discord.ui.button(label='💡 Hint', style=discord.ButtonStyle.success)
    async def get_hint(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.hints_used >= self.max_hints:
            await interaction.response.send_message("❌ No more hints available!", ephemeral=True)
            return
            
        if self.current_word_index >= len(self.word_data['words']):
            await interaction.response.send_message("Game completed!", ephemeral=True)
            return
            
        current_word = self.word_data['words'][self.current_word_index]
        word = current_word['word'].lower()
        
        # Generate hint based on hints used
        if self.hints_used == 0:
            hint = f"The word starts with '{word[0].upper()}' and has {len(word)} letters"
        elif self.hints_used == 1:
            hint = f"The word ends with '{word[-1].upper()}'"
        else:
            # Show every other letter
            hint_word = ""
            for i, letter in enumerate(word):
                if i % 2 == 0:
                    hint_word += letter.upper()
                else:
                    hint_word += "_"
            hint = f"Pattern: {hint_word}"
            
        self.hints_used += 1
        
        embed = discord.Embed(
            title="💡 Hint",
            description=hint,
            color=0xf39c12
        )
        embed.set_footer(text=f"Hints used: {self.hints_used}/{self.max_hints}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @discord.ui.button(label='🏳️ Skip Word', style=discord.ButtonStyle.danger)
    async def skip_word(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_word_index >= len(self.word_data['words']):
            await interaction.response.send_message("Game completed!", ephemeral=True)
            return
            
        current_word = self.word_data['words'][self.current_word_index]
        
        embed = discord.Embed(
            title="⏭️ Word Skipped",
            description=f"The correct spelling was: **{current_word['word']}**",
            color=0xe74c3c
        )
        
        self.words_attempted += 1
        await self._next_word()
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @discord.ui.button(label='🏆 Leaderboard', style=discord.ButtonStyle.secondary)
    async def show_leaderboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        leaderboard = await self.cog.get_leaderboard(interaction.guild.id, self.difficulty)
        
        if not leaderboard:
            embed = discord.Embed(
                title="🏆 Spelling Bee Leaderboard",
                description="No scores recorded yet!",
                color=0x95a5a6
            )
        else:
            description = ""
            for i, (user_id, data) in enumerate(leaderboard[:10], 1):
                user = interaction.guild.get_member(user_id)
                username = user.display_name if user else "Unknown User"
                description += f"{i}. **{username}** - {data['high_score']} points\n"
                
            embed = discord.Embed(
                title=f"🏆 {self.difficulty.title()} Difficulty Leaderboard",
                description=description,
                color=0xf1c40f
            )
            
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @discord.ui.button(label='❌ End Game', style=discord.ButtonStyle.danger, row=1)
    async def end_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._end_game(interaction)
        
    async def _next_word(self):
        self.current_word_index += 1
        self.hints_used = 0
        
        if self.current_word_index >= len(self.word_data['words']):
            # Game completed
            for item in self.children:
                item.disabled = True
            
            await self._save_final_score()
            
            embed = discord.Embed(
                title="🎉 Spelling Bee Complete!",
                color=0x27ae60
            )
            embed.add_field(name="Final Score", value=f"{self.score} points", inline=True)
            embed.add_field(name="Words Correct", value=f"{self.words_correct}/{self.words_attempted}", inline=True)
            embed.add_field(name="Accuracy", value=f"{(self.words_correct/max(self.words_attempted, 1)*100):.1f}%", inline=True)
            
            await self.message.edit(embed=embed, view=self)
            return
            
        # Show next word
        current_word = self.word_data['words'][self.current_word_index]
        embed = discord.Embed(
            title="🐝 Spelling Bee",
            description=f"**Word {self.current_word_index + 1} of {len(self.word_data['words'])}**\n\nClick 🔊 to hear the word pronunciation!",
            color=0xf1c40f
        )
        embed.add_field(name="Current Score", value=f"{self.score} points", inline=True)
        embed.add_field(name="Difficulty", value=self.difficulty.title(), inline=True)
        embed.add_field(name="Progress", value=f"{self.words_correct} correct / {self.words_attempted} attempted", inline=True)
        embed.set_footer(text="Type your answer in chat after hearing the word!")
        
        await self.message.edit(embed=embed, view=self)
        
    async def _end_game(self, interaction):
        await self._save_final_score()
        
        for item in self.children:
            item.disabled = True
            
        embed = discord.Embed(
            title="🛑 Game Ended",
            description="Thanks for playing!",
            color=0xe74c3c
        )
        embed.add_field(name="Final Score", value=f"{self.score} points", inline=True)
        embed.add_field(name="Words Correct", value=f"{self.words_correct}/{max(self.words_attempted, 1)}", inline=True)
        
        await interaction.response.edit_message(embed=embed, view=self)
        
    async def _save_final_score(self):
        await self.cog.update_user_stats(
            self.ctx.guild.id, 
            self.ctx.author.id, 
            self.score, 
            self.words_correct, 
            self.words_attempted, 
            self.difficulty
        )

class SpellingBee(commands.Cog):
    """A comprehensive spelling bee bot with multiple difficulty levels and features."""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        
        default_guild = {
            "games": {},
            "leaderboards": {},
            "settings": {
                "max_concurrent_games": 3,
                "words_per_game": 10,
                "allow_hints": True
            }
        }
        
        default_user = {
            "stats": {
                "easy": {"games_played": 0, "high_score": 0, "total_score": 0, "words_correct": 0, "words_attempted": 0},
                "medium": {"games_played": 0, "high_score": 0, "total_score": 0, "words_correct": 0, "words_attempted": 0},
                "hard": {"games_played": 0, "high_score": 0, "total_score": 0, "words_correct": 0, "words_attempted": 0},
                "expert": {"games_played": 0, "high_score": 0, "total_score": 0, "words_correct": 0, "words_attempted": 0}
            }
        }
        
        self.config.register_guild(**default_guild)
        self.config.register_user(**default_user)
        
        # Word lists for different difficulties
        self.word_lists = {
            "easy": [
                {"word": "cat", "definition": "A small domesticated carnivorous mammal", "pronunciation": "/kæt/"},
                {"word": "dog", "definition": "A domesticated carnivorous mammal", "pronunciation": "/dɔːɡ/"},
                {"word": "house", "definition": "A building for human habitation", "pronunciation": "/haʊs/"},
                {"word": "school", "definition": "An institution for learning", "pronunciation": "/skuːl/"},
                {"word": "friend", "definition": "A person you like and know well", "pronunciation": "/frɛnd/"},
                {"word": "happy", "definition": "Feeling joy or pleasure", "pronunciation": "/ˈhæpi/"},
                {"word": "water", "definition": "A colorless, transparent liquid", "pronunciation": "/ˈwɔːtər/"},
                {"word": "plant", "definition": "A living organism that grows in earth", "pronunciation": "/plænt/"},
                {"word": "smile", "definition": "A pleased, happy expression", "pronunciation": "/smaɪl/"},
                {"word": "heart", "definition": "The organ that pumps blood", "pronunciation": "/hɑːrt/"},
                {"word": "music", "definition": "Vocal or instrumental sounds", "pronunciation": "/ˈmjuːzɪk/"},
                {"word": "color", "definition": "The appearance of objects in light", "pronunciation": "/ˈkʌlər/"},
                {"word": "money", "definition": "A medium of exchange", "pronunciation": "/ˈmʌni/"},
                {"word": "dance", "definition": "Move rhythmically to music", "pronunciation": "/dæns/"},
                {"word": "learn", "definition": "Acquire knowledge or skills", "pronunciation": "/lɜːrn/"}
            ],
            "medium": [
                {"word": "beautiful", "definition": "Pleasing the senses or mind", "pronunciation": "/ˈbjuːtɪfəl/"},
                {"word": "elephant", "definition": "A large mammal with a trunk", "pronunciation": "/ˈɛlɪfənt/"},
                {"word": "chocolate", "definition": "A sweet food made from cacao", "pronunciation": "/ˈtʃɔːklət/"},
                {"word": "mountain", "definition": "A large natural elevation of earth", "pronunciation": "/ˈmaʊntən/"},
                {"word": "sandwich", "definition": "Food between slices of bread", "pronunciation": "/ˈsænwɪtʃ/"},
                {"word": "telephone", "definition": "A device for voice communication", "pronunciation": "/ˈtɛlɪfoʊn/"},
                {"word": "basketball", "definition": "A sport played with a ball and hoops", "pronunciation": "/ˈbæskɪtbɔːl/"},
                {"word": "medicine", "definition": "Treatment for illness", "pronunciation": "/ˈmɛdəsən/"},
                {"word": "calendar", "definition": "A system showing days and months", "pronunciation": "/ˈkælɪndər/"},
                {"word": "library", "definition": "A place with books for reading", "pronunciation": "/ˈlaɪbrɛri/"},
                {"word": "computer", "definition": "An electronic device for processing data", "pronunciation": "/kəmˈpjuːtər/"},
                {"word": "exercise", "definition": "Physical activity for health", "pronunciation": "/ˈɛksərsaɪz/"},
                {"word": "temperature", "definition": "The degree of hotness or coldness", "pronunciation": "/ˈtɛmpərətʃər/"},
                {"word": "adventure", "definition": "An exciting or unusual experience", "pronunciation": "/ədˈvɛntʃər/"},
                {"word": "celebrate", "definition": "Acknowledge a special occasion with festivities", "pronunciation": "/ˈsɛləbreɪt/"}
            ],
            "hard": [
                {"word": "pneumonia", "definition": "Infection that inflames air sacs in lungs", "pronunciation": "/nʊˈmoʊnjə/"},
                {"word": "psychology", "definition": "The study of mind and behavior", "pronunciation": "/saɪˈkɑːlədʒi/"},
                {"word": "bureaucracy", "definition": "A system of government by departments", "pronunciation": "/bjʊˈrɑːkrəsi/"},
                {"word": "reconnaissance", "definition": "Military observation of a region", "pronunciation": "/rɪˈkɑːnəsəns/"},
                {"word": "pharmaceutical", "definition": "Relating to medicinal drugs", "pronunciation": "/ˌfɑːrməˈsuːtɪkəl/"},
                {"word": "conscientious", "definition": "Wishing to do what is right", "pronunciation": "/ˌkɑːnʃiˈɛnʃəs/"},
                {"word": "entrepreneurship", "definition": "The activity of setting up businesses", "pronunciation": "/ˌɑːntrəprəˈnɜːrʃɪp/"},
                {"word": "sophisticated", "definition": "Complex or refined", "pronunciation": "/səˈfɪstɪkeɪtɪd/"},
                {"word": "deteriorate", "definition": "Become progressively worse", "pronunciation": "/dɪˈtɪriəreɪt/"},
                {"word": "miscellaneous", "definition": "Consisting of various types", "pronunciation": "/ˌmɪsəˈleɪniəs/"},
                {"word": "pronunciation", "definition": "The way words are spoken", "pronunciation": "/prəˌnʌnsiˈeɪʃən/"},
                {"word": "accommodate", "definition": "Provide lodging or sufficient space", "pronunciation": "/əˈkɑːmədeɪt/"},
                {"word": "millennium", "definition": "A period of one thousand years", "pronunciation": "/mɪˈlɛniəm/"},
                {"word": "architecture", "definition": "The design and construction of buildings", "pronunciation": "/ˈɑːrkɪtɛktʃər/"},
                {"word": "refrigerator", "definition": "An appliance for keeping food cold", "pronunciation": "/rɪˈfrɪdʒəreɪtər/"}
            ],
            "expert": [
                {"word": "onomatopoeia", "definition": "Words that imitate sounds", "pronunciation": "/ˌɑːnəˌmætəˈpiːə/"},
                {"word": "chrysanthemum", "definition": "A type of flowering plant", "pronunciation": "/krɪˈsænθəməm/"},
                {"word": "schadenfreude", "definition": "Pleasure from another's misfortune", "pronunciation": "/ˈʃɑːdənfrɔɪdə/"},
                {"word": "antidisestablishmentarianism", "definition": "Opposition to withdrawal of state support from church", "pronunciation": "/ˌæntiˌdɪsɪˌstæblɪʃmənˈtɛriəˌnɪzəm/"},
                {"word": "floccinaucinihilipilification", "definition": "The action of estimating something as worthless", "pronunciation": "/ˌflɑːksɪˌnɔːsɪˌnaɪhɪlɪˌpɪlɪfɪˈkeɪʃən/"},
                {"word": "pneumonoultramicroscopicsilicovolcanoconiosiss", "definition": "A lung disease caused by inhaling very fine silicate dust", "pronunciation": "/ˌnuːmənoʊˌʌltrəˌmaɪkrəˈskɑːpɪkˌsɪlɪkoʊˌvɑːlkeɪnoʊˌkoʊniˈoʊsɪs/"},
                {"word": "hippopotomonstrosesquippedaliophobia", "definition": "Fear of long words", "pronunciation": "/ˌhɪpəˌpɑːtəˌmɑːnstrəˌsɛskwɪˌpɛdæliəˈfoʊbiə/"},
                {"word": "supercalifragilisticexpialidocious", "definition": "Extraordinarily good; wonderful", "pronunciation": "/ˌsuːpərˌkælɪˌfrædʒəlɪstɪkˌɛkspiˌælɪˈdoʊʃəs/"},
                {"word": "pseudopseudohypoparathyroidism", "definition": "A genetic disorder", "pronunciation": "/ˌsuːdoʊˌsuːdoʊˌhaɪpoʊˌpærəˈθaɪrɔɪdɪzəm/"},
                {"word": "psychopharmacology", "definition": "Study of drug-induced changes in mood", "pronunciation": "/ˌsaɪkoʊˌfɑːrməˈkɑːlədʒi/"},
                {"word": "electroencephalography", "definition": "Recording of brain electrical activity", "pronunciation": "/ɪˌlɛktroʊɪnˌsɛfəˈlɑːɡrəfi/"},
                {"word": "immunoelectrophoresis", "definition": "A lab technique for protein analysis", "pronunciation": "/ˌɪmjənoʊɪˌlɛktroʊfəˈriːsɪs/"},
                {"word": "spectrophotometry", "definition": "Quantitative measurement of light reflection", "pronunciation": "/ˌspɛktroʊfoʊˈtɑːmətri/"},
                {"word": "deinstitutionalization", "definition": "Process of moving care from institutions", "pronunciation": "/ˌdiːɪnstɪˌtuːʃənəlaɪˈzeɪʃən/"},
                {"word": "counterrevolutionaries", "definition": "People opposing a revolution", "pronunciation": "/ˌkaʊntərrɛvəˈluːʃəˌnɛriz/"}
            ]
        }
        
        self.active_games = {}  # Track active games by user ID
        
    @commands.group(name="spellingbee", aliases=["sb"])
    async def spelling_bee(self, ctx):
        """Spelling bee commands."""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="🐝 Spelling Bee Bot",
                description="Welcome to the Spelling Bee! Test your spelling skills with words of varying difficulty.",
                color=0xf1c40f
            )
            embed.add_field(
                name="Available Commands",
                value="• `!spellingbee start` - Start a new game\n"
                      "• `!spellingbee stats` - View your statistics\n"
                      "• `!spellingbee leaderboard` - View leaderboards\n"
                      "• `!spellingbee settings` - Configure bot settings",
                inline=False
            )
            embed.add_field(
                name="Difficulty Levels",
                value="🟢 **Easy** - Simple everyday words\n"
                      "🟡 **Medium** - Common but longer words\n"
                      "🔴 **Hard** - Complex and challenging words\n"
                      "⚫ **Expert** - Extremely difficult words",
                inline=False
            )
            embed.set_footer(text="Click buttons during gameplay for pronunciation, definitions, and hints!")
            
            await ctx.send(embed=embed)
    
    @spelling_bee.command(name="start")
    async def start_game(self, ctx):
        """Start a new spelling bee game."""
        if ctx.author.id in self.active_games:
            await ctx.send("❌ You already have an active game! Please finish it first.")
            return
            
        # Difficulty selection
        difficulty_view = DifficultySelectionView(self, ctx)
        embed = discord.Embed(
            title="🐝 Select Difficulty Level",
            description="Choose your preferred difficulty level:",
            color=0xf1c40f
        )
        embed.add_field(name="🟢 Easy", value="Simple everyday words (5-7 letters)", inline=True)
        embed.add_field(name="🟡 Medium", value="Common but longer words (8-12 letters)", inline=True)
        embed.add_field(name="🔴 Hard", value="Complex words (10+ letters)", inline=True)
        embed.add_field(name="⚫ Expert", value="Extremely difficult words", inline=True)
        
        message = await ctx.send(embed=embed, view=difficulty_view)
        difficulty_view.message = message
        
    @spelling_bee.command(name="stats")
    async def show_stats(self, ctx, user: discord.Member = None):
        """Show spelling bee statistics for a user."""
        target_user = user or ctx.author
        stats = await self.config.user(target_user).stats()
        
        embed = discord.Embed(
            title=f"📊 {target_user.display_name}'s Spelling Bee Stats",
            color=0x3498db
        )
        
        for difficulty, data in stats.items():
            if data["games_played"] > 0:
                accuracy = (data["words_correct"] / max(data["words_attempted"], 1)) * 100
                avg_score = data["total_score"] / data["games_played"]
                
                embed.add_field(
                    name=f"{difficulty.title()} Difficulty",
                    value=f"Games Played: {data['games_played']}\n"
                          f"High Score: {data['high_score']}\n"
                          f"Average Score: {avg_score:.1f}\n"
                          f"Accuracy: {accuracy:.1f}%",
                    inline=True
                )
        
        if not any(data["games_played"] > 0 for data in stats.values()):
            embed.description = "No games played yet! Use `!spellingbee start` to begin."
            
        await ctx.send(embed=embed)
        
    @spelling_bee.command(name="leaderboard", aliases=["lb"])
    async def show_leaderboard(self, ctx, difficulty: str = "easy"):
        """Show the spelling bee leaderboard for a difficulty."""
        if difficulty.lower() not in ["easy", "medium", "hard", "expert"]:
            await ctx.send("❌ Invalid difficulty! Choose from: easy, medium, hard, expert")
            return
            
        leaderboard = await self.get_leaderboard(ctx.guild.id, difficulty.lower())
        
        if not leaderboard:
            embed = discord.Embed(
                title=f"🏆 {difficulty.title()} Difficulty Leaderboard",
                description="No scores recorded yet!",
                color=0x95a5a6
            )
            await ctx.send(embed=embed)
            return
            
        description = ""
        for i, (user_id, data) in enumerate(leaderboard[:10], 1):
            user = ctx.guild.get_member(user_id)
            username = user.display_name if user else "Unknown User"
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            description += f"{medal} **{username}** - {data['high_score']} points\n"
            
        embed = discord.Embed(
            title=f"🏆 {difficulty.title()} Difficulty Leaderboard",
            description=description,
            color=0xf1c40f
        )
        
        await ctx.send(embed=embed)
        
    @spelling_bee.group(name="settings")
    @checks.admin_or_permissions(manage_guild=True)
    async def settings(self, ctx):
        """Configure spelling bee settings."""
        if ctx.invoked_subcommand is None:
            settings = await self.config.guild(ctx.guild).settings()
            
            embed = discord.Embed(
                title="⚙️ Spelling Bee Settings",
                color=0x95a5a6
            )
            embed.add_field(name="Max Concurrent Games", value=settings["max_concurrent_games"], inline=True)
            embed.add_field(name="Words Per Game", value=settings["words_per_game"], inline=True)
            embed.add_field(name="Allow Hints", value="✅" if settings["allow_hints"] else "❌", inline=True)
            
            await ctx.send(embed=embed)
    
    async def start_spelling_game(self, ctx, difficulty: str):
        """Start a spelling bee game with the specified difficulty."""
        settings = await self.config.guild(ctx.guild).settings()
        
        # Check concurrent games limit
        active_count = len([g for g in self.active_games.values() if g.get("guild_id") == ctx.guild.id])
        if active_count >= settings["max_concurrent_games"]:
            await ctx.send(f"❌ Maximum concurrent games ({settings['max_concurrent_games']}) reached in this server!")
            return
            
        # Select random words for the game
        word_pool = self.word_lists[difficulty].copy()
        random.shuffle(word_pool)
        selected_words = word_pool[:settings["words_per_game"]]
        
        word_data = {
            "words": selected_words,
            "difficulty": difficulty
        }
        
        game_id = f"{ctx.guild.id}_{ctx.author.id}_{datetime.now().timestamp()}"
        
        # Create the game view
        view = SpellingBeeView(self, ctx, word_data, difficulty, game_id)
        
        embed = discord.Embed(
            title="🐝 Spelling Bee Started!",
            description=f"**Word 1 of {len(selected_words)}**\n\nClick 🔊 to hear the word pronunciation!",
            color=0xf1c40f
        )
        embed.add_field(name="Difficulty", value=difficulty.title(), inline=True)
        embed.add_field(name="Current Score", value="0 points", inline=True)
        embed.add_field(name="Progress", value="0 correct / 0 attempted", inline=True)
        embed.set_footer(text="Type your answer in chat after hearing the word!")
        
        message = await ctx.send(embed=embed, view=view)
        view.message = message
        
        # Track the active game
        self.active_games[ctx.author.id] = {
            "guild_id": ctx.guild.id,
            "view": view,
            "message": message
        }
        
        # Set up message listener for spelling attempts
        def check(m):
            return (m.author == ctx.author and 
                   m.channel == ctx.channel and 
                   ctx.author.id in self.active_games)
                   
        while ctx.author.id in self.active_games:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=300.0)
                await self._process_spelling_attempt(view, msg)
                
            except asyncio.TimeoutError:
                # Game timed out
                if ctx.author.id in self.active_games:
                    del self.active_games[ctx.author.id]
                    
                for item in view.children:
                    item.disabled = True
                    
                embed = discord.Embed(
                    title="⏰ Game Timed Out",
                    description="The game has ended due to inactivity.",
                    color=0x95a5a6
                )
                embed.add_field(name="Final Score", value=f"{view.score} points", inline=True)
                
                try:
                    await message.edit(embed=embed, view=view)
                except:
                    pass
                break
                
    async def _process_spelling_attempt(self, view, message):
        """Process a spelling attempt from the user."""
        if view.current_word_index >= len(view.word_data['words']):
            return
            
        current_word = view.word_data['words'][view.current_word_index]
        user_spelling = message.content.strip().lower()
        correct_spelling = current_word['word'].lower()
        
        view.words_attempted += 1
        
        # Calculate points based on difficulty and word length
        difficulty_multipliers = {"easy": 1, "medium": 2, "hard": 3, "expert": 5}
        base_points = len(correct_spelling) * difficulty_multipliers[view.difficulty]
        
        if user_spelling == correct_spelling:
            # Correct spelling
            view.words_correct += 1
            
            # Bonus points for not using hints
            hint_penalty = view.hints_used * 2
            points_earned = max(base_points - hint_penalty, 1)
            view.score += points_earned
            
            embed = discord.Embed(
                title="✅ Correct!",
                description=f"**{current_word['word']}** is spelled correctly!",
                color=0x27ae60
            )
            embed.add_field(name="Points Earned", value=f"+{points_earned}", inline=True)
            embed.add_field(name="Total Score", value=f"{view.score}", inline=True)
            
            if view.hints_used > 0:
                embed.add_field(name="Hint Penalty", value=f"-{hint_penalty}", inline=True)
                
            try:
                await message.add_reaction("✅")
                await message.channel.send(embed=embed, delete_after=5)
            except:
                pass
                
        else:
            # Incorrect spelling
            embed = discord.Embed(
                title="❌ Incorrect",
                description=f"The correct spelling is: **{current_word['word']}**",
                color=0xe74c3c
            )
            embed.add_field(name="Your Answer", value=user_spelling, inline=True)
            embed.add_field(name="Current Score", value=f"{view.score}", inline=True)
            
            try:
                await message.add_reaction("❌")
                await message.channel.send(embed=embed, delete_after=8)
            except:
                pass
                
        # Move to next word
        await view._next_word()
        
    async def get_leaderboard(self, guild_id: int, difficulty: str) -> List[Tuple[int, dict]]:
        """Get leaderboard for a specific difficulty."""
        all_users = await self.config.all_users()
        leaderboard_data = []
        
        for user_id, user_data in all_users.items():
            stats = user_data.get("stats", {}).get(difficulty, {})
            if stats.get("games_played", 0) > 0:
                leaderboard_data.append((user_id, stats))
                
        # Sort by high score descending
        leaderboard_data.sort(key=lambda x: x[1]["high_score"], reverse=True)
        return leaderboard_data
        
    async def update_user_stats(self, guild_id: int, user_id: int, score: int, 
                              words_correct: int, words_attempted: int, difficulty: str):
        """Update user statistics after a game."""
        async with self.config.user_from_id(user_id).stats() as stats:
            difficulty_stats = stats[difficulty]
            
            difficulty_stats["games_played"] += 1
            difficulty_stats["total_score"] += score
            difficulty_stats["words_correct"] += words_correct
            difficulty_stats["words_attempted"] += words_attempted
            
            if score > difficulty_stats["high_score"]:
                difficulty_stats["high_score"] = score
                
        # Clean up active game
        if user_id in self.active_games:
            del self.active_games[user_id]

class DifficultySelectionView(discord.ui.View):
    """View for selecting game difficulty."""
    
    def __init__(self, cog, ctx):
        super().__init__(timeout=60)
        self.cog = cog
        self.ctx = ctx
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.ctx.author
        
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except:
            pass
            
    @discord.ui.button(label='🟢 Easy', style=discord.ButtonStyle.success)
    async def easy_difficulty(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.cog.start_spelling_game(self.ctx, "easy")
        
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)
        
    @discord.ui.button(label='🟡 Medium', style=discord.ButtonStyle.primary)
    async def medium_difficulty(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.cog.start_spelling_game(self.ctx, "medium")
        
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)
        
    @discord.ui.button(label='🔴 Hard', style=discord.ButtonStyle.danger)
    async def hard_difficulty(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.cog.start_spelling_game(self.ctx, "hard")
        
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)
        
    @discord.ui.button(label='⚫ Expert', style=discord.ButtonStyle.secondary)
    async def expert_difficulty(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.cog.start_spelling_game(self.ctx, "expert")
        
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(SpellingBee(bot))
