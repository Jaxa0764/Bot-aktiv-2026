// app.js - Single Page Application Core Controller
// Manages App State, Page Routing, API Integration, Quiz Loops, Wallet logic, and AI chat.

import { initializeApp } from "https://www.gstatic.com/firebasejs/11.9.1/firebase-app.js";
import { getFirestore, doc, setDoc, getDoc } from "https://www.gstatic.com/firebasejs/11.9.1/firebase-firestore.js";

// Global Firebase Instance variables
let db = null;
let firebaseInitialized = false;

// Global App State
let state = {
    user: {
        telegram_id: 12345678,
        username: "@dev_quiz_tester",
        first_name: "Developer",
        last_name: "Tester",
        phone_number: "+998 90 123 45 67",
        photo_url: "/static/images/default-avatar.png",
        balance: 0,
        total_earned: 0,
        correct_answers: 0,
        wrong_answers: 0,
        created_at: new Date().toISOString()
    },
    subjects: {},
    activeQuiz: null,
    currentTab: "home"
};

// Initialize Firebase SDK dynamically from server configuration
async function initFirebase() {
    try {
        const res = await fetch("/api/config/firebase");
        const config = await res.json();
        
        if (config.projectId && config.apiKey) {
            const firebaseConfig = {
                apiKey: config.apiKey,
                authDomain: config.authDomain || `${config.projectId}.firebaseapp.com`,
                projectId: config.projectId,
            };
            const app = initializeApp(firebaseConfig);
            db = getFirestore(app);
            firebaseInitialized = true;
            console.log("[Firebase] Firestore SDK has been initialized successfully.");
        } else {
            console.warn("[Firebase] Credentials not configured in .env. Front-end Firebase writes are disabled.");
        }
    } catch (err) {
        console.error("[Firebase] Initialization failed:", err);
    }
}

// Initialize App on DOM Content Loaded
document.addEventListener("DOMContentLoaded", async () => {
    console.log("[App] Initializing Smart Quiz Bot App...");
    
    // Create static images folder and default placeholder if not exists
    createDefaultAvatarPlaceholder();
    
    // Load Firebase Config first
    await initFirebase();
    
    // 1. Detect Telegram WebApp Platform or Browser Fallback
    await initTelegramWebApp();
    
    // 2. Fetch/Verify User Details
    fetchUserProfile();
    
    // 3. Load Quiz Subjects
    fetchQuizSubjects();
    
    // 4. Bind DOM UI Event Handlers
    bindEventHandlers();
});

// Create beautiful inline SVG default avatar if not present
function createDefaultAvatarPlaceholder() {
    // If the image tag fails to load, we assign an inline SVG colored avatar
    const defaultImg = document.getElementById("header-avatar");
    defaultImg.onerror = () => {
        defaultImg.src = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' fill='%239b51e0'/><circle cx='50' cy='35' r='20' fill='%23ffffff'/><path d='M20,80 C20,60 80,60 80,80' fill='%23ffffff'/></svg>";
    };
    
    const profileImg = document.getElementById("profile-avatar-img");
    profileImg.onerror = () => {
        profileImg.src = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' fill='%239b51e0'/><circle cx='50' cy='35' r='20' fill='%23ffffff'/><path d='M20,80 C20,60 80,60 80,80' fill='%23ffffff'/></svg>";
    };
}

