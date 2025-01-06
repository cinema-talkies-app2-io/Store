import re
from pyrogram import filters, Client, enums
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, UsernameInvalid, UsernameNotModified
from config import ADMINS, LOG_CHANNEL, PUBLIC_FILE_STORE, WEBSITE_URL, WEBSITE_URL_MODE
from plugins.database import unpack_new_file_id
from plugins.users_api import get_user, get_short_link
import os
import json
import base64
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def allowed(_, __, message):
    if PUBLIC_FILE_STORE:
        return True
    if message.from_user and message.from_user.id in ADMINS:
        return True
    return False

@Client.on_message((filters.document | filters.video | filters.audio | filters.text) & filters.private & filters.create(allowed))
async def incoming_gen_link(bot, message):
    username = (await bot.get_me()).username
    file_type = message.media if message.media else 'text'
    
    if file_type == 'text':
        file_id = str(message.message_id)
    else:
        file_id, ref = unpack_new_file_id((getattr(message, file_type.value)).file_id)
    
    string = 'msg_' if file_type == 'text' else 'file_'
    string += file_id
    outstr = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
    user_id = message.from_user.id
    user = await get_user(user_id)
    
    if WEBSITE_URL_MODE:
        share_link = f"{WEBSITE_URL}?Tech_VJ={outstr}"
    else:
        share_link = f"https://t.me/{username}?start={outstr}"
    
    if user["base_site"] and user["shortener_api"]:
        short_link = await get_short_link(user, share_link)
        await message.reply(f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🖇️ sʜᴏʀᴛ ʟɪɴᴋ :- {short_link}</b>")
    else:
        await message.reply(f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🔗 ᴏʀɪɢɪɴᴀʟ ʟɪɴᴋ :- {share_link}</b>")

@Client.on_message(filters.command(['link', 'plink']) & filters.create(allowed))
async def gen_link_s(bot, message):
    username = (await bot.get_me()).username
    replied = message.reply_to_message
    if not replied:
        return await message.reply('Reply to a message to get a shareable link.')
    
    file_type = replied.media if replied.media else 'text'
    
    if file_type != 'text' and file_type not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.AUDIO, enums.MessageMediaType.DOCUMENT]:
        return await message.reply("**ʀᴇᴘʟʏ ᴛᴏ ᴀ sᴜᴘᴘᴏʀᴛᴇᴅ ᴍᴇᴅɪᴀ ᴏʀ ᴛᴇxᴛ ᴍᴇssᴀɢᴇ**")
    
    if message.has_protected_content and message.chat.id not in ADMINS:
        return await message.reply("Protected content can't be shared.")
    
    if file_type == 'text':
        file_id = str(replied.message_id)
    else:
        file_id, ref = unpack_new_file_id((getattr(replied, file_type.value)).file_id)
    
    string = 'msg_' if file_type == 'text' else 'file_'
    string += file_id
    outstr = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
    user_id = message.from_user.id
    user = await get_user(user_id)
    
    if WEBSITE_URL_MODE:
        share_link = f"{WEBSITE_URL}?Tech_VJ={outstr}"
    else:
        share_link = f"https://t.me/{username}?start={outstr}"
    
    if user["base_site"] and user["shortener_api"]:
        short_link = await get_short_link(user, share_link)
        await message.reply(f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🖇️ sʜᴏʀᴛ ʟɪɴᴋ :- {short_link}</b>")
    else:
        await message.reply(f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🔗 ᴏʀɪɢɪɴᴀʟ ʟɪɴᴋ :- {share_link}</b>")

@Client.on_message(filters.command(['batch', 'pbatch']) & filters.create(allowed))
async def gen_link_batch(bot, message):
    username = (await bot.get_me()).username
    if " " not in message.text:
        return await message.reply("Use correct format.\nExample /batch https://t.me/vj_botz/10 https://t.me/vj_botz/20.")
    links = message.text.strip().split(" ")
    if len(links) != 3:
        return await message.reply("Use correct format.\nExample /batch https://t.me/vj_botz/10 https://t.me/vj_botz/20.")
    
    cmd, first, last = links
    regex = re.compile("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
    match = regex.match(first)
    if not match:
        return await message.reply('Invalid link')
    
    f_chat_id = match.group(4)
    f_msg_id = int(match.group(5))
    l_msg_id = int(regex.match(last).group(5))
    
    try:
        chat_id = (await bot.get_chat(f_chat_id)).id
    except Exception as e:
        return await message.reply(f'Error - {e}')
    
    outlist = []
    async for msg in bot.iter_messages(f_chat_id, l_msg_id, f_msg_id):
        file_type = msg.media if msg.media else 'text'
        file = getattr(msg, file_type.value, None) if file_type != 'text' else None
        caption = getattr(msg, 'caption', '') or msg.text if file_type == 'text' else ''
        
        if file or file_type == 'text':
            outlist.append({
                "file_id": file.file_id if file else str(msg.message_id),
                "caption": caption,
                "title": getattr(file, "file_name", "") if file else '',
                "size": getattr(file, "file_size", 0) if file else 0,
            })
    
    with open(f"batchmode_{message.from_user.id}.json", "w+") as out:
        json.dump(outlist, out)
    await bot.send_document(LOG_CHANNEL, f"batchmode_{message.from_user.id}.json", caption="Batch Generated.")
