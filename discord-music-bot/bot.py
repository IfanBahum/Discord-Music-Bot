import discord
from discord.ext import commands
import os
import aiohttp
from dotenv import load_dotenv

# Load token dari .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

playlist_folder = './playlist'
music_queue = []

# === EVENT SAAT BOT SIAP ===
@bot.event
async def on_ready():
    print(f'✅ Bot aktif sebagai {bot.user.name}')
    if not os.path.exists(playlist_folder):
        os.makedirs(playlist_folder)

# === UPLOAD FILE MUSIK ===
@bot.command()
async def upload(ctx):
    if not ctx.message.attachments:
        await ctx.send("❗ Silakan lampirkan file lagu (.mp3/.wav).")
        return

    for attachment in ctx.message.attachments:
        if attachment.filename.endswith(('.mp3', '.wav')):
            file_path = os.path.join(playlist_folder, attachment.filename)

            if os.path.exists(file_path):
                await ctx.send(f"⚠️ File `{attachment.filename}` sudah ada.")
                continue

            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status == 200:
                        with open(file_path, 'wb') as f:
                            f.write(await resp.read())
                        await ctx.send(f"✅ Lagu `{attachment.filename}` berhasil ditambahkan.")
                    else:
                        await ctx.send("❌ Gagal mengunduh file.")
        else:
            await ctx.send("❗ Hanya file .mp3 atau .wav yang diperbolehkan.")

# === JOIN VOICE CHANNEL ===
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()
        await ctx.send("🔊 Bot bergabung ke voice channel.")
    else:
        await ctx.send("❗ Kamu harus masuk ke voice channel dulu.")

# === LEAVE VOICE CHANNEL ===
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Bot keluar dari voice channel.")
    else:
        await ctx.send("❗ Bot tidak sedang terhubung ke voice channel.")

# === MAINKAN SEMUA LAGU ===
@bot.command()
async def play(ctx):
    if not ctx.voice_client:
        await ctx.invoke(bot.get_command('join'))

    files = [f for f in os.listdir(playlist_folder) if f.endswith(('.mp3', '.wav'))]
    if not files:
        await ctx.send("❗ Tidak ada lagu yang diupload.")
        return

    music_queue.clear()
    music_queue.extend(files)
    await play_next_song(ctx)

# === FUNGSI MEMAINKAN LAGU BERIKUTNYA ===
async def play_next_song(ctx):
    if len(music_queue) == 0:
        await ctx.send("✅ Playlist selesai.")
        await ctx.voice_client.disconnect()
        return

    next_song = music_queue.pop(0)
    path = os.path.join(playlist_folder, next_song)

    try:
        source = discord.FFmpegPCMAudio(executable="ffmpeg", source=path)
        ctx.voice_client.play(source, after=lambda e: bot.loop.create_task(play_next_song(ctx)))
        await ctx.send(f"🎵 Memutar: {next_song}")
    except Exception as e:
        await ctx.send(f"❌ Gagal memutar {next_song}. Error: {str(e)}")
        await play_next_song(ctx)

# === SKIP LAGU ===
@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭ Lagu dilewati.")

# === PAUSE DAN RESUME ===
@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸ Lagu dijeda.")

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Lagu dilanjutkan.")

# === PUTAR LAGU TERTENTU ===
@bot.command()
async def putar(ctx, *, nama_file):
    path = os.path.join(playlist_folder, nama_file)
    if not os.path.exists(path):
        await ctx.send("❌ Lagu tidak ditemukan.")
        return

    if not ctx.voice_client:
        await ctx.invoke(bot.get_command('join'))

    ctx.voice_client.stop()
    source = discord.FFmpegPCMAudio(executable="ffmpeg", source=path)
    ctx.voice_client.play(source)
    await ctx.send(f"🎵 Memutar: {nama_file}")

# === DAFTAR LAGU ===
@bot.command()
async def list(ctx):
    files = os.listdir(playlist_folder)
    if not files:
        await ctx.send("📭 Belum ada lagu yang diupload.")
    else:
        daftar = "\n".join(f"🎶 {f}" for f in files)
        await ctx.send(f"**Daftar lagu yang tersedia:**\n{daftar}")

bot.run(TOKEN)