// Initialize Telegram WebApp SDK
async function initTelegramWebApp() {
    if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData) {
        const webapp = window.Telegram.WebApp;
        webapp.ready();
        webapp.expand(); // Make full screen
        
        console.log("[App] Telegram WebApp detected. Loading user parameters.");
        
        // Load actual Telegram user profile
        if (webapp.initDataUnsafe && webapp.initDataUnsafe.user) {
            const tgUser = webapp.initDataUnsafe.user;
            state.user.telegram_id = tgUser.id;
            state.user.first_name = tgUser.first_name || "Foydalanuvchi";
            state.user.last_name = tgUser.last_name || "";
            state.user.username = tgUser.username ? `@${tgUser.username}` : "";
            
            // Set mock default photo, the server will serve the downloaded telegram profile avatar later if fetched
            state.user.photo_url = `/static/photos/${tgUser.id}.jpg`;
            
            // Foydalanuvchini bazaga yozish (Firebase Firestore)
            if (firebaseInitialized && db) {
                try {
                    const userDocRef = doc(db, "users", String(tgUser.id));
                    const docSnap = await getDoc(userDocRef);
                    
                    const userData = {
                        telegram_id: tgUser.id,
                        first_name: tgUser.first_name,
                        last_name: tgUser.last_name || "",
                        username: tgUser.username ? `@${tgUser.username}` : ""
                    };
                    
                    if (docSnap.exists()) {
                        // User exists, merge text details only so balance is preserved
                        await setDoc(userDocRef, userData, { merge: true });
                        console.log("[Firebase] User details merged in Firestore.");
                    } else {
                        // Create new user document
                        await setDoc(userDocRef, {
                            ...userData,
                            phone_number: "",
                            photo_url: `/static/photos/${tgUser.id}.jpg`,
                            balance: 0,
                            total_earned: 0,
                            correct_answers: 0,
                            wrong_answers: 0,
                            created_at: new Date().toISOString()
                        });
                        console.log("[Firebase] New user initialized in Firestore.");
                    }
                } catch (err) {
                    console.error("[Firebase] Direct setDoc write failed:", err);
                }
            }
        }
    } else {
        console.log("[App] Running in standard web browser. Activating Demo Mode.");
        showToast("E'lon: Ishlab chiquvchi rejimida ishlamoqdasiz! (Demo Mode)", "info");
    }
}

// Fetch Profile from FastAPI server
function fetchUserProfile() {
    const url = `/api/user/${state.user.telegram_id}`;
    
    // Send Verify payload first
    fetch("/api/user/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            telegram_id: state.user.telegram_id,
            first_name: state.user.first_name,
            last_name: state.user.last_name,
            username: state.user.username,
            photo_url: state.user.photo_url
        })
    })
    .then(res => res.json())
    .then(userData => {
        state.user = userData;
        updateUI();
    })
    .catch(err => {
        console.error("[App] Failed to verify user:", err);
        // Direct profile fetch fallback
        fetch(url)
            .then(res => res.json())
            .then(userData => {
                state.user = userData;
                updateUI();
            })
            .catch(e => console.error("[App] Direct user fetch error:", e));
    });
}

// Fetch subjects metadata
function fetchQuizSubjects() {
    fetch("/api/quiz/subjects")
        .then(res => res.json())
        .then(data => {
            state.subjects = data;
            renderSubjects();
            updateProgressMetrics();
        })
        .catch(err => console.error("[App] Failed to fetch subjects:", err));
}

// Update DOM elements based on State
function updateUI() {
    const user = state.user;
    
    // Header UI
    document.getElementById("header-username").textContent = user.first_name + (user.last_name ? " " + user.last_name : "");
    document.getElementById("header-balance").textContent = formatNumber(user.balance);
    if (user.photo_url) {
        document.getElementById("header-avatar").src = user.photo_url;
        document.getElementById("profile-avatar-img").src = user.photo_url;
    }
    
    // Home Tab
    document.getElementById("home-correct-cnt").textContent = user.correct_answers;
    document.getElementById("home-wallet-bal").textContent = formatNumber(user.balance) + " so'm";
    document.getElementById("home-total-earned").textContent = formatNumber(user.total_earned) + " so'm";
    
    // Wallet Tab
    document.getElementById("wallet-balance").textContent = formatNumber(user.balance);
    document.getElementById("wallet-total-earned").textContent = formatNumber(user.total_earned) + " so'm";
    document.getElementById("wallet-correct-answers").textContent = user.correct_answers + " ta";
    
    // Unlock or lock withdrawal controls
    const lockBanner = document.getElementById("withdraw-locked-banner");
    const withdrawForm = document.getElementById("withdraw-form");
    
    if (user.balance >= 1000) {
        lockBanner.style.display = "none";
        withdrawForm.style.display = "block";
    } else {
        lockBanner.style.display = "flex";
        withdrawForm.style.display = "none";
    }
    
    // Profile Tab
    document.getElementById("profile-fullname").textContent = user.first_name + (user.last_name ? " " + user.last_name : "");
    document.getElementById("profile-username-tag").textContent = user.username || "@username";
    document.getElementById("profile-tg-id").textContent = user.telegram_id;
    document.getElementById("profile-phone").textContent = user.phone_number || "Telefon kiritilmagan";
    
    if (user.created_at) {
        const date = new Date(user.created_at);
        document.getElementById("profile-join-date").textContent = date.toLocaleDateString("uz-UZ", { year: 'numeric', month: 'long', day: 'numeric' });
    }
}

