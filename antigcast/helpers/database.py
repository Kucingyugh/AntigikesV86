import datetime
from pytz import timezone
from dateutil.relativedelta import relativedelta
from antigcast.config import MONGO_DB_URI, DB_NAME
from motor.motor_asyncio import AsyncIOMotorClient

mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
db = mongo_client[DB_NAME]

userdb = db['USERS']
serchat = db['SERVEDCHATS']
actchat = db['ACTIVEDVEDCHATS']
blackword = db['BLACKWORDS']
owner = db['OWNERS']
exp = db['EXP']
globaldb = db['GLOBALMUTE']
mute_collection = db['GROUPMUTE']
sellers_collection = db['ADDSELLER']

#USERS
def new_user(id):
    return dict(
        id=id,
        join_date=datetime.date.today().isoformat(),
        ban_status=dict(
            is_banned=False,
            ban_duration=0,
            banned_on=datetime.date.max.isoformat(),
            ban_reason="",
        ),
    )


async def add_user(id):
    user = new_user(id)
    await userdb.insert_one(user)


async def is_user_exist(id):
    user = await userdb.find_one({"id": int(id)})
    return bool(user)


async def total_users_count():
    count = await userdb.count_documents({})
    return count


async def get_all_users():
    return userdb.find({})


async def delete_user(user_id):
    await userdb.delete_many({"id": int(user_id)})


async def remove_ban(id):
    ban_status = dict(
        is_banned=False,
        ban_duration=0,
        banned_on=datetime.date.max.isoformat(),
        ban_reason="",
    )
    await userdb.update_one({"id": id}, {"$set": {"ban_status": ban_status}})


async def ban_user(user_id, ban_duration, ban_reason):
    ban_status = dict(
        is_banned=True,
        ban_duration=ban_duration,
        banned_on=datetime.date.today().isoformat(),
        ban_reason=ban_reason,
    )
    await userdb.update_one({"id": user_id}, {"$set": {"ban_status": ban_status}})


async def get_ban_status(id):
    default = dict(
        is_banned=False,
        ban_duration=0,
        banned_on=datetime.date.max.isoformat(),
        ban_reason="",
    )
    user = await userdb.find_one({"id": int(id)})
    return user.get("ban_status", default)


async def get_all_banned_users():
    return userdb.find({"ban_status.is_banned": True})
    

# SERVED_CHATS
async def get_served_chats() -> list:
    servedchats = await serchat.find_one({"servedchat": "servedchat"})
    if not servedchats:
        return []
    return servedchats["servedchats"]


async def add_aserved_chat(trigger) -> bool:
    servedchats = await get_served_chats()
    servedchats.append(trigger)
    await serchat.update_one({"servedchat": "servedchat"}, {"$set": {"servedchats": servedchats}}, upsert=True)
    return True


async def rem_served_chat(trigger) -> bool:
    servedchats = await get_served_chats()
    servedchats.remove(trigger)
    await serchat.update_one({"servedchat": "servedchat"}, {"$set": {"servedchats": servedchats}}, upsert=True)
    return True
    

# ACTIVED_CHATS
async def get_actived_chats() -> list:
    acctivedchats = await actchat.find_one({"acctivedchat": "acctivedchat"})
    if not acctivedchats:
        return []
    return acctivedchats["acctivedchats"]

async def add_actived_chat(trigger, user_id, username) -> bool:
    acctivedchats = await get_actived_chats()
    if trigger not in acctivedchats:
        acctivedchats.append(trigger)
        await actchat.update_one(
            {"acctivedchat": "acctivedchat"},
            {"$set": {"acctivedchats": acctivedchats}},
            upsert=True
        )
        await set_chat_added_by(trigger, user_id, username)
        return True
    return False

async def rem_actived_chat(trigger) -> bool:
    acctivedchats = await get_actived_chats()
    if trigger in acctivedchats:
        acctivedchats.remove(trigger)
        await actchat.update_one(
            {"acctivedchat": "acctivedchat"},
            {"$set": {"acctivedchats": acctivedchats}},
            upsert=True
        )
        return True
    return False

async def set_chat_added_by(chat_id, user_id, username):
    await actchat.update_one(
        {'_id': chat_id},
        {'$set': {
            'added_by': {
                'user_id': user_id,
                'username': username
            }
        }},
        upsert=True
    )

async def get_added_by(chat_id):
    chat = await actchat.find_one({'_id': chat_id})
    if chat:
        return chat.get('added_by')
    return None


# BLACKLIST_WORD
async def get_bl_words() -> list:
    filters = await blackword.find_one({"filter": "filter"})
    if not filters:
        return []
    return filters["filters"]


