import hashlib
import os
import math
import urllib.request as urllib
from io import BytesIO
from PIL import Image
from pyrogram import Client
import telegram
import logging
import json
from typing import Optional, List
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram import TelegramError
from telegram import Update, Bot
from telegram.ext import CommandHandler, run_async, Updater, Handler, InlineQueryHandler
from telegram.utils.helpers import escape_markdown
from telegram import Message, Chat, MessageEntity, InlineQueryResultArticle
from os import path
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

# Load environment variables
load_dotenv()  # Ensure you have a .env file in the same directory

# Get configuration values from the .env file
TOKEN = os.getenv("TOKEN")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

# Ensure these environment variables are available
if not TOKEN or not API_ID or not API_HASH:
    logger.error("Environment variables missing! Exiting now.")
    exit(1)

# Initialize Pyrogram client
pyrogram_client = Client("my_bot", api_id=API_ID, api_hash=API_HASH)

updater = telegram.ext.Updater(token=TOKEN)
bot = updater.bot
dispatcher = updater.dispatcher

START_TEXT = """
Hey! I'm {}, and I'm a bot which allows you to create a sticker pack from other stickers, images and documents!
I only have a few commands so I don't have a help menu or anything like that.
You can also check out the source code for the bot [here](https://github.com/koreansmu/stormkang-sticker)
""".format(dispatcher.bot.first_name)

# /start Command
@run_async
def start(bot: Bot, update: Update):
    if update.effective_chat.type == "private":
        update.effective_message.reply_text(START_TEXT, parse_mode=ParseMode.MARKDOWN)


# /kang Command (to create a sticker pack with no customization)
@run_async
def kang(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message
    user = update.effective_user
    packname = f"a{str(user.id)}_by_{bot.username}"
    packnum = 0
    max_stickers = 120
    packname_found = 0
    while packname_found == 0:
        try:
            stickerset = bot.get_sticker_set(packname)
            if len(stickerset.stickers) >= max_stickers:
                packnum += 1
                packname = f"a{packnum}_{str(user.id)}_by_{bot.username}"
            else:
                packname_found = 1
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                packname_found = 1

    if msg.reply_to_message:
        if msg.reply_to_message.sticker:
            file_id = msg.reply_to_message.sticker.file_id
        elif msg.reply_to_message.photo:
            file_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.document:
            file_id = msg.reply_to_message.document.file_id
        else:
            msg.reply_text("I can't kang that.")
            return
        kang_file = bot.get_file(file_id)
        kang_file.download('kangsticker.png')

        if args:
            sticker_emoji = str(args[0])
        else:
            sticker_emoji = "🤔"

        try:
            im = Image.open('kangsticker.png')
            if (im.width and im.height) < 512:
                size1 = im.width
                size2 = im.height
                if im.width > im.height:
                    scale = 512/size1
                    size1new = 512
                    size2new = size2 * scale
                else:
                    scale = 512/size2
                    size1new = size1 * scale
                    size2new = 512
                size1new = math.floor(size1new)
                size2new = math.floor(size2new)
                sizenew = (size1new, size2new)
                im = im.resize(sizenew)
            else:
                maxsize = (512, 512)
                im.thumbnail(maxsize)

            im.save('kangsticker.png', "PNG")
            bot.add_sticker_to_set(user_id=user.id, name=packname,
                                    png_sticker=open('kangsticker.png', 'rb'), emojis=sticker_emoji)
            msg.reply_text(f"Sticker successfully added to [pack](t.me/addstickers/{packname})" +
                            f"\nEmoji is: {sticker_emoji}", parse_mode=ParseMode.MARKDOWN)
        except OSError as e:
            msg.reply_text("I can only kang images m8.")
            print(e)
            return
    else:
        msg.reply_text("Please reply to a sticker, or image to kang it!")


# /kangim Command (to create a sticker pack with image and user details)
@run_async
def kangim(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message
    user = update.effective_user
    packname = f"a{str(user.id)}_by_{bot.username}"
    packnum = 0
    max_stickers = 120
    packname_found = 0
    while packname_found == 0:
        try:
            stickerset = bot.get_sticker_set(packname)
            if len(stickerset.stickers) >= max_stickers:
                packnum += 1
                packname = f"a{packnum}_{str(user.id)}_by_{bot.username}"
            else:
                packname_found = 1
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                packname_found = 1

    # Check if user provided custom background color
    background_color = args[0] if args else "white"  # Default to white if no color is provided

    # Code to handle custom background color and text overlay
    # You could use Pillow to create a background and overlay the user details (profile pic, name)
    try:
        profile_picture = pyrogram_client.download_profile_photo(user.id)
        profile_image = Image.open(profile_picture)

        # Create background image with specified color
        bg = Image.new("RGB", (512, 512), background_color)
        bg.paste(profile_image, (0, 0))

        # Add user's name or text on top (custom font can be used)
        draw = ImageDraw.Draw(bg)
        font = ImageFont.load_default()
        name = user.first_name
        draw.text((10, 10), name, font=font, fill=(255, 255, 255))

        bg.save('kangsticker_modified.png', "PNG")

        bot.add_sticker_to_set(user_id=user.id, name=packname,
                               png_sticker=open('kangsticker_modified.png', 'rb'), emojis="🤔")
        msg.reply_text(f"Sticker successfully added to [pack](t.me/addstickers/{packname})" +
                        f"\nEmoji is: 🤔", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        msg.reply_text(f"An error occurred: {str(e)}")
        print(e)

    # Clean up temporary files
    if os.path.isfile("kangsticker_modified.png"):
        os.remove("kangsticker_modified.png")
    if os.path.isfile("profile_pic.jpg"):
        os.remove("profile_pic.jpg")


# /kangm Command (to create a sticker pack with customization options)
@run_async
def kangm(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message
    user = update.effective_user
    packname = f"a{str(user.id)}_by_{bot.username}"
    packnum = 0
    max_stickers = 120
    packname_found = 0
    while packname_found == 0:
        try:
            stickerset = bot.get_sticker_set(packname)
            if len(stickerset.stickers) >= max_stickers:
                packnum += 1
                packname = f"a{packnum}_{str(user.id)}_by_{bot.username}"
            else:
                packname_found = 1
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                packname_found = 1

    # Check if user provided custom background color
    background_color = args[0] if args else "white"  # Default to white if no color is provided

    # Code to handle custom background color and text overlay
    # You could use Pillow to create a background and overlay the user details (profile pic, name)
    try:
        profile_picture = pyrogram_client.download_profile_photo(user.id)
        profile_image = Image.open(profile_picture)

        # Create background image with specified color
        bg = Image.new("RGB", (512, 512), background_color)
        bg.paste(profile_image, (0, 0))

        bg.save('kangsticker_modified.png', "PNG")

        bot.add_sticker_to_set(user_id=user.id, name=packname,
                               png_sticker=open('kangsticker_modified.png', 'rb'), emojis="🤔")
        msg.reply_text(f"Sticker successfully added to [pack](t.me/addstickers/{packname})" +
                        f"\nEmoji is: 🤔", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        msg.reply_text(f"An error occurred: {str(e)}")
        print(e)

    # Clean up temporary files
    if os.path.isfile("kangsticker_modified.png"):
        os.remove("kangsticker_modified.png")


# Adding handlers to the dispatcher
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("kang", kang, pass_args=True))
dispatcher.add_handler(CommandHandler("kangim", kangim, pass_args=True))
dispatcher.add_handler(CommandHandler("kangm", kangm, pass_args=True))

updater.start_polling(timeout=15, read_latency=4)
updater.idle()
