import time
import os
import re
import random
import asyncio

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.errors.exceptions.not_acceptable_406 import ChannelPrivate
from pyrogram.errors.exceptions.flood_420 import SlowmodeWait
from youtubesearchpython.__future__ import VideosSearch

import config
from AnonXMusic import app
from AnonXMusic.misc import _boot_
from AnonXMusic.plugins.sudo.sudoers import sudoers_list
from AnonXMusic.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
    blacklist_chat,
)
from AnonXMusic.utils.decorators.language import LanguageStart
from AnonXMusic.utils.formatters import get_readable_time
from AnonXMusic.utils.inline import help_pannel, private_panel, start_panel
from config import BANNED_USERS, LOGGER_ID
from strings import get_string


# ================== GROUP COUNTER STORAGE ==================

GROUP_FILE = "groups.txt"

def read_groups():
    if not os.path.exists(GROUP_FILE):
        return set()
    with open(GROUP_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def add_group(chat_id: int):
    gid = str(chat_id)
    groups = read_groups()
    if gid not in groups:
        with open(GROUP_FILE, "a") as f:
            f.write(gid + "\n")

def remove_group(chat_id: int):
    gid = str(chat_id)
    groups = read_groups()
    if gid in groups:
        groups.remove(gid)
        with open(GROUP_FILE, "w") as f:
            for g in groups:
                f.write(g + "\n")

# ===========================================================



# ================== /start PRIVATE =========================

@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):

    await add_served_user(message.from_user.id)

    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]

        if name.startswith("help"):
            keyboard = help_pannel(_)
            await message.reply_sticker("CAACAgUAAx0CdQO5IgACMTplUFOpwDjf-UC7pqVt9uG659qxWQACfQkAAghYGFVtSkRZ5FZQXDME")
            return await message.reply_photo(
                photo=random.choice(config.START_IMG_URL),
                caption=_["help_1"].format(config.SUPPORT_CHAT),
                reply_markup=keyboard,
            )

        if name.startswith("sud"):
            await sudoers_list(client=client, message=message, _=_)
            return

        if name.startswith("inf"):
            m = await message.reply_text("🔎")
            query = name.replace("info_", "", 1)
            query = f"https://www.youtube.com/watch?v={query}"
            results = VideosSearch(query, limit=1)

            for result in (await results.next())["result"]:
                title = result["title"]
                duration = result["duration"]
                views = result["viewCount"]["short"]
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                channellink = result["channel"]["link"]
                channel = result["channel"]["name"]
                link = result["link"]
                published = result["publishedTime"]

            searched_text = _["start_6"].format(
                title, duration, views, published, channellink, channel, app.mention
            )

            key = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text=_["S_B_8"], url=link),
                        InlineKeyboardButton(text=_["S_B_9"], url=config.SUPPORT_CHAT),
                    ],
                ]
            )

            await m.delete()
            return await app.send_photo(
                chat_id=message.chat.id,
                photo=thumbnail,
                caption=searched_text,
                reply_markup=key,
            )

    # Normal Start
    out = private_panel(_)
    await message.reply_sticker("CAACAgUAAx0CdQO5IgACMTplUFOpwDjf-UC7pqVt9uG659qxWQACfQkAAghYGFVtSkRZ5FZQXDME")
    return await message.reply_photo(
        photo=random.choice(config.START_IMG_URL),
        caption=_["start_2"].format(message.from_user.mention, app.mention),
        reply_markup=InlineKeyboardMarkup(out),
    )



# ================== /start GROUP ===========================

@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):

    out = start_panel(_)
    uptime = int(time.time() - _boot_)

    try:
        await message.reply_photo(
            photo=random.choice(config.START_IMG_URL),
            caption=_["start_1"].format(app.mention, get_readable_time(uptime)),
            reply_markup=InlineKeyboardMarkup(out),
        )
        await add_served_chat(message.chat.id)
    except ChannelPrivate:
        pass


# ================== WELCOME & BOT JOIN =====================

@app.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    for member in message.new_chat_members:

        # When bot joins a new group -> SAVE GROUP ID
        if member.id == app.id:
            add_group(message.chat.id)

        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)

            if member.id == app.id:
                out = start_panel(_)
                await message.reply_photo(
                    photo=random.choice(config.START_IMG_URL),
                    caption=_["start_3"].format(
                        message.from_user.first_name,
                        app.mention,
                        message.chat.title,
                        app.mention,
                    ),
                    reply_markup=InlineKeyboardMarkup(out),
                )
                await add_served_chat(message.chat.id)
                await message.stop_propagation()

        except Exception as ex:
            print(ex)



# ================== TRACK BOT LEAVE ========================

@app.on_chat_member_updated()
async def track_group_leave(client, update):
    try:
        old = update.old_chat_member
        new = update.new_chat_member

        if old and new:
            if old.user.id == app.id and new.status in ["left", "kicked"]:
                remove_group(update.chat.id)
    except:
        pass



# ================== /groups COMMAND ========================

@app.on_message(filters.command("groups") & filters.private)
async def show_groups(client, message: Message):
    groups = read_groups()
    await message.reply_text(f"✅ Total Groups: {len(groups)}")
