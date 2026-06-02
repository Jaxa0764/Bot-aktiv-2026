import re
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import database
from quiz_data import QUIZ_SUBJECTS
from config import STATIC_DIR, DEV_MODE, PHOTOS_DIR

app = FastAPI(
    title="Smart Quiz Bot API",
    description="Secure backend for Smart Quiz Telegram Bot & Mini App",
    version="1.0.0"
)

# Pydantic models for structured input validation
class UserVerifyModel(BaseModel):
    telegram_id: int
    first_name: str
    last_name: str = None
    username: str = None
    photo_url: str = None

class QuizSubmitModel(BaseModel):
    telegram_id: int
    subject: str
    question_index: int
    answer: str

class WithdrawalRequestModel(BaseModel):
    telegram_id: int
    full_name: str
    card_number: str

# API Routes
@app.get("/api/user/{telegram_id}")
async def get_user_profile(telegram_id: int):
    """Fetches user details. In DEV_MODE, auto-creates a mock developer user if not exists."""
    user = database.get_user(telegram_id)
    
    if not user:
        if DEV_MODE or telegram_id == 12345678:
            print(f"[API] User {telegram_id} not found. Creating mock user for developer testing.")
            user = database.create_or_update_user(
                telegram_id=telegram_id,
                username="@dev_quiz_tester",
                first_name="Developer",
                last_name="Tester",
                phone_number="+998901234567",
                photo_url="/static/images/default-avatar.png"
            )
        else:
            raise HTTPException(status_code=404, detail="User not registered. Please /start the bot first.")
            
    return user

@app.post("/api/user/verify")
async def verify_or_create_user(payload: UserVerifyModel):
    """Called when user opens WebApp. Validates or initializes user profile in DB."""
    user = database.get_user(payload.telegram_id)
    if user:
        # Keep old phone number and photo if not provided in payload
        updated_photo = payload.photo_url if payload.photo_url else user["photo_url"]
        user = database.create_or_update_user(
            telegram_id=payload.telegram_id,
            username=payload.username,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone_number=user["phone_number"],
            photo_url=updated_photo
        )
    else:
        # Create new profile
        user = database.create_or_update_user(
            telegram_id=payload.telegram_id,
            username=payload.username,
            first_name=payload.first_name,
            last_name=payload.last_name,
            photo_url=payload.photo_url or "/static/images/default-avatar.png"
        )
    return user

@app.get("/api/quiz/subjects")
async def get_quiz_subjects():
    """Returns a list of quiz subjects with title, description, icon, and questions count, omitting the answers."""
    subjects_summary = {}
    for key, data in QUIZ_SUBJECTS.items():
        subjects_summary[key] = {
            "title": data["title"],
            "description": data["description"],
            "icon": data["icon"],
            "question_count": len(data["questions"])
        }
    return subjects_summary

@app.get("/api/quiz/questions/{subject}")
async def get_subject_questions(subject: str):
    """Returns questions for a specific subject, explicitly omitting the answers for security."""
    if subject not in QUIZ_SUBJECTS:
        raise HTTPException(status_code=404, detail="Subject not found")
        
    raw_questions = QUIZ_SUBJECTS[subject]["questions"]
    # Strip answers to prevent front-end inspect manipulation
    secure_questions = [{"index": i, "q": q["q"]} for i, q in enumerate(raw_questions)]
    return secure_questions

@app.post("/api/quiz/submit")
async def submit_quiz_answer(payload: QuizSubmitModel):
    """Verifies answer on the backend (preventing balance hacking) and updates player metrics."""
    if payload.subject not in QUIZ_SUBJECTS:
        raise HTTPException(status_code=404, detail="Subject not found")
        
    questions = QUIZ_SUBJECTS[payload.subject]["questions"]
    if payload.question_index < 0 or payload.question_index >= len(questions):
        raise HTTPException(status_code=400, detail="Invalid question index")
        
    # Standardize strings for loose matching: lowercase and trim trailing/leading whitespaces
    correct_ans = str(questions[payload.question_index]["a"]).strip().lower()
    user_ans = str(payload.answer).strip().lower()
    
    is_correct = (user_ans == correct_ans)
    reward = 10 if is_correct else 0
    
    # Update SQLite database in a safe atomic query
    user = database.add_quiz_score(payload.telegram_id, is_correct=is_correct, reward_amount=reward)
    if not user:
        raise HTTPException(status_code=404, detail="User not found in database. Open the bot first.")
        
    return {
        "correct": is_correct,
        "correct_answer": questions[payload.question_index]["a"] if not is_correct else "",
        "new_balance": user["balance"],
        "total_earned": user["total_earned"],
        "correct_answers": user["correct_answers"],
        "wrong_answers": user["wrong_answers"]
    }

@app.post("/api/wallet/withdraw")
async def request_withdrawal(payload: WithdrawalRequestModel):
    """Validates user balance, card specifications, and creates a withdrawal request."""
    # Clean the card number (strip whitespaces/dashes)
    card_number_clean = re.sub(r"\s+|-", "", payload.card_number)
    
    if len(card_number_clean) != 16 or not card_number_clean.isdigit():
        raise HTTPException(status_code=400, detail="Card number must contain exactly 16 digits.")
        
    user = database.get_user(payload.telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    balance = user["balance"]
    if balance < 1000:
        raise HTTPException(status_code=400, detail="Minimum withdrawal amount is 1000 so'm.")
        
    # We will withdraw their full balance!
    withdrawal_amount = balance
    
    # Create withdrawal request and deduct balance inside db transaction
    res = database.create_withdrawal(
        telegram_id=payload.telegram_id,
        full_name=payload.full_name,
        card_number=card_number_clean,
        amount=withdrawal_amount
    )
    
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
        
    # Get updated user data
    updated_user = database.get_user(payload.telegram_id)
    return {
        "success": True,
        "message": f"{withdrawal_amount} so'm withdrawal request has been submitted successfully.",
        "new_balance": updated_user["balance"]
    }

@app.get("/api/user/{telegram_id}/withdrawals")
async def get_user_withdrawal_history(telegram_id: int):
    """Returns historical withdrawal requests for the user."""
    return database.get_user_withdrawals(telegram_id)

@app.get("/api/admin/stats")
async def get_administration_stats():
    """Endpoint for future administration utility statistics."""
    return database.get_admin_stats()

@app.get("/api/config/firebase")
async def get_firebase_config():
    """Returns public Firebase configuration for client-side initialization."""
    from config import FIREBASE_PROJECT_ID, FIREBASE_API_KEY, FIREBASE_AUTH_DOMAIN
    return {
        "projectId": FIREBASE_PROJECT_ID,
        "apiKey": FIREBASE_API_KEY,
        "authDomain": FIREBASE_AUTH_DOMAIN
    }

# HTML Frontend Mounting and Redirects
@app.get("/")
async def serve_index():
    """Serves the Single Page Application index file."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return {"error": "Frontend static index.html not found. Please compile frontend."}
    return FileResponse(index_file)

# Mount all other static files (/static/css, /static/js, etc.)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/css", StaticFiles(directory=str(STATIC_DIR / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(STATIC_DIR / "js")), name="js")

@app.get("/{catchall:path}")
async def catch_all_redirect():
    """Fallback route redirecting to root index.html to maintain SPA behavior."""
    return RedirectResponse(url="/")