// Calculate and render progress indicators
function updateProgressMetrics() {
    const totalQuestions = 50; // 5 subjects * 10 questions
    const answeredCount = Math.min(state.user.correct_answers + state.user.wrong_answers, totalQuestions);
    const progressPercent = Math.round((answeredCount / totalQuestions) * 100);
    
    document.getElementById("home-progress-fill").style.width = `${progressPercent}%`;
    document.getElementById("home-progress-percentage").textContent = `${progressPercent}% Bajarildi`;
    document.getElementById("home-progress-ratio").textContent = `${answeredCount}/${totalQuestions} Savol`;
}

// Render available subjects
function renderSubjects() {
    const container = document.getElementById("subjects-list-container");
    container.innerHTML = "";
    
    for (const key in state.subjects) {
        const sub = state.subjects[key];
        
        const card = document.createElement("div");
        card.className = "quiz-card";
        card.innerHTML = `
            <div class="quiz-info-col">
                <div class="quiz-card-icon">${sub.icon}</div>
                <div class="quiz-details">
                    <h3>${sub.title}</h3>
                    <p>${sub.description}</p>
                    <span class="quiz-tag-cnt"><i class="fa-solid fa-layer-group"></i> ${sub.question_count} ta savol</span>
                </div>
            </div>
            <button class="btn-quiz-start" onclick="startQuiz('${key}')">
                <i class="fa-solid fa-arrow-right"></i>
            </button>
        `;
        container.appendChild(card);
    }
}

// SPA tab switcher routing
function switchTab(tabId) {
    if (state.activeQuiz) return; // Prevent tab jumping during quiz
    
    console.log(`[Router] Switching to tab: ${tabId}`);
    
    // Update active state in state object
    state.currentTab = tabId;
    
    // Hide all panels
    document.querySelectorAll(".page-section").forEach(sec => sec.classList.remove("active"));
    document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));
    
    // Activate target panel
    document.getElementById(`page-${tabId}`).classList.add("active");
    
    // Activate nav button
    document.getElementById(`nav-${tabId}`).classList.add("active");
    
    // Fetch refreshed states for specific tabs
    if (tabId === "wallet") {
        fetchWithdrawalHistory();
        fetchUserProfile();
    } else if (tabId === "home" || tabId === "profile") {
        fetchUserProfile();
    }
}

// Event Bindings
function bindEventHandlers() {
    // Card inputs formatting (UzCard / Humo)
    const cardInput = document.getElementById("withdraw-card");
    cardInput.addEventListener("input", (e) => {
        let val = e.target.value.replace(/\s+/g, "").replace(/[^0-9]/gi, "");
        let formatted = "";
        for (let i = 0; i < val.length; i++) {
            if (i > 0 && i % 4 === 0) formatted += " ";
            formatted += val[i];
        }
        e.target.value = formatted;
    });
    
    // Bind AI chat trigger
    const aiBubble = document.getElementById("ai-support-trigger");
    const aiWindow = document.getElementById("ai-chat-window");
    const closeAi = document.getElementById("btn-close-ai-chat");
    
    aiBubble.addEventListener("click", () => {
        aiWindow.classList.add("active");
    });
    
    closeAi.addEventListener("click", () => {
        aiWindow.classList.remove("active");
    });
    
    // Bind Quiz Play controller closures
    document.getElementById("btn-quit-quiz").addEventListener("click", quitQuizPlay);
    document.getElementById("btn-submit-answer").addEventListener("click", submitQuizAnswer);
    
    // Bind Quiz play text field Enter keypress
    document.getElementById("quiz-user-answer").addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            submitQuizAnswer();
        }
    });
    
    // Bind results modal buttons
    document.getElementById("btn-restart-subject").addEventListener("click", () => {
        const subKey = state.activeQuiz.subjectKey;
        document.getElementById("quiz-results-modal").classList.remove("active");
        state.activeQuiz = null;
        startQuiz(subKey);
    });
    
    document.getElementById("btn-exit-results").addEventListener("click", () => {
        document.getElementById("quiz-results-modal").classList.remove("active");
        state.activeQuiz = null;
        switchTab("quizzes");
    });
}

