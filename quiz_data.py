# quiz_data.py
# Static dictionary of quiz subjects, questions, and exact answers.
# Answers are stored in lowercase for easy checking.

QUIZ_SUBJECTS = {
    "mathematics": {
        "title": "Mathematics",
        "description": "Test your logic, algebra, and basic math calculations.",
        "icon": "📐",
        "questions": [
            {"q": "What is 5 + 7?", "a": "12"},
            {"q": "What is 12 multiplied by 11?", "a": "132"},
            {"q": "What is the square of 9?", "a": "81"},
            {"q": "What is the square root of 64?", "a": "8"},
            {"q": "What is 100 divided by 4?", "a": "25"},
            {"q": "Solve for x: 2x - 6 = 10.", "a": "8"},
            {"q": "What is 15% of 200?", "a": "30"},
            {"q": "How many sides does a hexagon have?", "a": "6"},
            {"q": "What is the only even prime number?", "a": "2"},
            {"q": "What is 3 to the power of 3 (3^3)?", "a": "27"}
        ]
    },
    "english": {
        "title": "English",
        "description": "Vocabulary, basic grammar, plurals, and adjectives.",
        "icon": "📚",
        "questions": [
            {"q": "What is the past tense of the verb 'go'?", "a": "went"},
            {"q": "What is the opposite of the word 'cold'?", "a": "hot"},
            {"q": "What is the plural of 'child'?", "a": "children"},
            {"q": "What is the opposite of the word 'large'?", "a": "small"},
            {"q": "What is the plural form of the word 'mouse'?", "a": "mice"},
            {"q": "Which article is used before vowel sounds (e.g. 'apple')?", "a": "an"},
            {"q": "What is the comparative form of the adjective 'good'?", "a": "better"},
            {"q": "What is the opposite of the word 'dark'?", "a": "light"},
            {"q": "Fill in the blank: 'He ___ English every day' (studies/study).", "a": "studies"},
            {"q": "What is the plural of 'foot'?", "a": "feet"}
        ]
    },
    "history": {
        "title": "History",
        "description": "Famous landmarks, historic events, and past figures.",
        "icon": "🏛️",
        "questions": [
            {"q": "In which year did World War II end?", "a": "1945"},
            {"q": "Who was the first President of the United States? (Last name only)", "a": "washington"},
            {"q": "Which country built the famous ancient Pyramids?", "a": "egypt"},
            {"q": "In which year did the Titanic sink?", "a": "1912"},
            {"q": "Who was the legendary first Great Khan of the Mongol Empire?", "a": "genghis khan"},
            {"q": "Which empire built the Colosseum in Rome?", "a": "roman empire"},
            {"q": "What was the historical capital of the Byzantine Empire?", "a": "constantinople"},
            {"q": "Which continent is home to the ancient ruins of Machu Picchu?", "a": "south america"},
            {"q": "Who painted the famous artwork 'Mona Lisa'? (First & last name)", "a": "leonardo da vinci"},
            {"q": "Which German city was split by a famous wall until 1989?", "a": "berlin"}
        ]
    },
    "biology": {
        "title": "Biology",
        "description": "Human anatomy, plant systems, and animal kingdom facts.",
        "icon": "🧬",
        "questions": [
            {"q": "What gas do humans breathe in to survive?", "a": "oxygen"},
            {"q": "What is the basic structural unit of life in all organisms?", "a": "cell"},
            {"q": "How many chambers does the human heart have?", "a": "4"},
            {"q": "What is the largest organ of the human body?", "a": "skin"},
            {"q": "What green pigment in plants is used for photosynthesis?", "a": "chlorophyll"},
            {"q": "What is the main source of light and energy for life on Earth?", "a": "sun"},
            {"q": "How many bones are in an adult human body?", "a": "206"},
            {"q": "Which animal is known as the tallest living land mammal?", "a": "giraffe"},
            {"q": "What is the primary hereditary material in humans? (Abbreviation)", "a": "dna"},
            {"q": "What type of animal is a frog? (Amphibian, Reptile, or Mammal)", "a": "amphibian"}
        ]
    },
    "informatics": {
        "title": "Informatics",
        "description": "Computer science basics, hardware, internet, and languages.",
        "icon": "💻",
        "questions": [
            {"q": "What does the abbreviation 'CPU' stand for?", "a": "central processing unit"},
            {"q": "What is the name of the main operating system developed by Microsoft?", "a": "windows"},
            {"q": "Which programming language is famous for its clean indentation?", "a": "python"},
            {"q": "What is the largest global network of interconnected computers called?", "a": "internet"},
            {"q": "What does 'HTML' stand for?", "a": "hypertext markup language"},
            {"q": "What binary digit is used along with 1 in computer systems?", "a": "0"},
            {"q": "What does the hardware abbreviation 'RAM' stand for?", "a": "random access memory"},
            {"q": "What standard language is used to query relational databases?", "a": "sql"},
            {"q": "What CSS property is used to change text color?", "a": "color"},
            {"q": "Which tech giant created the Android mobile operating system?", "a": "google"}
        ]
    }
}
