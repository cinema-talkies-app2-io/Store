import logging, asyncio, os, re, random, pytz, aiohttp, requests, string, json, http.client
from datetime import date, datetime, timedelta
from config import SHORTLINK_API, SHORTLINK_URL
from shortzy import Shortzy

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
TOKENS = {}
VERIFIED = {}

async def get_verify_shorted_link(link):
    if SHORTLINK_URL == "api.shareus.io":
        url = f'https://{SHORTLINK_URL}/easy_api'
        params = {
            "key": SHORTLINK_API,
            "link": link,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, raise_for_status=True, ssl=False) as response:
                    data = await response.text()
                    return data
        except Exception as e:
            logger.error(e)
            return link
    else:
  #      response = requests.get(f"https://{SHORTLINK_URL}/api?api={SHORTLINK_API}&url={link}")
 #       data = response.json()
  #      if data["status"] == "success" or rget.status_code == 200:
   #         return data["shortenedUrl"]
        shortzy = Shortzy(api_key=SHORTLINK_API, base_site=SHORTLINK_URL)
        link = await shortzy.convert(link)
        return link

async def check_token(bot, userid, token):
    user = await bot.get_users(userid)
    if user.id in TOKENS.keys():
        TKN = TOKENS[user.id]
        if token in TKN.keys():
            is_used = TKN[token]
            if is_used == True:
                return False
            else:
                return True
    else:
        return False

async def get_token(bot, userid, link):
    user = await bot.get_users(userid)
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=7))
    TOKENS[user.id] = {token: False}
    link = f"{link}verify-{user.id}-{token}"
    shortened_verify_url = await get_verify_shorted_link(link)
    return str(shortened_verify_url)

async def verify_user(bot, userid, token):
    user = await bot.get_users(userid)
    TOKENS[user.id] = {token: True}
    tz = pytz.timezone('Asia/Kolkata')
    today = date.today()
    VERIFIED[user.id] = str(today)

async def check_verification(bot, userid):
    try:
        user = await bot.get_users(userid)
        if not await db.is_user_exist(user.id):
            await db.add_user(user.id, user.first_name)
            await bot.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(user.id, user.mention))
        
        tz = pytz.timezone('Asia/Kolkata')
        today = date.today()

        if user.id in VERIFIED.keys():
            EXP = VERIFIED[user.id]
            years, month, day = map(int, EXP.split('-'))
            comp = date(years, month, day)
            comp_with_extra_time = comp + timedelta(days=1)  # Add 1 day
            
            if comp_with_extra_time >= today:
                remaining_time = comp_with_extra_time - today
                days_remaining = remaining_time.days
                hours_remaining = remaining_time.seconds // 3600
                minutes_remaining = (remaining_time.seconds % 3600) // 60
                seconds_remaining = remaining_time.seconds % 60

                remaining_time_str = (f"{days_remaining} days, "
                                      f"{hours_remaining} hours, "
                                      f"{minutes_remaining} minutes, "
                                      f"{seconds_remaining} seconds remaining")
                
                # You can send this information to the user or log it
                #await bot.send_message(user.id, f"Your verification is valid for {remaining_time_str}.")
                
                return True
            else:
              #  await bot.send_message(user.id, "Your verification has expired.")
                return False
        else:
            return False

    except Exception as e:
        # Handle exceptions (e.g., log them)
        print(f"An error occurred: {e}")
        return False