// ----------------- QUIZ CONTROLLER LOOPS -----------------

function startQuiz(subjectKey) {
    console.log(`[Quiz] Fetching questions for: ${subjectKey}`);
    
    // Close result dashboard just in case
    document.getElementById("quiz-results-modal").classList.remove("active");
    
    // Show loading state
    showToast("Yuklanmoqda...", "info");
    
    fetch(`/api/quiz/questions/${subjectKey}`)
        .then(res => {
            if (!res.ok) throw new Error("Fanni yuklab bo'lmadi");
            return res.json();
        })
        .then(questions => {
            state.activeQuiz = {
                subjectKey: subjectKey,
                title: state.subjects[subjectKey].title,
                icon: state.subjects[subjectKey].icon,
                questions: questions,
                currentIndex: 0,
                correctAnswers: 0,
                wrongAnswers: 0,
                wrongList: []
            };
            
            // Render UI Modal
            document.getElementById("quiz-subj-title").textContent = state.activeQuiz.title;
            document.getElementById("quiz-subj-icon").textContent = state.activeQuiz.icon;
            
            document.getElementById("quiz-play-modal").classList.add("active");
            renderQuizQuestion();
        })
        .catch(err => {
            showToast("Xatolik yuz berdi: " + err.message, "error");
        });
}

function renderQuizQuestion() {
    const qState = state.activeQuiz;
    const currentQ = qState.questions[qState.currentIndex];
    
    // Clear previous input/alerts
    document.getElementById("quiz-user-answer").value = "";
    document.getElementById("quiz-user-answer").disabled = false;
    document.getElementById("quiz-feedback-box").innerHTML = "";
    
    // Enable submit button
    const submitBtn = document.getElementById("btn-submit-answer");
    submitBtn.disabled = false;
    submitBtn.innerHTML = `Javobni tekshirish <i class="fa-solid fa-paper-plane"></i>`;
    
    // Update texts
    document.getElementById("quiz-question-text").textContent = currentQ.q;
    document.getElementById("quiz-step-txt").textContent = `Savol: ${qState.currentIndex + 1} / ${qState.questions.length}`;
    
    // Update progress bar fill
    const fillPercent = ((qState.currentIndex + 1) / qState.questions.length) * 100;
    document.getElementById("quiz-step-fill").style.width = `${fillPercent}%`;
    
    // Set focus on input field after small delay
    setTimeout(() => {
        document.getElementById("quiz-user-answer").focus();
    }, 150);
}

