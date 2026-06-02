import os
import json
from datetime import datetime
from config import DATABASE_PATH, FIREBASE_PROJECT_ID, FIREBASE_SERVICE_ACCOUNT_JSON

# Try to initialize Firebase
db = None
firebase_active = False

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    
    if not firebase_admin._apps:
        cred = None
        
        # 1. Try parsing service account JSON from environment variable
        if FIREBASE_SERVICE_ACCOUNT_JSON:
            try:
                # Try parsing as JSON string
                service_account_info = json.loads(FIREBASE_SERVICE_ACCOUNT_JSON)
                cred = credentials.Certificate(service_account_info)
                print("[Firebase] Ulanish muvaffaqiyatli: Env tarkibidagi JSON kalitidan foydalanilmoqda.")
            except json.JSONDecodeError:
                # If it's a file path
                if os.path.exists(FIREBASE_SERVICE_ACCOUNT_JSON):
                    cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_JSON)
                    print(f"[Firebase] Ulanish muvaffaqiyatli: {FIREBASE_SERVICE_ACCOUNT_JSON} faylidan foydalanilmoqda.")
                else:
                    print(f"[Firebase] WARNING: FIREBASE_SERVICE_ACCOUNT_JSON xato yoki fayl topilmadi: {FIREBASE_SERVICE_ACCOUNT_JSON}")
        
        # 2. Try default local file if no credentials loaded yet
        if not cred and os.path.exists("firebase_key.json"):
            cred = credentials.Certificate("firebase_key.json")
            print("[Firebase] Ulanish muvaffaqiyatli: local firebase_key.json faylidan foydalanilmoqda.")
            
        # Initialize app
        if cred:
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            firebase_active = True
            print("[Firebase] Firestore ishga tushdi (Service Account orqali).")
        elif FIREBASE_PROJECT_ID:
            firebase_admin.initialize_app(options={'projectId': FIREBASE_PROJECT_ID})
            db = firestore.client()
            firebase_active = True
            print(f"[Firebase] Firestore ishga tushdi (Project ID: {FIREBASE_PROJECT_ID}).")
        else:
            print("[Firebase] WARNING: Firebase kalitlari topilmadi. SQLite rejimiga o'tilmoqda.")
    else:
        db = firestore.client()
        firebase_active = True
except Exception as e:
    print(f"[Firebase] Ulanishda xatolik yuz berdi: {e}")
    print("[Firebase] SQLite ma'lumotlar bazasi rejimida davom ettiriladi.")

# ==================== SQLITE FALLBACK IMPLEMENTATION ====================
import sqlite3

