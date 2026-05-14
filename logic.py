import sqlite3
import random
from datetime import datetime
from config import DATABASE 
import os
import cv2

class DatabaseManager:
    def __init__(self, database):
        self.database = database

    def create_tables(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                user_name TEXT
            )
        ''')

            conn.execute('''
            CREATE TABLE IF NOT EXISTS prizes (
                prize_id INTEGER PRIMARY KEY,
                image TEXT,
                used INTEGER DEFAULT 0
            )
        ''')

            conn.execute('''
            CREATE TABLE IF NOT EXISTS winners (
                user_id INTEGER,
                prize_id INTEGER,
                win_time TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id),
                FOREIGN KEY(prize_id) REFERENCES prizes(prize_id)
            )
        ''')

            conn.commit()

    def add_user(self, user_id, user_name):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('INSERT INTO users VALUES (?, ?)', (user_id, user_name))
            conn.commit()

    def add_prize(self, data):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.executemany('''INSERT INTO prizes (image) VALUES (?)''', data)
            conn.commit()

    def add_winner(self, user_id, prize_id):
        win_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM winners WHERE user_id = ? AND prize_id = ?", (user_id, prize_id))
            if cur.fetchall():
                return 0
            else:
                conn.execute('''INSERT INTO winners (user_id, prize_id, win_time) VALUES (?, ?, ?)''', (user_id, prize_id, win_time))
                conn.commit()
                return 1

    def mark_prize_used(self, prize_id):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''UPDATE prizes SET used = 1 WHERE prize_id = ?''', (prize_id,))
            conn.commit()

    def get_users(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT user_id FROM users')
            rows = cur.fetchall()
        return [row[0] for row in rows]

    def get_prize_img(self, prize_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT image FROM prizes WHERE prize_id = ?', (prize_id,))
            row = cur.fetchone()
        return row[0] if row else None

    def get_random_prize(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT prize_id, image, used FROM prizes WHERE used = 0')
            rows = cur.fetchall()
        if not rows:
            return None
        return random.choice(rows)

    def count_prize_winners(self, prize_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT COUNT(*) FROM winners WHERE prize_id = ?', (prize_id,))
            count = cur.fetchone()[0]
        return count

    def get_winners(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('''SELECT u.user_name, w.prize_id, w.win_time 
                          FROM winners w 
                          JOIN users u ON w.user_id = u.user_id 
                          ORDER BY w.win_time DESC''')
            rows = cur.fetchall()
        return rows

class DatabaseManager:
    def get_winners_img(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(''' 
    SELECT image FROM winners 
    INNER JOIN prizes ON 
    winners.prize_id = prizes.prize_id
    WHERE user_id = ?''', (user_id, ))
            return cur.fetchall()
@bot.message_handler(commands=['rating'])
def handle_rating(message):
    winners = manager.get_winners()
    
    if not winners:
        bot.send_message(message.chat.id, "📊 Таблица рейтинга пуста. Победителей пока нет!")
        return
    
    # Формируем таблицу
    rating_text = "📊 <b>Таблица рейтинга</b>\n\n"
    rating_text += "<code>" + f"{'№':<3} {'Пользователь':<20} {'Приз ID':<10} {'Время':<19}\n" + "-" * 52 + "</code>\n"
    
    for idx, (username, prize_id, win_time) in enumerate(winners, 1):
        username = username or "Unknown"
        rating_text += f"<code>{idx:<3} {username:<20} {prize_id:<10} {win_time:<19}</code>\n"
    
    bot.send_message(message.chat.id, rating_text, parse_mode="HTML")

def create_collage(image_paths):
    images = []
    for path in image_paths:
        image = cv2.imread(path)
        images.append(image)

    num_images = len(images)
    num_cols = floor(sqrt(num_images)) # Поиск количество картинок по горизонтали
    num_rows = ceil(num_images/num_cols)  # Поиск количество картинок по вертикали
    # Создание пустого коллажа
    collage = np.zeros((num_rows * images[0].shape[0], num_cols * images[0].shape[1], 3), dtype=np.uint8)
    # Размещение изображений на коллаже
    for i, image in enumerate(images):
        row = i // num_cols
        col = i % num_cols
        collage[row*image.shape[0]:(row+1)*image.shape[0], col*image.shape[1]:(col+1)*image.shape[1], :] = image
    return collage


m = DatabaseManager(DATABASE)
info = m.get_winners_img("user_id")
prizes = [x[0] for x in info]
image_paths = os.listdir('img')
image_paths = [f'img/{x}' if x in prizes else f'hidden_img/{x}' for x in image_paths]
collage = create_collage(image_paths)

def get_winners_img(self, user_id):
    conn = sqlite3.connect(self.database)
    with conn:
        cur = conn.cursor()
        cur.execute(''' 
SELECT image FROM winners 
INNER JOIN prizes ON 
winners.prize_id = prizes.prize_id
WHERE user_id = ?''', (user_id, ))
        return cur.fetchall()
def hide_img(img_name):
    image = cv2.imread(f'img/{img_name}')
    blurred_image = cv2.GaussianBlur(image, (15, 15), 0)
    pixelated_image = cv2.resize(blurred_image, (30, 30), interpolation=cv2.INTER_NEAREST)
    pixelated_image = cv2.resize(pixelated_image, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(f'hidden_img/{img_name}', pixelated_image)

if __name__ == '__main__':
    manager = DatabaseManager(DATABASE)
    manager.create_tables()
    prizes_img = os.listdir('img')
    data = [(x,) for x in prizes_img]
    manager.add_prize(data)
