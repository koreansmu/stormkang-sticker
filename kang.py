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
ʀᴀᴅʜᴇ ʀᴀᴅʜᴇ ! ɪ'ᴍ {}, ᴀɴᴅ ᴛʜɪs ɪs ʙɪʟʟᴀ ᴋᴀɴɢ sᴛɪᴄᴋᴇʀ ʙᴏᴛ ᴡʜɪᴄʜ ᴀʟʟᴏᴡs ʏᴏᴜ ᴛᴏ ᴄʀᴇᴀᴛᴇ ᴀ sᴛɪᴄᴋᴇʀ ᴘᴀᴄᴋ ғʀᴏᴍ ᴏᴛʜᴇʀ sᴛɪᴄᴋᴇʀs, ɪᴍᴀɢᴇs ᴀɴᴅ ᴅᴏᴄᴜᴍᴇɴᴛs! 
ɪ ᴏɴʟʏ ʜᴀᴠᴇ ᴀ ғᴇᴡ ᴄᴏᴍᴍᴀɴᴅs sᴏ ɪ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀ ʜᴇʟᴘ ᴍᴇɴᴜ ᴏʀ ᴀɴʏᴛʜɪɴɢ ʟɪᴋᴇ ᴛʜᴀᴛ. ʏᴏᴜ ᴄᴀɴ ᴀʟsᴏ ᴄᴀʟʟ ᴏᴜᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ғᴏʀ ᴛʜᴇ ʜᴇʟᴘ ᴏғ ʙᴏᴛ [ʜᴇʀᴇ](https://t.me/interstellarXd)
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

        # Download the sticker/image
        kang_file = bot.get_file(file_id)
        kang_file.download('kangsticker.png')

        # Get the user's profile picture and name using Pyrogram
        try:
            profile_photos = pyrogram_client.get_users_profile_photos(user.id)
            if profile_photos.total_count > 0:
                profile_picture = pyrogram_client.get_file(profile_photos.photos[0][-1].file_id)
                profile_picture.download('profile_pic.jpg')
            else:
                msg.reply_text("I couldn't retrieve your profile picture.")
                return

            user_name = user.first_name if user.first_name else "No Name"

        except Exception as e:
            msg.reply_text(f"An error occurred while fetching your profile picture or name: {str(e)}")
            return

        # Add the user's profile photo and name to the sticker
        try:
            sticker_image = Image.open('kangsticker.png')
            profile_image = Image.open('profile_pic.jpg')

            profile_image = profile_image.resize((100, 100))

            sticker_image.paste(profile_image, (sticker_image.width - 110, sticker_image.height - 110))

            draw = ImageDraw.Draw(sticker_image)
            font = ImageFont.load_default()
            draw.text((10, 10), user_name, font=font, fill="white")

            sticker_image.save('kangsticker_with_profile.png', "PNG")

            sticker_emoji = args[0] if args else "🤔"
            bot.add_sticker_to_set(user_id=user.id, name=packname,
                                    png_sticker=open('kangsticker_with_profile.png', 'rb'), emojis=sticker_emoji)

            if os.path.exists('profile_pic.jpg'):
                os.remove('profile_pic.jpg')
            if os.path.exists('kangsticker_with_profile.png'):
                os.remove('kangsticker_with_profile.png')

            msg.reply_text(f"Sticker successfully added to [pack](t.me/addstickers/{packname})" +
                            f"\nEmoji is: {sticker_emoji}", parse_mode=ParseMode.MARKDOWN)

        except OSError as e:
            msg.reply_text("I can only kang images with valid formats.")
            print(e)
            return
    else:
        msg.reply_text("Please reply to a sticker, or image to kang it!")

# /kangurl Command (to create a sticker pack from an image URL)
@run_async
def kangurl(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message
    user = update.effective_user
    if not args:
        msg.reply_text("Please provide a URL.")
        return
    
    image_url = args[0]
    
    try:
        # Download image from the provided URL
        file_path = 'kangsticker_from_url.png'
        urllib.urlretrieve(image_url, file_path)

        # Create a sticker pack name
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

        # Add the sticker from the URL to the pack
        bot.add_sticker_to_set(user_id=user.id, name=packname,
                               png_sticker=open(file_path, 'rb'), emojis="🤔")

        msg.reply_text(f"Sticker successfully added to [pack](t.me/addstickers/{packname})" +
                        f"\nEmoji is: 🤔", parse_mode=ParseMode.MARKDOWN)

        # Clean up
        if os.path.isfile(file_path):
            os.remove(file_path)

    except Exception as e:
        msg.reply_text(f"An error occurred: {str(e)}")
        print(e)

# /kangim Command (to create a sticker pack with image and user details)
run_async
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

    # Handle custom background and text overlay
    background_color = args[0] if args else "white"
    try:
        profile_photos = pyrogram_client.get_users_profile_photos(user.id)
        if profile_photos.total_count > 0:
            profile_picture = pyrogram_client.get_file(profile_photos.photos[0][-1].file_id)
            profile_picture.download('profile_pic.jpg')
        else:
            msg.reply_text("I couldn't retrieve your profile picture.")
            return

        profile_image = Image.open('profile_pic.jpg')

        bg = Image.new("RGB", (512, 512), background_color)
        profile_image = profile_image.resize((100, 100))
        bg.paste(profile_image, (0, 0))

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


# /kangm Command (customized for user with their profile image and name on the sticker)
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

    # Customization options (background color, text, etc.)
    background_color = args[0] if args else "white"  # Default to white if no color is provided

    try:
        # Fetch profile picture
        profile_photos = pyrogram_client.get_users_profile_photos(user.id)
        if profile_photos.total_count > 0:
            # Download the profile picture
            profile_picture = pyrogram_client.get_file(profile_photos.photos[0][-1].file_id)
            profile_picture.download('profile_pic.jpg')
        else:
            msg.reply_text("Could not retrieve your profile picture.")
            return

        profile_image = Image.open('profile_pic.jpg')
        bg = Image.new("RGB", (512, 512), background_color)

        # Resize the profile image and paste it on the background
        profile_image = profile_image.resize((100, 100))
        bg.paste(profile_image, (0, 0))

        # Draw text (user's name)
        draw = ImageDraw.Draw(bg)
        font = ImageFont.load_default()
        name = user.first_name
        draw.text((10, 10), name, font=font, fill=(255, 255, 255))

        bg.save('kangm_sticker.png', "PNG")
        bot.add_sticker_to_set(user_id=user.id, name=packname,
                               png_sticker=open('kangm_sticker.png', 'rb'), emojis="🤔")

        msg.reply_text(f"Sticker successfully added to [pack](t.me/addstickers/{packname})" +
                        f"\nEmoji is: 🤔", parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        msg.reply_text(f"An error occurred: {str(e)}")
        print(e)

    # Clean up
    if os.path.isfile("kangm_sticker.png"):
        os.remove("kangm_sticker.png")
    if os.path.isfile("profile_pic.jpg"):
        os.remove("profile_pic.jpg")


# Adding handlers to the dispatcher
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("kang", kang, pass_args=True))
dispatcher.add_handler(CommandHandler("kangurl", kangurl, pass_args=True))
dispatcher.add_handler(CommandHandler("kangim", kangim, pass_args=True))
dispatcher.add_handler(CommandHandler("kangm", kangm, pass_args=True))

updater.start_polling(timeout=15, read_latency=4)
updater.idle()
