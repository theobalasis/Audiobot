from discord.ext.commands import Bot, Context, when_mentioned
from discord.player import FFmpegPCMAudio
from os import getenv, listdir
from sys import stdout
import asyncio
import logging
import random

logging.basicConfig(
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    stream=stdout,
    level=logging.INFO
)

bot = Bot(command_prefix=when_mentioned)
audio_queue = asyncio.Queue()
play_next = asyncio.Event()


async def play_audio_queue():
    while True:
        (voice_client, audio, filename) = await audio_queue.get()
        logging.info(f"Playing {filename}")
        voice_client.play(audio)
        while voice_client.is_playing():
            await asyncio.sleep(0.02)


@bot.command()
async def status(ctx: Context) -> None:
    await ctx.reply("I'm up.")
    logging.info(
        (f"Status requested by [{ctx.author}] "
         f"in [{ctx.guild}/{ctx.channel}].")
    )


@bot.command()
async def join(ctx: Context) -> None:
    if ctx.author.voice == None:
        await ctx.reply("You're not in a voice channel!")
    else:
        if [vc for vc in ctx.bot.voice_clients if vc.guild == ctx.guild] != [ctx.voice_client]:
            await ctx.author.voice.channel.connect()


@bot.command()
async def shuffle(ctx: Context, number: int) -> None:
    await join(ctx)
    files = [f for f in listdir("audio")]
    random.shuffle(files)
    logging.info(
        (f"Playback requested by [{ctx.author.name}] in "
         f"[{ctx.guild}/{ctx.channel}]")
    )
    for filename in files[:number]:
        audio = FFmpegPCMAudio(
            f"audio/{filename}",
            before_options='-guess_layout_max 0',
            options='-ac 2'
        )
        await audio_queue.put((ctx.voice_client, audio, filename))


@bot.command()
async def play(ctx: Context) -> None:
    await shuffle(ctx, 1)


@bot.command()
async def cancel(ctx: Context) -> None:
    logging.info(
        (f"Audio playback cancellation requested by {ctx.author}"
         f" in {ctx.guild}")
    )
    ctx.voice_client.stop()
    for _ in range(audio_queue.qsize()):
        audio_queue.get_nowait()
        audio_queue.task_done()


@bot.command()
async def disconnect(ctx: Context) -> None:
    logging.info(f"Disconnect requested by [{ctx.author.name}]")
    await ctx.voice_client.disconnect()


bot.loop.create_task(play_audio_queue())

bot.run(getenv("AUDIOBOT_TOKEN"))
