import hashlib
import os
import math
import urllib.request as urllib

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

def getConfig(name: str):
    return os.environ[name]

try:
     TOKEN = "7366093843:AAHerH1Z83vVFsVoASPyR003U5nj4bprZcs"
except KeyError as e:
    LOGGER.error("TOKEN env variables missing! Exiting now")
    exit(1)

updater = telegram.ext.Updater(token=TOKEN)
bot = updater.bot
dispatcher = updater.dispatcher

START_TEXT = """
ʀᴀᴅʜᴇ ʀᴀᴅʜᴇ ! ɪ'ᴍ {}, ᴀɴᴅ ᴛʜɪs ɪs ʙɪʟʟᴀ ᴋᴀɴɢ sᴛɪᴄᴋᴇʀ ʙᴏᴛ ᴡʜɪᴄʜ ᴀʟʟᴏᴡs ʏᴏᴜ ᴛᴏ ᴄʀᴇᴀᴛᴇ ᴀ sᴛɪᴄᴋᴇʀ ᴘᴀᴄᴋ ғʀᴏᴍ ᴏᴛʜᴇʀ sᴛɪᴄᴋᴇʀs, ɪᴍᴀɢᴇs ᴀɴᴅ ᴅᴏᴄᴜᴍᴇɴᴛs! 
ɪ ᴏɴʟʏ ʜᴀᴠᴇ ᴀ ғᴇᴡ ᴄᴏᴍᴍᴀɴᴅs sᴏ ɪ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀ ʜᴇʟᴘ ᴍᴇɴᴜ ᴏʀ ᴀɴʏᴛʜɪɴɢ ʟɪᴋᴇ ᴛʜᴀᴛ. ʏᴏᴜ ᴄᴀɴ ᴀʟsᴏ ᴄᴀʟʟ ᴏᴜᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ғᴏʀ ᴛʜᴇ ʜᴇʟᴘ ᴏғ ʙᴏᴛ [ʜᴇʀᴇ](https://t.me/interstellarXd)
""".format(dispatcher.bot.first_name)

@run_async
def start(bot: Bot, update: Update):
    if update.effective_chat.type == "private":
        update.effective_message.reply_text(START_TEXT, parse_mode=ParseMode.MARKDOWN)

# Color name mapping to hex values
color_map = {
    "red": "#FF0000",
    "green": "#008000",
    "blue": "#0000FF",
    "yellow": "#FFFF00",
    "purple": "#800080",
    "orange": "#FFA500",
    "pink": "#FFC0CB",
    "black": "#000000",
    "white": "#FFFFFF",
    "gray": "#808080",
    "brown": "#A52A2A",
}

# Function to ensure sticker pack is valid
def check_pack_validity(bot: Bot, user: telegram.User, packname: str, max_stickers: int) -> str:
    packnum = 0
    packname_found = False
    while not packname_found:
        try:
            stickerset = bot.get_sticker_set(packname)
            if len(stickerset.stickers) >= max_stickers:
                packnum += 1
                packname = f"a{packnum}_{str(user.id)}_by_{bot.username}"
            else:
                packname_found = True
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                packname_found = True
    return packname