function submitQuizAnswer() {
    const qState = state.activeQuiz;
    if (!qState) return;
    
    const ansInput = document.getElementById("quiz-user-answer");
    const answer = ansInput.value.trim();
    
    if (!answer) {
        showToast("Iltimos, avval javobingizni yozing!", "info");
        return;
    }
    
    // Lock inputs while checking
    ansInput.disabled = true;
    const submitBtn = document.getElementById("btn-submit-answer");
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Tekshirilmoqda...`;
    
    const currentQ = qState.questions[qState.currentIndex];
    
    // Send to backend API for validation (Secure balance accretion)
    fetch("/api/quiz/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            telegram_id: state.user.telegram_id,
            subject: qState.subjectKey,
            question_index: currentQ.index,
            answer: answer
        })
    })
    .then(res => res.json())
    .then(resData => {
        // Update user scores and balances
        state.user.balance = resData.new_balance;
        state.user.total_earned = resData.total_earned;
        state.user.correct_answers = resData.correct_answers;
        state.user.wrong_answers = resData.wrong_answers;
        
        // Update UI everywhere
        updateUI();
        
        const feedbackContainer = document.getElementById("quiz-feedback-box");
        
        if (resData.correct) {
            qState.correctAnswers++;
            feedbackContainer.innerHTML = `
                <div class="feedback-msg correct">
                    <i class="fa-solid fa-circle-check"></i>
                    <span>To'g'ri! +10 so'm hisobingizga qo'shildi.</span>
                </div>
            `;
        } else {
            qState.wrongAnswers++;
            qState.wrongList.push({
                q: currentQ.q,
                your_ans: answer,
                correct_ans: resData.correct_answer
            });
            
            feedbackContainer.innerHTML = `
                <div class="feedback-msg wrong">
                    <i class="fa-solid fa-circle-xmark"></i>
                    <span>Xato! To'g'ri javob: <b>${resData.correct_answer}</b></span>
                </div>
            `;
        }
        
        // Wait 2.5s and load next question or show complete dashboard
        setTimeout(() => {
            qState.currentIndex++;
            if (qState.currentIndex < qState.questions.length) {
                renderQuizQuestion();
            } else {
                finishQuizPlay();
            }
        }, 2500);
    })
    .catch(err => {
        console.error("[Quiz] Answer submit failed:", err);
        showToast("API xatolik yuz berdi. Iltimos qayta urining.", "error");
        ansInput.disabled = false;
        submitBtn.disabled = false;
        submitBtn.innerHTML = `Javobni tekshirish <i class="fa-solid fa-paper-plane"></i>`;
    });
}

function quitQuizPlay() {
    if (confirm("Haqiqatan ham viktorinadan chiqmoqchimisiz? Progress yo'qotiladi!")) {
        document.getElementById("quiz-play-modal").classList.remove("active");
        state.activeQuiz = null;
        switchTab("quizzes");
    }
}

function finishQuizPlay() {
    document.getElementById("quiz-play-modal").classList.remove("active");
    
    const qState = state.activeQuiz;
    
    // Fill in stats details
    document.getElementById("res-correct-cnt").textContent = qState.correctAnswers;
    document.getElementById("res-wrong-cnt").textContent = qState.wrongAnswers;
    
    const totalEarnedInQuiz = qState.correctAnswers * 10;
    document.getElementById("res-earned-val").textContent = `+${totalEarnedInQuiz}`;
    
    // Show incorrect answers logger
    const wrongLogBox = document.getElementById("wrong-questions-log-box");
    const wrongListUl = document.getElementById("wrong-questions-list");
    
    if (qState.wrongList.length > 0) {
        wrongListUl.innerHTML = "";
        qState.wrongList.forEach(item => {
            const li = document.createElement("li");
            li.innerHTML = `
                <span class="wq-txt">❓ ${item.q}</span>
                Siz: <span class="wq-ans">${item.your_ans}</span> | To'g'ri: <span class="wq-correct">${item.correct_ans}</span>
            `;
            wrongListUl.appendChild(li);
        });
        wrongLogBox.style.display = "block";
    } else {
        wrongLogBox.style.display = "none";
    }
    
    // Open results overlay modal
    document.getElementById("quiz-results-modal").classList.add("active");
}


// ----------------- WALLET WITHDRAWAL CONTROLLER -----------------

function handleWithdrawal(event) {
    event.preventDefault();
    
    const name = document.getElementById("withdraw-fullname").value.trim();
    const cardRaw = document.getElementById("withdraw-card").value.replace(/\s+/g, "");
    
    if (cardRaw.length !== 16 || isNaN(cardRaw)) {
        showToast("Karta raqami noto'g'ri (16 xonali bo'lishi lozim)!", "error");
        return;
    }
    
    const submitBtn = document.getElementById("btn-withdraw-submit");
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Yuborilmoqda...`;
    
    fetch("/api/wallet/withdraw", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            telegram_id: state.user.telegram_id,
            full_name: name,
            card_number: cardRaw
        })
    })
    .then(res => {
        if (!res.ok) return res.json().then(e => { throw new Error(e.detail); });
        return res.json();
    })
    .then(resData => {
        showToast("So'rov muvaffaqiyatli qabul qilindi! ✅", "info");
        
        // Reset form
        document.getElementById("withdraw-fullname").value = "";
        document.getElementById("withdraw-card").value = "";
        
        // Update local balance from response
        state.user.balance = resData.new_balance;
        updateUI();
        
        // Refresh withdrawals log list
        fetchWithdrawalHistory();
    })
    .catch(err => {
        showToast("Xatolik: " + err.message, "error");
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `Pulni yechishni so'rash <i class="fa-solid fa-circle-chevron-right"></i>`;
    });
}

