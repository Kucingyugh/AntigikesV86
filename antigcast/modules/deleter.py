import asyncio
from antigcast import Bot
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait

from antigcast.config import *
from antigcast.helpers.tools import *
from antigcast.helpers.admins import *
from antigcast.helpers.message import *
from antigcast.helpers.database import *

def get_full_name(user):
    return f"{user.first_name or ''} {user.last_name or ''}".strip()

@Bot.on_message(filters.command("bl") & ~filters.private & Admin)
async def tambah_ke_blacklist(app: Bot, message: Message):
    trigger = get_arg(message)
    if not trigger and message.reply_to_message:
        trigger = message.reply_to_message.text or message.reply_to_message.caption

    if not trigger:
        await message.reply("Error: Tidak ada kata yang diberikan untuk blacklist.")
        return

    user_info = {
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "name": get_full_name(message.from_user),
        "group_name": message.chat.title,
        "chat_id": message.chat.id
    }

    response = await message.reply(
        f"<blockquote>Menambahkan {trigger} ke dalam blacklist oleh {user_info['name']} (@{user_info['username']}) di grup {user_info['group_name']}...</blockquote>",
    )
    try:
        await add_bl_word(trigger.lower(), user_info)
        await response.edit(
            f"<blockquote>{trigger} berhasil ditambahkan ke dalam blacklist oleh {user_info['name']} (@{user_info['username']}) di grup {user_info['group_name']}.</blockquote>",
        )
    except Exception as e:
        await response.edit(f"Error: `{e}`")

    await asyncio.sleep(3)
    await response.delete()
    await message.delete()

@Bot.on_message(filters.command("delbl") & ~filters.private & Admin)
async def hapus_dari_blacklist(app: Bot, message: Message):
    trigger = get_arg(message)
    if not trigger and message.reply_to_message:
        trigger = message.reply_to_message.text or message.reply_to_message.caption

    if not trigger:
        await message.reply("Error: Tidak ada kata yang diberikan untuk dihapus dari blacklist.")
        return

    user_info = {
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "name": get_full_name(message.from_user),
        "group_name": message.chat.title,
        "chat_id": message.chat.id
    }

    response = await message.reply(
        f"<blockquote>Menghapus {trigger} dari blacklist oleh {user_info['name']} (@{user_info['username']}) di grup {user_info['group_name']}...</blockquote>",
    )
    try:
        await remove_bl_word(trigger.lower(), user_info["chat_id"])
        await response.edit(
            f"<blockquote>{trigger} berhasil dihapus dari blacklist oleh {user_info['name']} (@{user_info['username']}) di grup {user_info['group_name']}.</blockquote>",
        )
    except ValueError as e:
        await response.edit(f"Error: `{e}`")
    except Exception as e:
        await response.edit(f"Error: `{e}`")

    await asyncio.sleep(3)
    await response.delete()
    await message.delete()

@Bot.on_message(filters.command("listbl") & ~filters.private & Admin)
async def daftar_blacklist(app: Bot, message: Message):
    try:
        chat_id = message.chat.id
        bl_words = await get_bl_words(chat_id)
        if not bl_words:
            await message.reply("Tidak ada kata-kata yang di-blacklist.")
            return

        bl_list = "\n".join([f"{idx + 1}. {word}" for idx, word in enumerate(bl_words)])
        response_text = f"<blockquote>**Daftar kata-kata yang di-blacklist di grup ini ({len(bl_words)} kata):**\n{bl_list}</blockquote>"
        await message.reply(response_text)
    except Exception as e:
        await message.reply(f"Error: `{e}`")

@Bot.on_message(filters.command("listblgroups") & ~filters.private & Admin)
async def daftar_grup_blacklist(app: Bot, message: Message):
    try:
        bl_groups = await get_bl_groups()
        if not bl_groups:
            await message.reply("Tidak ada grup yang menggunakan perintah blacklist.")
            return

        group_list = "\n".join([f"{idx + 1}. {group['group_name']} (ID: {group['chat_id']})" for idx, group in enumerate(bl_groups)])
        response_text = f"<blockquote>**Daftar grup yang menggunakan perintah blacklist ({len(bl_groups)} grup):**\n{group_list}</blockquote>"
        await message.reply(response_text)
    except Exception as e:
        await message.reply(f"Error: `{e}`")

@Bot.on_message(filters.text & ~filters.private & Member & Gcast)
async def deletermessag(app: Bot, message: Message):
    text = "<blockquote>Maaf, Grup ini tidak terdaftar di dalam list. Silahkan hubungi @Zenithnewbie Untuk mendaftarkan Group Anda.\n\n**Bot akan meninggalkan group!**</blockquote>"
    chat = message.chat.id
    chats = await get_actived_chats()
    if chat not in chats:
        await message.reply(text=text)
        await asyncio.sleep(5)
        try:
            await app.leave_chat(chat)
        except Exception as e:
            print(e)
        return

    try:
        await message.delete()
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.delete()
    except Exception as e:
        print(e)

#DELETE BL
@Bot.on_message(filters.text & ~filters.private)
async def cek_blacklist(app: Bot, message: Message):
    chat_id = message.chat.id
    text = message.text.lower() if message.text else ""
    
    # Dapatkan daftar kata yang di-blacklist untuk grup ini
    bl_words = await get_bl_words(chat_id)
    if not bl_words:
        return
    
    # Periksa apakah pesan mengandung kata yang di-blacklist
    for word in bl_words:
        if word in text:
            try:
                await message.delete()
                return
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await message.delete()
            except Exception as e:
                print(e)
                return