# Kang with user's name, profile picture, and background color
@run_async
def kangm(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message
    user = update.effective_user
    packname = f"a{str(user.id)}_by_{bot.username}"
    max_stickers = 120
    packname = check_pack_validity(bot, user, packname, max_stickers)

    # Retrieve background color
    background_color = args[0] if args and args[0].lower() in color_map else "white"
    background_color = color_map.get(background_color.lower(), "#FFFFFF")
    
    if msg.reply_to_message:
        if msg.reply_to_message.sticker:
            file_id = msg.reply_to_message.sticker.file_id
        elif msg.reply_to_message.photo:
            file_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.document:
            file_id = msg.reply_to_message.document.file_id
        else:
            msg.reply_text("I can't kang that.")
        
        kang_file = bot.get_file(file_id)
        kang_file.download('kangsticker.png')
        
        # Get user profile picture and name
        try:
            profile_picture = bot.get_user_profile_photos(user.id).photos[0][-1].file_id
            profile_photo = bot.get_file(profile_picture)
            profile_photo.download('profile_pic.jpg')
        except Exception as e:
            print("Error retrieving profile picture:", e)
            profile_photo = None

        # Set user name (handle symbols if any)
        name = user.first_name
        if user.last_name:
            name += " " + user.last_name
        name = escape_markdown(name)

        # Open the downloaded image for manipulation
        try:
            im = Image.open('kangsticker.png')
            if (im.width and im.height) < 512:
                size1 = im.width
                size2 = im.height
                if im.width > im.height:
                    scale = 512 / size1
                    size1new = 512
                    size2new = size2 * scale
                else:
                    scale = 512 / size2
                    size1new = size1 * scale
                    size2new = 512
                size1new = math.floor(size1new)
                size2new = math.floor(size2new)
                sizenew = (size1new, size2new)
                im = im.resize(sizenew)
            else:
                maxsize = (512, 512)
                im.thumbnail(maxsize)

            # Add background color customization
            im = Image.new('RGBA', im.size, background_color)
            im.paste(im, (0, 0), im)

            # Overlay profile picture and name
            if profile_photo:
                profile_image = Image.open('profile_pic.jpg').resize((50, 50))
                im.paste(profile_image, (10, 10))  # Place profile picture in the top-left corner

            # Add user's name in the same font
            draw = ImageDraw.Draw(im)
            try:
                font = ImageFont.truetype("arial.ttf", 24)  # Adjust as needed
            except IOError:
                font = ImageFont.load_default()
            
            draw.text((70, 10), name, fill="black", font=font)

            # Save the modified image
            im.save('kangsticker_modified.png', 'PNG')

            # Add sticker to the user's pack
            sticker_emoji = "🤔"  # You can get this from the message or set a default
            bot.add_sticker_to_set(user_id=user.id, name=packname,
                                    png_sticker=open('kangsticker_modified.png', 'rb'), emojis=sticker_emoji)

            msg.reply_text(f"Sticker successfully added to [pack](t.me/addstickers/{packname})\n"
                           f"Emoji is: {sticker_emoji}", parse_mode=ParseMode.MARKDOWN)

        except OSError as e:
            msg.reply_text("I can only kang images m8.")
            print(e)
            return
        except TelegramError as e:
            print(e)
            if e.message == "Internal Server Error: sticker set not found (500)":
                msg.reply_text("Sticker successfully added to [pack](t.me/addstickers/%s)" % packname +
                               "\nEmoji is:" + " " + sticker_emoji, parse_mode=ParseMode.MARKDOWN)
            elif e.message == "Stickers_too_much":
                msg.reply_text("Max packsize reached.")
            elif e.message == "Stickerset_invalid":
                makepack_internal(msg, user, open('kangsticker_modified.png', 'rb'), sticker_emoji, bot, packname, 0)
            print(e)
    else:
        msg.reply_text("Please reply to a sticker, or image to kang it!")

    if os.path.isfile("kangsticker_modified.png"):
        os.remove("kangsticker_modified.png")
    if os.path.isfile("profile_pic.jpg"):
        os.remove("profile_pic.jpg")

# Function to handle the original /kang command (no customization)
@run_async
def kangim(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message
    user = update.effective_user
    packname = f"a{str(user.id)}_by_{bot.username}"
    max_stickers = 120
    packname = check_pack_validity(bot, user, packname, max_stickers)

    if msg.reply_to_message:
        if msg.reply_to_message.sticker:
            file_id = msg.reply_to_message.sticker.file_id
        elif msg.reply_to_message.photo:
            file_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.document:
            file_id = msg.reply_to_message.document.file_id
        else:
            msg.reply_text("I can't kang that.")
        
        kang_file = bot.get_file(file_id)
        kang_file.download('kangsticker.png')

        # Get user profile picture and name (no color customization)
        try:
            profile_picture = bot.get_user_profile_photos(user.id).photos[0][-1].file_id
            profile_photo = bot.get_file(profile_picture)
            profile_photo.download('profile_pic.jpg')
        except Exception as e:
            print("Error retrieving profile picture:", e)
            profile_photo = None

        # Set user name (handle symbols if any)
        name = user.first_name
        if user.last_name:
            name += " " + user.last_name
        name = escape_markdown(name)

        # Open the downloaded image for manipulation
        try:
            im = Image.open('kangsticker.png')
            im = im.convert('RGBA')

            # Add background color from user without customization
            background_color = "#FFFFFF"
            im = Image.new('RGBA', im.size, background_color)
            im.paste(im, (0, 0), im)

            # Overlay profile picture and name
            if profile_photo:
                profile_image = Image.open('profile_pic.jpg').resize((50, 50))
                im.paste(profile_image, (10, 10))  # Place profile picture in the top-left corner

            # Add user's name in the default font
            draw = ImageDraw.Draw(im)
            try:
                font = ImageFont.truetype("arial.ttf", 24)  # Adjust as needed
            except IOError:
                font = ImageFont.load_default()
            
            draw.text((70, 10), name, fill="black", font=font)

            # Save the modified image
            im.save('kangsticker_modified.png', 'PNG')

            # Add sticker to the user's pack
            sticker_emoji = "🤔"
            bot.add_sticker_to_set(user_id=user.id, name=packname,
                                    png_sticker=open('kangsticker_modified.png', 'rb'), emojis=sticker_emoji)

            msg.reply_text(f"Sticker successfully added to [pack](t.me/addstickers/{packname})\n"
                           f"Emoji is: {sticker_emoji}", parse_mode=ParseMode.MARKDOWN)

        except OSError as e:
            msg.reply_text("I can only kang images m8.")
            print(e)
            return
        except TelegramError as e:
            print(e)
            if e.message == "Internal Server Error: sticker set not found (500)":
                msg.reply_text("Sticker successfully added to [pack](t.me/addstickers/%s)" % packname +
                               "\nEmoji is:" + " " + sticker_emoji, parse_mode=ParseMode.MARKDOWN)
            elif e.message == "Stickers_too_much":
                msg.reply_text("Max packsize reached.")
            elif e.message == "Stickerset_invalid":
                makepack_internal(msg, user, open('kangsticker_modified.png', 'rb'), sticker_emoji, bot, packname, 0)
            print(e)
    else:
        msg.reply_text("Please reply to a sticker, or image to kang it!")

    if os.path.isfile("kangsticker_modified.png"):
        os.remove("kangsticker_modified.png")
    if os.path.isfile("profile_pic.jpg"):
        os.remove("profile_pic.jpg")

# Adding the handlers to the dispatcher
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("kang", kangim, pass_args=True))
dispatcher.add_handler(CommandHandler("kangurl", kangurl, pass_args=True))
dispatcher.add_handler(CommandHandler("kangm", kangm, pass_args=True))

updater.start_polling(timeout=15, read_latency=4)
updater.idle()