def get_sqlite_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_sqlite_db():
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT NOT NULL,
            last_name TEXT,
            phone_number TEXT,
            photo_url TEXT,
            balance INTEGER DEFAULT 0,
            total_earned INTEGER DEFAULT 0,
            correct_answers INTEGER DEFAULT 0,
            wrong_answers INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            full_name TEXT NOT NULL,
            card_number TEXT NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL,
            FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
        )
    """)
    conn.commit()
    conn.close()

# ==================== MAIN DATABASE API INTERFACES ====================

def init_db():
    """Initializes the database. If Firestore is active, we check connectivity. Otherwise, SQLite is initialized."""
    if firebase_active:
        print("[Database] Firebase Firestore muvaffaqiyatli bog'landi va ishga tayyor.")
    else:
        init_sqlite_db()
        print("[Database] SQLite ma'lumotlar bazasi initsializatsiya qilindi.")

def get_user(telegram_id: int):
    """Retrieves a user profile by Telegram ID."""
    if firebase_active:
        try:
            doc_ref = db.collection("users").document(str(telegram_id))
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"[Firebase Database Error] get_user: {e}")
            return None
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

def create_or_update_user(telegram_id: int, username: str, first_name: str, last_name: str, phone_number: str = None, photo_url: str = None):
    """Creates a user or updates their profile details without resetting game stats (balance, correct/wrong count)."""
    now_str = datetime.now().isoformat()
    
    if firebase_active:
        try:
            doc_ref = db.collection("users").document(str(telegram_id))
            doc = doc_ref.get()
            
            if doc.exists:
                existing = doc.to_dict()
                updated_phone = phone_number if phone_number is not None else existing.get("phone_number")
                updated_photo = photo_url if photo_url is not None else existing.get("photo_url")
                
                doc_ref.update({
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name or "",
                    "phone_number": updated_phone or "",
                    "photo_url": updated_photo or "/static/images/default-avatar.png"
                })
            else:
                doc_ref.set({
                    "telegram_id": telegram_id,
                    "username": username or "",
                    "first_name": first_name,
                    "last_name": last_name or "",
                    "phone_number": phone_number or "",
                    "photo_url": photo_url or "/static/images/default-avatar.png",
                    "balance": 0,
                    "total_earned": 0,
                    "correct_answers": 0,
                    "wrong_answers": 0,
                    "created_at": now_str
                })
            
            return doc_ref.get().to_dict()
        except Exception as e:
            print(f"[Firebase Database Error] create_or_update_user: {e}")
            return None
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        existing = get_user(telegram_id)
        
        if existing:
            updated_phone = phone_number if phone_number is not None else existing['phone_number']
            updated_photo = photo_url if photo_url is not None else existing['photo_url']
            cursor.execute("""
                UPDATE users 
                SET username = ?, first_name = ?, last_name = ?, phone_number = ?, photo_url = ?
                WHERE telegram_id = ?
            """, (username, first_name, last_name, updated_phone, updated_photo, telegram_id))
        else:
            cursor.execute("""
                INSERT INTO users (telegram_id, username, first_name, last_name, phone_number, photo_url, balance, total_earned, correct_answers, wrong_answers, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, 0, ?)
            """, (telegram_id, username, first_name, last_name, phone_number, photo_url, now_str))
            
        conn.commit()
        conn.close()
        return get_user(telegram_id)

def add_quiz_score(telegram_id: int, is_correct: bool, reward_amount: int = 10):
    """Updates user statistics based on quiz answer."""
    if firebase_active:
        try:
            doc_ref = db.collection("users").document(str(telegram_id))
            doc = doc_ref.get()
            if not doc.exists:
                return None
                
            if is_correct:
                doc_ref.update({
                    "balance": firestore.Increment(reward_amount),
                    "total_earned": firestore.Increment(reward_amount),
                    "correct_answers": firestore.Increment(1)
                })
            else:
                doc_ref.update({
                    "wrong_answers": firestore.Increment(1)
                })
            return doc_ref.get().to_dict()
        except Exception as e:
            print(f"[Firebase Database Error] add_quiz_score: {e}")
            return None
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        user = get_user(telegram_id)
        if not user:
            conn.close()
            return None
            
        if is_correct:
            cursor.execute("""
                UPDATE users 
                SET balance = balance + ?, total_earned = total_earned + ?, correct_answers = correct_answers + 1
                WHERE telegram_id = ?
            """, (reward_amount, reward_amount, telegram_id))
        else:
            cursor.execute("""
                UPDATE users 
                SET wrong_answers = wrong_answers + 1
                WHERE telegram_id = ?
            """, (telegram_id,))
            
        conn.commit()
        conn.close()
        return get_user(telegram_id)

def create_withdrawal(telegram_id: int, full_name: str, card_number: str, amount: int):
    """Creates a withdrawal request, deducting from user balance."""
    if firebase_active:
        try:
            user_ref = db.collection("users").document(str(telegram_id))
            
            # Use transactional update for secure balance deduction
            @firestore.transactional
            def process_withdrawal_transaction(transaction):
                snapshot = user_ref.get(transaction=transaction)
                if not snapshot.exists:
                    return {"success": False, "message": "Foydalanuvchi topilmadi."}
                
                user_data = snapshot.to_dict()
                current_balance = user_data.get("balance", 0)
                if current_balance < amount:
                    return {
                        "success": False, 
                        "message": f"Mablag' yetarli emas. Talab etiladi: {amount}, Mavjud: {current_balance}"
                    }
                
                # Deduct balance
                transaction.update(user_ref, {"balance": current_balance - amount})
                
                # Record withdrawal
                now_str = datetime.now().isoformat()
                new_withdrawal_ref = db.collection("withdrawals").document()
                transaction.set(new_withdrawal_ref, {
                    "telegram_id": telegram_id,
                    "full_name": full_name,
                    "card_number": card_number,
                    "amount": amount,
                    "status": "pending",
                    "created_at": now_str
                })
                
                return {"success": True, "message": "Pul yechish so'rovi qabul qilindi."}
                
            transaction = db.transaction()
            res = process_withdrawal_transaction(transaction)
            return res
        except Exception as e:
            print(f"[Firebase Database Error] create_withdrawal: {e}")
            return {"success": False, "message": f"Ma'lumotlar bazasida xatolik yuz berdi: {str(e)}"}
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute("SELECT balance FROM users WHERE telegram_id = ?", (telegram_id,))
            row = cursor.fetchone()
            if not row:
                conn.rollback()
                return {"success": False, "message": "User not found"}
                
            current_balance = row['balance']
            if current_balance < amount:
                conn.rollback()
                return {"success": False, "message": "Sufficient funds not available."}
                
            cursor.execute("UPDATE users SET balance = balance - ? WHERE telegram_id = ?", (amount, telegram_id))
            
            now_str = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO withdrawals (telegram_id, full_name, card_number, amount, status, created_at)
                VALUES (?, ?, ?, ?, 'pending', ?)
            """, (telegram_id, full_name, card_number, amount, now_str))
            
            cursor.execute("COMMIT")
            conn.close()
            return {"success": True, "message": "Withdrawal request submitted successfully"}
        except Exception as e:
            conn.rollback()
            conn.close()
            return {"success": False, "message": f"Database error: {str(e)}"}

