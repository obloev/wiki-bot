import json
import logging
import wikipedia
from aiogram.utils.exceptions import MessageIsTooLong, BadRequest
from wikipedia import PageError, DisambiguationError
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove
import requests, lxml, re, datetime
from bs4 import BeautifulSoup

API_TOKEN = '2035011359:AAGVyMjbyzDj7-TOaYIoiNEEQYmxmwfWmaw'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
channel = '@ok7_bots'
channel_join_link = 'https://t.me/+10N8yl2ChXc5NmIy'
dp = Dispatcher(bot)
admin = 880280670

wikipedia.set_lang('en')

def get_photo(text):
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582"
    }
    params = {
        "q": text,
        "tbm": "isch",
        "ijn": "0",
    }
    html = requests.get("https://www.google.com/search", params=params, headers=headers)
    soup = BeautifulSoup(html.text, 'lxml')
    all_script_tags = soup.select('script')
    matched_images_data = ''.join(re.findall(r"AF_initDataCallback\(([^<]+)\);", str(all_script_tags)))
    matched_images_data_fix = json.dumps(matched_images_data)
    matched_images_data_json = json.loads(matched_images_data_fix)
    matched_google_image_data = re.findall(r'\[\"GRID_STATE0\",null,\[\[1,\[0,\".*?\",(.*),\"All\",', matched_images_data_json)
    removed_matched_google_images_thumbnails = re.sub(
        r'\[\"(https\:\/\/encrypted-tbn0\.gstatic\.com\/images\?.*?)\",\d+,\d+\]', '', str(matched_google_image_data))
    matched_google_full_resolution_images = re.findall(r"(?:'|,),\[\"(https:|http.*?)\",\d+,\d+\]",
                                                       removed_matched_google_images_thumbnails)
    photos = list(filter(lambda x: bytes(x, 'ascii').decode('unicode-escape'), matched_google_full_resolution_images[:5]))
    photos = list(filter(lambda x: x[-5:] != '.wepg', photos))
    return photos[0]

def subscribe():
    url = InlineKeyboardButton('🔗 View channel', url=channel_join_link)
    check = InlineKeyboardButton('✅ Confirmation', callback_data='check')
    return InlineKeyboardMarkup(resize_keyboard=True, row_width=12).row(url).row(check)


def get_choices(choices):
    keyboards = []
    for choice in choices:
        keyboards.append([types.KeyboardButton(choice)])
    markup = types.ReplyKeyboardMarkup(keyboard=keyboards, resize_keyboard=True)
    return markup


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    name = message.chat.first_name
    await message.reply(f'🤖 Hello {name}\! Welcome to *Wikipedia Bot*\. '
                        'Just send me the word '
                        'and I will search for it on wikipedia', parse_mode='MarkdownV2', reply_markup=ReplyKeyboardRemove())


@dp.message_handler()
async def send_wiki(message: types.Message):
    chat_id = message.chat.id
    user_channel_status = await bot.get_chat_member(chat_id=channel, user_id=chat_id)
    if user_channel_status.status not in ['left', 'kicked']:
        try:
            response = wikipedia.summary(message.text)
            photo = get_photo(message.text)
            print(photo)
            await bot.send_photo(chat_id, caption=f'🌐 '+response, photo=photo, parse_mode='HTML', reply_markup=ReplyKeyboardRemove())
        except PageError:
            await message.answer('❌ No articles on this topic were found', reply_markup=ReplyKeyboardRemove())
        except (MessageIsTooLong, BadRequest):
            response = wikipedia.summary(message.text, sentences=5)
            await bot.send_photo(chat_id, caption=f'🌐 '+response[:1020],
                                 photo=get_photo(message.text), parse_mode='HTML', reply_markup=ReplyKeyboardRemove())
        except DisambiguationError as e:
            await message.reply("⚠️ Many articles on this topic have been found. Choose one of the following", reply_markup=get_choices(e.options))
    else:
        await message.answer('🤖 Please, subscribe to the channel below to use the bot', reply_markup=subscribe())
        

@dp.callback_query_handler(text='check')
async def check_subscription(callback_query: types.CallbackQuery):
    user_id = callback_query.message.chat.id
    user = callback_query.message.chat.first_name
    user_channel_status = await bot.get_chat_member(chat_id=channel, user_id=user_id)
    if user_channel_status.status in ['left', 'kicked']:
        await bot.answer_callback_query(callback_query.id, "You aren't a member of the channel", show_alert=True)
    else:
        await bot.delete_message(user_id, callback_query.message.message_id)
        await bot.send_message(admin, f'[{user}](tg://user?id={user_id}) joined the channel', parse_mode='MarkdownV2')
        await callback_query.message.answer('✅ OK. Now you can now use the bot')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