async def add_bl_word(trigger) -> bool:
    x = trigger.lower()
    filters = await get_bl_words()
    filters.append(x)
    await blackword.update_one({"filter": "filter"}, {"$set": {"filters": filters}}, upsert=True)
    return True


async def remove_bl_word(trigger) -> bool:
    x = trigger.lower()
    filters = await get_bl_words()
    filters.remove(x)
    await blackword.update_one({"filter": "filter"}, {"$set": {"filters": filters}}, upsert=True)
    return True
    

# OWNER
async def get_owners() -> list:
    owners = await owner.find_one({"owner": "owner"})
    if not owners:
        return []
    return owners["owners"]


async def add_owner(trigger) -> bool:
    owners = await get_owners()
    owners.append(trigger)
    await owner.update_one({"owner": "owner"}, {"$set": {"owners": owners}}, upsert=True)
    return True


async def remove_owner(trigger) -> bool:
    owners = await get_owners()
    owners.remove(trigger)
    await owner.update_one({"owner": "owner"}, {"$set": {"owners": owners}}, upsert=True)
    return True
    

# EXPIRED DATE
async def get_expired_date(chat_id):
    group = await exp.find_one({'_id': chat_id})
    if group:
        return group.get('expire_date')
    return None

async def rem_expired_date(chat_id):
    await exp.update_one({"_id": chat_id}, {"$unset": {"expire_date": ""}}, upsert=True)

async def rem_expired(chat_id):
    await exp.delete_one({"_id": chat_id})

async def remove_expired():
    now = datetime.datetime.now(timezone("Asia/Jakarta"))
    async for group in exp.find({"expire_date": {"$lt": now}}):
        await rem_expired(group["_id"])
        await rem_actived_chat(group["_id"])
        gc = group["_id"]
        exptext = f"Masa Aktif {gc} Telah Habis dan telah dihapus dari database."
        print(exptext)

async def set_expired_date(chat_id, expire_date, user_id, username):
    await exp.update_one(
        {'_id': chat_id},
        {'$set': {
            'expire_date': expire_date,
            'added_by': {
                'user_id': user_id,
                'username': username
            }
        }},
        upsert=True
    )


# GLOBAL_DELETE
async def get_muted_users() -> list:
    mutedusers = await globaldb.find_one({"muteduser": "muteduser"})
    if not mutedusers:
        return []
    return mutedusers["mutedusers"]


async def mute_user(uid_id) -> bool:
    mutedusers = await get_muted_users()
    mutedusers.append(uid_id)
    await globaldb.update_one({"muteduser": "muteduser"}, {"$set": {"mutedusers": mutedusers}}, upsert=True)
    return True


async def unmute_user(uid_id) -> bool:
    mutedusers = await get_muted_users()
    mutedusers.remove(uid_id)
    await globaldb.update_one({"muteduser": "muteduser"}, {"$set": {"mutedusers": mutedusers}}, upsert=True)
    return True


# GROUP_MUTE
async def mute_user_in_group(group_id, user_id, user_name, issuer_id, issuer_name):
    await mute_collection.update_one(
        {'group_id': group_id},
        {
            '$set': {
                f'user_data.{user_id}': {
                    'name': user_name,
                    'muted_by': {
                        'id': issuer_id,
                        'name': issuer_name
                    }
                }
            }
        },
        upsert=True
    )

async def unmute_user_in_group(group_id, user_id):
    await mute_collection.update_one(
        {'group_id': group_id},
        {'$unset': {f'user_data.{user_id}': ""}}  # Remove user from dictionary
    )

async def get_muted_users_in_group(group_id):
    doc = await mute_collection.find_one({'group_id': group_id})
    if doc and 'user_data' in doc:
        return doc['user_data']  # Return dictionary of user ID and associated data
    return {}

async def clear_muted_users_in_group(group_id):
    await mute_collection.update_one(
        {'group_id': group_id},
        {'$unset': {'user_data': ""}}  # Remove the entire user_data field
    )


#SELLER
async def add_seller(seller_id, user_id, username):
    try:
        await sellers_collection.update_one(
            {'_id': seller_id},
            {'$set': {
                'added_by': {
                    'user_id': user_id,
                    'username': username
                },
                'added_at': datetime.datetime.now()
            }},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error adding seller: {e}")
        return False


async def rem_seller(seller_id):
    try:
        result = await sellers_collection.delete_one({'_id': seller_id})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error removing seller: {e}")
        return False


async def list_sellers():
    try:
        sellers = []
        async for seller in sellers_collection.find():
            sellers.append(seller)
        return sellers
    except Exception as e:
        print(f"Error listing sellers: {e}")
        return []
