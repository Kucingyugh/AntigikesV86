import asyncio
from antigcast import Bot
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, PeerIdInvalid, UserNotParticipant
from pyrogram.enums import ChatMemberStatus as STATUS

from antigcast.helpers.tools import extract
from antigcast.helpers.database import *

async def is_admin_or_owner(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in [STATUS.OWNER, STATUS.ADMINISTRATOR]
    except (FloodWait, UserNotParticipant):
        return False
    except:
        return False

@Bot.on_message(filters.command("pl") & ~filters.private)
async def mute_handler(app: Bot, message: Message):
    if not await is_admin_or_owner(app, message.chat.id, message.from_user.id):
        return await message.reply_text("Kamu harus menjadi admin untuk menggunakan perintah ini.")

    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text("Berikan saya ID atau nama pengguna yang ingin di mute.")

    if message.reply_to_message:
        user = message.reply_to_message.from_user
    else:
        user_input = message.command[1]
        try:
            if user_input.isdigit():
                user = await app.get_users(int(user_input))
            else:
                user = await app.get_users(user_input)
        except PeerIdInvalid:
            return await message.reply_text("Tidak dapat menemukan pengguna dengan nama tersebut.")

    user_id = user.id
    group_id = message.chat.id
    issuer_id = message.from_user.id
    issuer_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}"

    if user_id == issuer_id:
        return await message.reply_text("Kamu tidak bisa mute diri sendiri.")
    elif user_id == app.me.id:
        return await message.reply_text("Kamu tidak bisa mute bot.")

    if await is_admin_or_owner(app, message.chat.id, user_id):
        return await message.reply_text("Kamu tidak bisa mute admin atau owner.")

    xxnx = await message.reply("`Menambahkan pengguna ke dalam daftar mute...`")

    muted = await get_muted_users_in_group(group_id)
    if any(u['user_id'] == user_id for u in muted):
        await xxnx.edit("**Pengguna ini sudah ada di daftar mute.**")
        await asyncio.sleep(10)
        await xxnx.delete()
        return

    try:
        user_name = f"{user.first_name or ''} {user.last_name or ''}"
        await mute_user_in_group(group_id, user_id, issuer_id, issuer_name)
        await xxnx.edit(
            f"<b><blockquote>Pengguna berhasil di mute</blockquote>\n- Nama: {user_name}\n- User ID: <code>{user_id}</code>\n- Di-mute oleh: {issuer_name}</b>"
        )
        await asyncio.sleep(10)
        await xxnx.delete()
    except Exception as e:
        await xxnx.edit(f"**Gagal mute pengguna:** `{e}`")

@Bot.on_message(filters.command("ungdel") & ~filters.private)
async def unmute_handler(app: Bot, message: Message):
    if not await is_admin_or_owner(app, message.chat.id, message.from_user.id):
        return await message.reply_text("Kamu harus menjadi admin untuk menggunakan perintah ini.")

    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text("Berikan saya ID atau nama pengguna yang ingin di unmute.")

    if message.reply_to_message:
        user = message.reply_to_message.from_user
    else:
        user_input = message.command[1]
        try:
            if user_input.isdigit():
                user = await app.get_users(int(user_input))
            else:
                user = await app.get_users(user_input)
        except PeerIdInvalid:
            return await message.reply_text("Tidak dapat menemukan pengguna dengan nama tersebut.")

    user_id = user.id
    group_id = message.chat.id
    issuer_id = message.from_user.id
    issuer_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}"

    if user_id == issuer_id:
        return await message.reply_text("Kamu tidak bisa unmute diri sendiri.")
    elif user_id == app.me.id:
        return await message.reply_text("Kamu tidak bisa unmute bot.")

    xxnx = await message.reply("`Menghapus pengguna dari daftar mute...`")

    muted = await get_muted_users_in_group(group_id)
    if not any(u['user_id'] == user_id for u in muted):
        await xxnx.edit("**Pengguna ini tidak ada di daftar mute.**")
        await asyncio.sleep(10)
        await xxnx.delete()
        return

    try:
        await unmute_user_in_group(group_id, user_id)
        await xxnx.edit(
            f"<blockquote>**Pengguna berhasil di unmute**\n- Nama: {user.first_name}\n- User ID: `{user_id}`</blockquote>"
        )
        await asyncio.sleep(10)
        await xxnx.delete()
        await message.delete()
    except Exception as e:
        await xxnx.edit(f"**Gagal unmute pengguna:** `{e}`")

@Bot.on_message(filters.command("gmuted") & ~filters.private)
async def muted(app: Bot, message: Message):
    if not await is_admin_or_owner(app, message.chat.id, message.from_user.id):
        return await message.reply_text("Kamu harus menjadi admin untuk menggunakan perintah ini.")

    group_id = message.chat.id
    kons = await get_muted_users_in_group(group_id)

    if not kons:
        return await message.reply("**Belum ada pengguna yang di mute.**")

    resp = await message.reply("**Memuat database...**")

    header_msg = "<blockquote>**Daftar pengguna yang di mute**\n\n</blockquote>"
    msg = header_msg
    num = 0
    max_length = 4096  # Maximum message length allowed by Telegram

    for user in kons:
        num += 1
        user_id = user['user_id']
        try:
            user_info = await app.get_users(int(user_id))
            user_name = f"{user_info.first_name or ''} {user_info.last_name or ''}"
        except PeerIdInvalid:
            user_name = "Tidak dikenal"
        muted_by_name = user['muted_by']['name']
        user_info_msg = f"<blockquote>**{num}. {user_name}**\n└ User ID: `{user_id}`\n└ Di-mute oleh: {muted_by_name}\n\n</blockquote>"

        if len(msg) + len(user_info_msg) > max_length:
            await message.reply(msg, disable_web_page_preview=True)
            msg = header_msg + user_info_msg
        else:
            msg += user_info_msg

    await message.reply(msg, disable_web_page_preview=True)
    await resp.delete()

@Bot.on_message(filters.command("clearmuted") & ~filters.private)
async def clear_muted(app: Bot, message: Message):
    if not await is_admin_or_owner(app, message.chat.id, message.from_user.id):
        return await message.reply_text("Kamu harus menjadi admin untuk menggunakan perintah ini.")

    group_id = message.chat.id
    muted_users = await get_muted_users_in_group(group_id)

    if not muted_users:
        return await message.reply("**Tidak ada pengguna yang di mute untuk dihapus.**")

    await clear_muted_users_in_group(group_id)
    await message.reply("**Semua pengguna yang di mute telah dihapus untuk grup ini.**")

@Bot.on_message(filters.group & ~filters.private, group=54)
async def delete_muted_messages(app: Bot, message: Message):
    if message.from_user is None:
        return

    user_id = message.from_user.id
    group_id = message.chat.id
    group_name = message.chat.title

    muted_users = await get_muted_users_in_group(group_id)
    if any(u['user_id'] == user_id for u in muted_users):
        print(f"Pesan dari pengguna yang di-mute: {user_id} di grup {group_name} ({group_id})")
        try:
            await message.delete()
            print(f"Pesan dari pengguna yang di-mute {user_id} di grup {group_name} ({group_id}) berhasil dihapus")
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await message.delete()
            print(f"Pesan dari pengguna yang di-mute {user_id} di grup {group_name} ({group_id}) berhasil dihapus setelah menunggu {e.value} detik")
        except Exception as e:
            print(f"Tidak dapat menghapus pesan dari pengguna yang di-mute: {user_id} di grup {group_name} ({group_id}). Error: {e}")
