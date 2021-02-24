from discord.ext.commands import Bot, Context, when_mentioned
from discord.player import FFmpegPCMAudio
from os import getenv, listdir, environ
from sys import stdout, exit
from utils import eprint
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


async def play_audio_queue() -> None:
    """Async loop for playing the audio queue
    """
    while True:
        (voice_client, audio, filename) = await audio_queue.get()
        logging.info(f"Playing {filename}")
        voice_client.play(audio)
        while voice_client.is_playing():
            await asyncio.sleep(0.02)


@bot.command()
async def status(context: Context) -> None:
    """Ping command to check if the bot is up

    Parameters
    ----------
    context : Context
        Context provided by discord.py
    """
    await context.reply("I'm up.")
    logging.info(
        (f"Status requested by [{context.author}] "
         f"in [{context.guild}/{context.channel}].")
    )


@bot.command()
async def join(context: Context) -> None:
    """Tells the bot to join the caller's current channel

    Parameters
    ----------
    context : Context
        Context provided by discord.py
    """
    if context.author.voice == None:
        await context.reply("You're not in a voice channel!")
    else:
        vc = [vc for vc in context.bot.voice_clients if vc.guild == context.guild]
        if vc != [context.voice_client]:
            await context.author.voice.channel.connect()


@bot.command()
async def play(context: Context, number: int) -> None:
    """Tells the bot to play a number of audio files

    Parameters
    ----------
    context : Context
        Context provided by discord.py
    number : int
        The number of audio files, must be greater than 0. If greater than
        the number of available files, adds the audio file list to the queue
        again
    """
    if number < 1:
        context.reply("Cannot play fewer than 1 audio clips!")
    else:
        files = [f for f in listdir("audio")]
        while len(files) < number:
            files += files
        files = files[:number]
        logging.info(
            (f"Playback requested by [{context.author.name}] in "
             f"[{context.guild}/{context.channel}]")
        )
        for filename in files:
            audio = FFmpegPCMAudio(f"audio/{filename}")
            await audio_queue.put((context.voice_client, audio, filename))


@bot.command()
async def shuffle(context: Context, number: int) -> None:
    """Tells the bot to play a number of audio files, shuffled

    Parameters
    ----------
    context : Context
        Context provided by discord.py
    number : int
        The number of audio files, must be greater than 0. If greater than
        the number of available files, adds duplicates to the queue
    """
    if number < 1:
        context.reply("Cannot play fewer than 1 audio clips!")
    else:
        await join(context)
        files = [f for f in listdir("audio")]
        while len(files) < number:
            files += files
        random.shuffle(files)
        files = files[:number]
        logging.info(
            (f"Playback requested by [{context.author.name}] in "
             f"[{context.guild}/{context.channel}]")
        )
        for filename in files:
            audio = FFmpegPCMAudio(f"audio/{filename}")
            await audio_queue.put((context.voice_client, audio, filename))


@bot.command()
async def cancel(context: Context) -> None:
    """Tells the bot to cancel the active audio queue. Stops playback and
    clears the queue.

    Parameters
    ----------
    context : Context
        Context provided by discord.py
    """
    logging.info(
        (f"Audio playback cancellation requested by {context.author}"
         f" in {context.guild}")
    )
    context.voice_client.stop()
    for _ in range(audio_queue.qsize()):
        audio_queue.get_nowait()
        audio_queue.task_done()


@bot.command()
async def disconnect(context: Context) -> None:
    """Tells the bot to disconnect from its current voice channel

    Parameters
    ----------
    context : Context
        Context provided by discord.py
    """
    logging.info(f"Disconnect requested by [{context.author.name}]")
    await context.voice_client.disconnect()


bot.loop.create_task(play_audio_queue())

if "AUDIOBOT_TOKEN" in environ:
    try:
        bot.run(getenv("AUDIOBOT_TOKEN"))
    except:
        eprint("Invalid bot token!")
        exit(1)
else:
    eprint("AUDIOBOT_TOKEN environment variable not defined!")
    exit(1)