function fetchWithdrawalHistory() {
    fetch(`/api/user/${state.user.telegram_id}/withdrawals`)
        .then(res => res.json())
        .then(data => {
            const emptyPlaceholder = document.getElementById("history-empty-placeholder");
            const listUl = document.getElementById("withdrawal-history-list");
            
            if (data.length > 0) {
                emptyPlaceholder.style.display = "none";
                listUl.style.display = "flex";
                listUl.innerHTML = "";
                
                data.forEach(item => {
                    // Format date
                    const dateObj = new Date(item.created_at);
                    const formattedDate = dateObj.toLocaleDateString("uz-UZ") + " " + dateObj.toLocaleTimeString("uz-UZ", { hour: '2-digit', minute: '2-digit' });
                    
                    // Format card mask (e.g. 8600 **** **** 1234)
                    const rawCard = item.card_number;
                    const maskedCard = `${rawCard.slice(0, 4)} **** **** ${rawCard.slice(12)}`;
                    
                    // Status styling
                    let statusLabel = "Kutilmoqda";
                    if (item.status === "completed") statusLabel = "O'tkazildi";
                    if (item.status === "rejected") statusLabel = "Rad etildi";
                    
                    const li = document.createElement("li");
                    li.className = "history-item";
                    li.innerHTML = `
                        <div class="hist-info">
                            <span class="hist-name">${item.full_name}</span>
                            <span class="hist-card"><i class="fa-solid fa-credit-card"></i> ${maskedCard}</span>
                            <span class="hist-date">${formattedDate}</span>
                        </div>
                        <div class="hist-status-col">
                            <span class="hist-amt">${formatNumber(item.amount)} so'm</span>
                            <span class="badge-status ${item.status}">${statusLabel}</span>
                        </div>
                    `;
                    listUl.appendChild(li);
                });
            } else {
                emptyPlaceholder.style.display = "flex";
                listUl.style.display = "none";
            }
        })
        .catch(err => console.error("[App] Failed to fetch withdrawal history:", err));
}


// ----------------- FLOATING AI CHAT ASSISTANT -----------------

