from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from logic import *
import schedule
import threading
import time
import os
import cv2
import numpy as np
from math import ceil, sqrt
from config import *

bot = TeleBot(API_TOKEN)
manager = None

def gen_markup(id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("Получить!", callback_data=id))
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    prize_id = call.data
    user_id = call.message.chat.id

    # Проверяем количество уже полученных призов
    winners_count = manager.count_prize_winners(prize_id)
    
    if winners_count >= 3:
        bot.send_message(user_id, "❌ Мне жаль, но уже 3 пользователя получили этот приз!")
        return
    
    # Добавляем пользователя как победителя
    if manager.add_winner(user_id, prize_id):
        # Отправляем расшифрованное изображение
        img = manager.get_prize_img(prize_id)
        with open(f'img/{img}', 'rb') as photo:
            bot.send_photo(user_id, photo, caption="🎉 Поздравляем! Ты получил приз!")
    else:
        bot.send_message(user_id, "⚠️ Ты уже получал этот приз!")


def send_message():
    prize_id, img = manager.get_random_prize()[:2]
    manager.mark_prize_used(prize_id)
    hide_img(img)
    for user in manager.get_users():
        with open(f'hidden_img/{img}', 'rb') as photo:
            bot.send_photo(user, photo, reply_markup=gen_markup(id = prize_id))
        

def shedule_thread():
    schedule.every().minute.do(send_message) # Здесь ты можешь задать периодичность отправки картинок
    while True:
        schedule.run_pending()
        time.sleep(1)

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    if user_id in manager.get_users():
        bot.reply_to(message, "Ты уже зарегестрирован!")
    else:
        manager.add_user(user_id, message.from_user.username)
        bot.reply_to(message, """Привет! Добро пожаловать! 
Тебя успешно зарегистрировали!
Каждый час тебе будут приходить новые картинки и у тебя будет шанс их получить!
Для этого нужно быстрее всех нажать на кнопку 'Получить!'

Только три первых пользователя получат картинку!)""")
        
@bot.message_handler(commands=['myscore'])
def get_my_score(message):
    user_id = message.from_user.id # Получаем ID пользователя из сообщения
    
    try:
        # Предполагаем, что get_user_score возвращает очки пользователя или None/0 при отсутствии
        score = db_manager.get_user_score(user_id)
        
        if score is not None and score >= 0: # Проверяем, что очки получены и они корректны
            bot.send_message(message.chat.id, f"Твои текущие очки: {score}")
        else:
            bot.send_message(message.chat.id, "У тебя пока нет очков. Начни играть, чтобы их получить!")
            
    except Exception as e:
        print(f"Ошибка в get_my_score: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении твоих очков.")

def polling_thread():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    manager = DatabaseManager(DATABASE)
    manager.create_tables()

    polling_thread = threading.Thread(target=polling_thread)
    polling_shedule  = threading.Thread(target=shedule_thread)

    polling_thread.start()
    polling_shedule.start()
  