def get_user_withdrawals(telegram_id: int):
    """Retrieves withdrawal history of a user."""
    if firebase_active:
        try:
            # Query all withdrawals for user
            docs = db.collection("withdrawals").where("telegram_id", "==", telegram_id).stream()
            results = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                results.append(data)
            
            # Sort manually by created_at descending to avoid composite index requirements
            results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return results
        except Exception as e:
            print(f"[Firebase Database Error] get_user_withdrawals: {e}")
            return []
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM withdrawals WHERE telegram_id = ? ORDER BY id DESC", (telegram_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

def get_admin_stats():
    """Calculates administrative summary statistics across users and withdrawals."""
    if firebase_active:
        try:
            users = db.collection("users").stream()
            withdrawals = db.collection("withdrawals").stream()
            
            stats = {
                "total_users": 0,
                "total_active_balances": 0,
                "total_earned": 0,
                "total_correct_answers": 0,
                "total_wrong_answers": 0,
                "pending_withdrawals_count": 0,
                "pending_withdrawals_sum": 0,
                "completed_withdrawals_count": 0,
                "completed_withdrawals_sum": 0
            }
            
            for doc in users:
                ud = doc.to_dict()
                stats["total_users"] += 1
                stats["total_active_balances"] += ud.get("balance", 0)
                stats["total_earned"] += ud.get("total_earned", 0)
                stats["total_correct_answers"] += ud.get("correct_answers", 0)
                stats["total_wrong_answers"] += ud.get("wrong_answers", 0)
                
            for doc in withdrawals:
                wd = doc.to_dict()
                status = wd.get("status", "pending")
                amount = wd.get("amount", 0)
                
                if status == "pending":
                    stats["pending_withdrawals_count"] += 1
                    stats["pending_withdrawals_sum"] += amount
                elif status == "completed":
                    stats["completed_withdrawals_count"] += 1
                    stats["completed_withdrawals_sum"] += amount
            return stats
        except Exception as e:
            print(f"[Firebase Database Error] get_admin_stats: {e}")
            return {}
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        stats = {}
        
        cursor.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(balance) FROM users")
        stats['total_active_balances'] = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(total_earned) FROM users")
        stats['total_earned'] = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(correct_answers) FROM users")
        stats['total_correct_answers'] = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(wrong_answers) FROM users")
        stats['total_wrong_answers'] = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*), SUM(amount) FROM withdrawals WHERE status = 'pending'")
        pending_row = cursor.fetchone()
        stats['pending_withdrawals_count'] = pending_row[0]
        stats['pending_withdrawals_sum'] = pending_row[1] or 0
        
        cursor.execute("SELECT COUNT(*), SUM(amount) FROM withdrawals WHERE status = 'completed'")
        completed_row = cursor.fetchone()
        stats['completed_withdrawals_count'] = completed_row[0]
        stats['completed_withdrawals_sum'] = completed_row[1] or 0
        
        conn.close()
        return stats