function askAiQuestion(topic) {
    const chatContainer = document.getElementById("ai-messages-container");
    const indicator = document.getElementById("ai-typing-indicator");
    
    // User question texts mapping
    let userQuestion = "";
    let botReply = "";
    
    if (topic === 'about') {
        userQuestion = "Bot haqida batafsil ma'lumot bera olasizmi? ℹ️";
        botReply = "📚 **SMART QUIZ BOT** - bu foydalanuvchilarning intellektual bilimlarini oshirish va ularni rag'batlantirish uchun yaratilgan zamonaviy platformadir.\n\nSiz bu yerda o'z bilimlaringizni turli fanlar bo'yicha sinashingiz va har bir to'g'ri topilgan savol uchun virtual mablag' shaklida pul mukofotini qo'lga kiritishingiz mumkin. Platforma to'liq avtomatlashtirilgan bo'lib, halol va xavfsiz bilim bahslashuviga tayanadi.";
    } else if (topic === 'rules') {
        userQuestion = "Viktorina shartlari va qoidalari qanday? 📝";
        botReply = "🎯 **Viktorina qoidalari juda oddiy:**\n\n1️⃣ Platformada 5 ta asosiy fan mavjud: Matematika, Ingliz tili, Tarix, Biologiya va Informatika.\n2️⃣ Har bir fanda **10 tadan** qiziqarli va ta'limiy savollar mavjud.\n3️⃣ Siz javobni klaviaturadan aniq yozishingiz lozim (harflar kattaligi ahamiyatsiz, probellar avtomatik tozalanadi).\n4️⃣ Har bir to'g'ri javob uchun sizga **10 so'm** to'lanadi.\n5️⃣ Agar xato qilsangiz, hech qanday jarima yo'q! Istalgan vaqtda testlarni qayta boshlashingiz mumkin.";
    } else if (topic === 'wallet') {
        userQuestion = "Pul yechish tizimi qanday ishlaydi? 💳";
        botReply = "💸 **Mablag'larni yechib olish shartlari:**\n\n- Yechib olish uchun eng kam miqdor **1,000 so'm**ni tashkil etadi.\n- Kerakli balansga yetgach, **'Hamyon'** sahifasida yechish formasi faollashadi.\n- Siz o'z **UzCard** yoki **Humo** kartangizning 16 xonali raqamini va karta egasining ismini kiritishingiz lozim.\n- So'rov yuborilgach, ma'lumotlar backend tizimimizda tekshiriladi va pul mablag'lari **24 soat** ichida kartangizga o'tkazib beriladi.";
    } else if (topic === 'profile') {
        userQuestion = "Profil ma'lumotlarini qayerdan sozlayman? 👤";
        botReply = "👤 **Profil boshqaruvi:**\n\nSizning barcha ma'lumotlaringiz: ism-sharifingiz, Telegram ID, tasdiqlangan telefon raqamingiz hamda o'yin statistikangiz **'Profil'** bo'limida ko'rsatiladi.\n\nUshbu ma'lumotlar Telegram Bot API orqali shaxsan siz ulagan hisobingizdan avtomatik yuklanadi. Profilingiz to'liq himoyalangan.";
    }
    
    // Append User Message to Chat log
    const userMsgDiv = document.createElement("div");
    userMsgDiv.className = "chat-msg user-msg";
    userMsgDiv.innerHTML = `
        <p>${userQuestion}</p>
        <span class="msg-time">${getCurrentTimeText()}</span>
    `;
    chatContainer.appendChild(userMsgDiv);
    scrollChatToBottom();
    
    // Show bot typing animation
    indicator.style.display = "flex";
    scrollChatToBottom();
    
    // Delay Bot reply to feel natural
    setTimeout(() => {
        indicator.style.display = "none";
        
        const botMsgDiv = document.createElement("div");
        botMsgDiv.className = "chat-msg bot-msg";
        
        // Format markdown double-stars to bold HTML tags
        let htmlFormatted = botReply
            .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
            .replace(/\n/g, '<br>');
            
        botMsgDiv.innerHTML = `
            <p>${htmlFormatted}</p>
            <span class="msg-time">${getCurrentTimeText()}</span>
        `;
        chatContainer.appendChild(botMsgDiv);
        scrollChatToBottom();
    }, 1200);
}

function scrollChatToBottom() {
    const container = document.getElementById("ai-messages-container");
    container.scrollTop = container.scrollHeight;
}

function getCurrentTimeText() {
    const now = new Date();
    return now.toLocaleTimeString("uz-UZ", { hour: '2-digit', minute: '2-digit' });
}


// ----------------- TOAST UTILITIES -----------------

function showToast(message, type = "info") {
    const toast = document.getElementById("toast-notification");
    const msgSpan = document.getElementById("toast-message");
    const icon = document.getElementById("toast-icon");
    
    msgSpan.textContent = message;
    
    // Clear old themes
    toast.className = "toast-notification";
    
    // Set theme and icon
    if (type === "error") {
        toast.classList.add("theme-error");
        icon.className = "fa-solid fa-circle-exclamation text-red";
        toast.style.borderColor = "rgba(231, 76, 60, 0.4)";
    } else if (type === "success" || type === "info") {
        toast.classList.add("theme-info");
        icon.className = "fa-solid fa-circle-info text-cyan";
        toast.style.borderColor = "rgba(0, 242, 254, 0.4)";
    }
    
    // Show toast
    toast.classList.add("active");
    
    // Auto hide after 3 seconds
    setTimeout(() => {
        toast.classList.remove("active");
    }, 3000);
}

// ----------------- NUMBER UTILITIES -----------------

function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

// Expose modules functions to global scope for HTML inline calls (like onclick)
window.switchTab = switchTab;
window.startQuiz = startQuiz;
window.handleWithdrawal = handleWithdrawal;
window.askAiQuestion = askAiQuestion;
