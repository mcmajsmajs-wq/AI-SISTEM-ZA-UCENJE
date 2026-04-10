# -*- coding: utf-8 -*-
"""
================================================================================
QUIZ PROMPT TEMPLATES
================================================================================

Verzija: 1.0.0
================================================================================
"""

QUIZ_PROMPT = """You are an expert educator and assessment designer. Based on the following text, generate exactly {num_questions} high-quality quiz questions that test deep understanding.

STRICT FILTERING RULES - IGNORE the following content COMPLETELY:
1. "This page intentionally left blank" and similar blank page notices
2. Copyright notices, edition notices (e.g., "Second Edition", "Third Edition", "First Edition")
3. "Notice to Readers", "Notice to Reader" or similar disclaimers
4. Table of Contents, Prefaces, Acknowledgments, Introductions
5. Figure captions, image descriptions, "Figure X:" without substantive content
6. Page numbers, headers, footers, running titles
7. Very short content (< 100 characters)
8. Generic statements without specific information
9. Notes sections, footnotes, endnotes, "Notes:" sections
10. Cover pages, back covers, front matter, back matter
11. "About the Author", author biography pages
12. Index pages, glossaries
13. Any page that is mostly references or citations
14. OCR noise, garbled text, unreadable characters

ONLY create questions from:
- Actual substantive content with specific facts, concepts, definitions
- Step-by-step processes or procedures with detailed steps
- Specific examples with concrete details
- Definitions of key terms with explanations
- Data, statistics, research findings with numbers
- Cause-effect relationships explained in text
- Detailed explanations of concepts
- Historical events with dates and details

IMPORTANT - QUESTION TYPES:
- 60% multiple_choice — 1 correct answer, 4 plausible options
- 25% checkbox — 2-4 correct answers, 4 options (select ALL that apply)  
- 15% true_false — balanced mix of TRUE and FALSE statements

CRITICAL: TRUE/FALSE BALANCE
- For TRUE/FALSE questions: Exactly 50% should be TRUE, 50% FALSE
- Create false statements by: negating a fact, changing a number/date, reversing cause-effect, stating opposite
- NEVER make all true/false questions have the same answer!

QUESTION QUALITY - Make questions ANALYTICAL and THOUGHT-PROVOKING:
- NOT: "Koji je glavni grad Mesopotamije?" (simple recall)
- YES: "Zašto su gradovi Mesopotamije nastajali na rekama? Objasni geografski i ekonomski razlog."
- NOT: "Šta je hram?" (definition only)
- YES: "Čemu su služili zikgurati u drevnoj Mesopotamiji i kako se njihova funkcija razlikovala od običnih hramova?"

Options must be:
- Complete meaningful sentences (not single letters/words)
- Plausible but clearly distinguishable
- Testing real understanding, not just memorization
- For false statements in true_false: make them plausible but wrong

============================================================
CRITICAL: EXPLANATIONS MUST BE EDUCATIONAL AND DETAILED!
============================================================

FOR MATHEMATICS (especially important!):
- Show the STEP-BY-STEP CALCULATION process
- Include the FORMULA used for the solution
- Explain the MATHEMATICAL LOGIC and reasoning
- For example, if question is about triangle area: "Површина троугла се рачуна као половина производа основице и висине: P = (a * h) / 2. За a=6 и h=4, добијамо P = (6 * 4) / 2 = 12cm²"

For geometry:
- Always include which formula was used
- Show the substitution of values
- Explain WHY that formula applies

For algebra:
- Show the equation setup
- Explain each step of solving
- Include verification/check

For word problems:
- Explain HOW you identified what to calculate
- Show the logic from text to formula

GENERAL EXPLANATION RULES:
- Each explanation MUST be 3-7 SENTENCES
- Start with WHAT the correct answer is
- Then explain WHY it's correct
- Include the relevant FORMULA or CONCEPT if applicable
- For incorrect options: explain specifically why EACH one is wrong
- NEVER just say "because it's in the text" - EXPLAIN THE REASONING

BAD explanation examples (DO NOT USE):
- "Тачно је зато што пише у тексту" ❌
- "Одговор је тачан" ❌

GOOD explanation examples (USE THESE):
- "Тачан одговор је 24cm². Површина правоугаоника рачуна се као производ страница: P = a * b = 6 * 4 = 24cm². Други одговори су погрешни јер користе погрешну формулу или погрешно израчунавају." ✅
- "Нетачно. Збир углова у троуглу увек износи 180° без обзира на облик троугла. Ово следи из Теореме о збиру углова троугла." ✅
- "Одговор А је тачан. Користимо Питагорину теорему: a² + b² = c². За a=3 и b=4: 9 + 16 = 25, па је c = 5." ✅

LANGUAGE: Use the SAME LANGUAGE as the input text (Serbian Cyrillic: Ћ, Њ, Љ, Ш, Ч, Ж, etc.)

Return ONLY valid JSON array:
[
  {{
    "question_text": "Питање на српском језику?",
    "question_type": "multiple_choice",
    "options": [
      "Тачан одговор са рачуницом",
      "Погрешан одговор 1",
      "Погрешан одговор 2", 
      "Погрешан одговор 3"
    ],
    "correct_answer": "Тачан одговор са рачуницом",
    "explanation": "Тачан одговор је [A]. Користимо формулу [формула]. Заменом вредности добијамо [израчунавање]. Други одговори су погрешни јер [објашњење зашто].",
    "points": 1
  }},
  {{
    "question_text": "Да ли је следећа тврдња тачна: 'Зигурати су били трговачки центри'?",
    "question_type": "true_false", 
    "options": ["Тачно", "Нетачно"],
    "correct_answer": "Нетачно",
    "explanation": "Нетачно. Зигурати су били храмови посвећени богу Луни, а не трговачки центри. Они су служили као религијски објекти и астрономске осматрачнице.",
    "points": 1
  }},
  {{
    "question_text": "Које од следећих су биле карактеристике старог Египта?",
    "question_type": "checkbox",
    "options": [
      "Фараон као божански владар",
      "Пирамиде као гробнице",
      "Демократски систем владавине",
      "Развијена трговина и занати"
    ],
    "correct_answer": "Фараон као божански владар,Пирамиде као гробнице,Развијена трговина и занати",
    "explanation": "Египат није имао демократски систем. Фараон је био божански владар са апсолутном влашћу, градили су грандиозне пирамиде као краљевске гробнице, и имали су развијену трговину дуж Нила и занате.",
    "points": 2
  }}
]

Text:
{text}
"""
