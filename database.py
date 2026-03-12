import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('edu_star.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def execute(self, query, params=None, fetchone=False, fetchall=False):
        """SQL query ni bajarish"""
        if params is None:
            params = ()
        
        self.cursor.execute(query, params)
        self.conn.commit()
        
        if fetchone:
            return self.cursor.fetchone()
        elif fetchall:
            return self.cursor.fetchall()
        return None
    
    def create_tables(self):
        """Barcha jadvallarni yaratish"""
        # Users table
        self.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                full_name TEXT,
                group_info TEXT,
                phone TEXT,
                instagram_followed INTEGER DEFAULT 0,
                instagram_username TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Admins table
        self.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                telegram_id INTEGER PRIMARY KEY,
                full_name TEXT,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (added_by) REFERENCES admins (telegram_id)
            )
        """)
        
        # Teacher secrets table
        self.execute("""
            CREATE TABLE IF NOT EXISTS teacher_secrets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_name TEXT UNIQUE,
                secret_word TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Teacher channels table
        self.execute("""
            CREATE TABLE IF NOT EXISTS teacher_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                teacher_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Instagram users table
        self.execute("""
            CREATE TABLE IF NOT EXISTS instagram_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                followed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
        """)
        
        # Blocked users table
        self.execute("""
            CREATE TABLE IF NOT EXISTS blocked_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                reason TEXT,
                blocked_by INTEGER,
                blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
            )
        """)
        
        # Content table — kanal postlari saqlanadi
        self.execute("""
            CREATE TABLE IF NOT EXISTS content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hashtag TEXT UNIQUE,
                content_type TEXT,
                file_id TEXT,
                file_type TEXT,
                channel_msg_id INTEGER,
                teacher_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Initialize default secrets
        self.init_default_secrets()
        
        # Initialize default teacher channels
        self.init_default_channels()
    
    def init_default_secrets(self):
        """Standart maxfiy so'zlarni yaratish"""
        from config import DEFAULT_TEACHER_SECRETS
        
        for teacher, secret in DEFAULT_TEACHER_SECRETS.items():
            self.execute("""
                INSERT OR IGNORE INTO teacher_secrets (teacher_name, secret_word) 
                VALUES (?, ?)
            """, (teacher, secret))
    
    def init_default_channels(self):
        """Standart o'qituvchi kanallarini yaratish"""
        from config import TEACHER_CHANNELS
        
        for channel_id, teacher_name in TEACHER_CHANNELS.items():
            self.execute("""
                INSERT OR IGNORE INTO teacher_channels (channel_id, teacher_name) 
                VALUES (?, ?)
            """, (channel_id, teacher_name))
    
    # ========== TEACHER SECRETS ==========
    def get_secret(self, teacher_name):
        """O'qituvchining maxfiy so'zini olish"""
        result = self.execute("SELECT secret_word FROM teacher_secrets WHERE teacher_name = ?", 
                              (teacher_name,), fetchone=True)
        return result[0] if result else None
    
    def update_secret(self, teacher_name, new_secret):
        """Maxfiy so'zni yangilash"""
        self.execute("""
            INSERT OR REPLACE INTO teacher_secrets (teacher_name, secret_word) 
            VALUES (?, ?)
        """, (teacher_name, new_secret))
        return True
    
    def get_all_secrets(self):
        """Barcha maxfiy so'zlarni olish"""
        return self.execute("SELECT teacher_name, secret_word FROM teacher_secrets", fetchall=True)
    
    # ========== CHANNEL MAPPING FUNCTIONS ==========
    def set_channel_teacher(self, channel_id, teacher_name):
        """Kanalni o'qituvchiga biriktirish"""
        self.execute("""
            INSERT OR REPLACE INTO teacher_channels (channel_id, teacher_name)
            VALUES (?, ?)
        """, (channel_id, teacher_name))
        return True

    def get_channel_teacher(self, channel_id):
        """Kanal egasini (o'qituvchini) aniqlash"""
        res = self.execute("SELECT teacher_name FROM teacher_channels WHERE channel_id = ?", (channel_id,), fetchone=True)
        return res[0] if res else None
    
    def get_all_channels(self):
        """Barcha ulangan kanallarni olish"""
        return self.execute("SELECT channel_id, teacher_name FROM teacher_channels", fetchall=True)

    # ========== USER FUNCTIONS ==========
    def add_user(self, user_id, full_name, group_info, phone):
        self.execute("""
            INSERT OR REPLACE INTO users (telegram_id, full_name, group_info, phone) 
            VALUES (?, ?, ?, ?)
        """, (user_id, full_name, group_info, phone))
        return True
    
    def get_user(self, user_id):
        return self.execute("SELECT * FROM users WHERE telegram_id = ?", 
                          (user_id,), fetchone=True)
    
    def is_user_registered(self, user_id):
        return bool(self.get_user(user_id))
    
    def is_user_blocked(self, tg_id):
        return bool(self.execute("SELECT 1 FROM blocked_users WHERE telegram_id = ?", 
                               (tg_id,), fetchone=True))
    
    def block_user(self, tg_id, reason, admin_id):
        self.execute("INSERT OR REPLACE INTO blocked_users (telegram_id, reason, blocked_by) VALUES (?, ?, ?)",
                    (tg_id, reason, admin_id))
        # Foydalanuvchini faolsizlantirish (o'chirish o'rniga)
        self.execute("UPDATE users SET is_active = 0 WHERE telegram_id = ?", (tg_id,))
        return True
    
    def unblock_user(self, tg_id):
        # Avval bloklanganlar jadvalidan ma'lumot olish
        blocked_info = self.execute("SELECT reason, blocked_by FROM blocked_users WHERE telegram_id = ?", 
                                   (tg_id,), fetchone=True)
        
        if not blocked_info:
            return False  # Bloklangan foydalanuvchi topilmadi
        
        # Bloklanganlar jadvalidan o'chirish
        self.execute("DELETE FROM blocked_users WHERE telegram_id = ?", (tg_id,))
        
        # Users jadvalida borligini tekshirish
        user = self.get_user(tg_id)
        if user:
            # Agar users jadvalida bo'lsa - faollashtirish
            self.execute("UPDATE users SET is_active = 1 WHERE telegram_id = ?", (tg_id,))
        else:
            # Agar users jadvalida bo'lmasa - qayta tiklash
            self.execute("""
                INSERT INTO users (telegram_id, full_name, group_info, phone, instagram_followed, instagram_username, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (tg_id, "Blokdan chiqarilgan foydalanuvchi", "Noma'lum", "+998000000000", 0, None))
        
        return True
    
    def get_all_users(self):
        return self.execute("SELECT * FROM users", fetchall=True)
    
    def get_active_users(self):
        result = self.execute("SELECT COUNT(*) FROM users WHERE is_active = 1", fetchone=True)
        return result[0] if result else 0
    
    def get_all_active_users(self):
        """Barcha aktiv foydalanuvchilarni olish (telegram_id, full_name)"""
        return self.execute(
            "SELECT telegram_id, full_name FROM users WHERE is_active = 1", 
            fetchall=True
        )
    
    # ========== CONTENT FUNCTIONS ==========
    def save_content(self, hashtag, content_type, file_id, file_type, channel_msg_id, teacher_name=None):
        self.execute("""
            INSERT OR REPLACE INTO content (hashtag, content_type, file_id, file_type, channel_msg_id, teacher_name) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (hashtag.lower(), content_type, file_id, file_type, channel_msg_id, teacher_name))
        return True
    
    def get_content(self, hashtag):
        return self.execute("SELECT * FROM content WHERE hashtag = ?", 
                          (hashtag.lower(),), fetchone=True)
    
    def get_content_by_type(self, content_type):
        return self.execute("SELECT * FROM content WHERE content_type = ?", 
                          (content_type,), fetchall=True)
    
    def get_content_by_hashtag(self, hashtag):
        """Specific hashtag bo'yicha kontentni olish"""
        return self.execute("SELECT * FROM content WHERE hashtag = ?", 
                          (hashtag,), fetchone=True)
    
    def get_content_by_hashtags(self, hashtags):
        """Ko'plab hashtag'lar bo'yicha kontentni olish"""
        if not hashtags:
            return []
        
        placeholders = ','.join(['?' for _ in hashtags])
        query = f"SELECT * FROM content WHERE hashtag IN ({placeholders}) ORDER BY created_at DESC"
        return self.execute(query, hashtags, fetchall=True)
    
    def get_all_content(self):
        return self.execute("SELECT hashtag, content_type, file_type FROM content", fetchall=True)
    
    def debug_content(self):
        """Debug uchun barcha kontentni ko'rish"""
        return self.execute("SELECT * FROM content", fetchall=True)
    
    def get_lesson_content(self, lesson_num, content_type, teacher_name=None):
        """Dars kontentini olish"""
        # Aniq qidirish - to'liq hashtag pattern
        hashtag_pattern = f'#lesson{lesson_num}_{content_type}_'
        query = """
            SELECT * FROM content 
            WHERE hashtag LIKE ? AND content_type = ?
        """
        params = [f'{hashtag_pattern}%', content_type]
        
        # Agar teacher_name None bo'lsa, barcha o'qituvchilar kontentini qaytar
        # Agar teacher_name berilgan bo'lsa, faqat shu o'qituvchining kontentini qaytar
        if teacher_name:
            query += " AND teacher_name = ?"
            params.append(teacher_name)
        
        query += " ORDER BY created_at DESC"
        result = self.execute(query, params, fetchall=True)
        
        # Qo'shimcha tekshirish - faqat to'g'ri darslarni qaytarish
        filtered_result = []
        if result:
            for row in result:
                hashtag = row[1]  # hashtag column
                # Faqat aniq lesson va content type ni tekshirish
                if hashtag.startswith(f'#lesson{lesson_num}_{content_type}_'):
                    filtered_result.append(row)
        
        return filtered_result
    

    
    def get_teacher_info(self, teacher_name):
        """O'qituvchi ma'lumotlarini olish"""
        result = self.execute("SELECT * FROM teacher_secrets WHERE teacher_name = ?", 
                            (teacher_name,), fetchone=True)
        return result
    

    # ========== INSTAGRAM FUNCTIONS ==========
    def set_instagram_follow(self, tg_id, username):
        """Instagram obunasini qo'shish"""
        try:
            self.execute("""
                UPDATE users SET instagram_followed = 1, instagram_username = ? 
                WHERE telegram_id = ?
            """, (username, tg_id))
            return True
        except Exception as e:
            print(f"❌ Instagram holatini yangilashda xatolik: {e}")
            return False
    
    def get_instagram_status(self, tg_id):
        """Instagram obuna holatini olish"""
        result = self.execute("SELECT instagram_followed, instagram_username FROM users WHERE telegram_id = ?", 
                          (tg_id,), fetchone=True)
        return result if result else (0, None)
    
    def get_users_without_instagram(self):
        """Instagram obuna bo'lmagan foydalanuvchilar"""
        return self.execute("""
            SELECT telegram_id, full_name FROM users 
            WHERE is_active = 1 AND instagram_followed = 0
        """, fetchall=True)
    
    # ========== USER DELETE FUNCTION ==========
    def delete_user(self, user_id):
        """Foydalanuvchini bazadan to'liq o'chirish"""
        try:
            print(f"🗑️ Foydalanuvchini o'chirish boshlandi: {user_id}")
            result1 = self.execute("DELETE FROM users WHERE telegram_id = ?", (user_id,))
            print(f"📋 Users jadvalidan o'chirildi: {result1}")


            try:
                result3 = self.execute("DELETE FROM instagram_users WHERE user_id = ?", (user_id,))
                print(f"📷 Instagram ma'lumotlari o'chirildi: {result3}")
            except Exception as e:
                print(f"⚠️ Instagram jadvali topilmadi yoki xatolik: {e}")
            
            print(f"✅ Foydalanuvchi {user_id} muvaffaqiyatli o'chirildi")
            return True
            
        except Exception as e:
            print(f"❌ Foydalanuvchini o'chirishda xatolik: {e}")
            return False
    
    def get_all_users_for_excel(self):
        """Barcha foydalanuvchilarni Excel uchun olish"""
        return self.execute("""
            SELECT telegram_id, full_name, phone, group_info, instagram_followed, instagram_username, 
                   CASE WHEN is_active = 1 THEN '✅ Faol' ELSE '❌ Nofaol' END as status
            FROM users 
            ORDER BY full_name
        """, fetchall=True)
    
    def get_teacher_channels(self, teacher_name):
        """O'qituvchiga biriktirilgan kanallarni olish"""
        return self.execute("""
            SELECT channel_id FROM teacher_channels 
            WHERE teacher_name = ?
        """, (teacher_name,), fetchall=True)
    
    def add_teacher_channel(self, teacher_name, channel_id):
        """O'qituvchiga kanal biriktirish"""
        return self.execute("""
            INSERT OR REPLACE INTO teacher_channels (channel_id, teacher_name)
            VALUES (?, ?)
        """, (channel_id, teacher_name))
    
    def delete_teacher_channel(self, channel_id):
        """Kanalni o'chirish"""
        return self.execute("DELETE FROM teacher_channels WHERE channel_id = ?", (channel_id,))
    
    # ========== ADMIN FUNCTIONS ==========
    def add_admin(self, telegram_id, full_name, added_by):
        """Yangi admin qo'shish"""
        self.execute("""
            INSERT OR REPLACE INTO admins (telegram_id, full_name, added_by, is_active)
            VALUES (?, ?, ?, 1)
        """, (telegram_id, full_name, added_by))
        return True
    
    def remove_admin(self, telegram_id):
        """Adminni o'chirish (faolsizlantirish)"""
        self.execute("UPDATE admins SET is_active = 0 WHERE telegram_id = ?", (telegram_id,))
        return True
    
    def is_admin(self, telegram_id):
        """Foydalanuvchi admin ekanligini tekshirish"""
        # Asosiy admin (config dan)
        from config import ADMIN_ID
        if telegram_id == ADMIN_ID:
            return True
        
        # Database dan adminlarni tekshirish
        result = self.execute("""
            SELECT 1 FROM admins 
            WHERE telegram_id = ? AND is_active = 1
        """, (telegram_id,), fetchone=True)
        return bool(result)
    
    def get_all_admins(self):
        """Barcha faol adminlarni olish"""
        return self.execute("""
            SELECT telegram_id, full_name, added_by, added_at 
            FROM admins 
            WHERE is_active = 1 
            ORDER BY added_at DESC
        """, fetchall=True)
    
    def init_default_admin(self):
        """Asosiy adminni database ga qo'shish (agar bo'lmasa)"""
        from config import ADMIN_ID
        self.add_admin(ADMIN_ID, "Super Admin", ADMIN_ID)

# Global database object
db = Database()
