# -*- coding: utf-8 -*-
"""
================================================================================
QUIZ PROMPT TEMPLATES
================================================================================

Verzija: 1.2.0 - Fixed ALL curly brace escaping for Python format()
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

IMPORTANT - QUESTION TYPES (use variety!):
- 30% multiple_choice - 1 correct answer, 4 plausible options
- 15% checkbox - 2-4 correct answers, 4 options (select ALL that apply)
- 10% true_false - balanced mix of TRUE and FALSE statements  
- 15% sequencing - Sort elements in correct order (e.g., chronological events, steps)
- 15% matching - Connect related pairs (left column to right column via drag/drop)
- 15% categorization - Put items in correct categories (buckets)

===============================================================================
SEMANTIC RULES FOR MULTIPLE_CHOICE vs CHECKBOX:
- MULTIPLE_CHOICE: EXACTLY ONE correct answer. The "correct_answer" field must contain a SINGLE option text that matches exactly one of the options in the "options" array.
- CHECKBOX: 2+ correct answers. The "correct_answer" field must contain MULTIPLE option texts separated by commas.
- IMPORTANT: NEVER create a multiple_choice question where ALL options are correct. If all options are valid answers, it MUST be a checkbox question.
- IMPORTANT: NEVER create a checkbox question where only 1 option is correct. That MUST be multiple_choice.

BAD multiple_choice (DO NOT USE):
- options: ["Option A", "Option B", "Option C", "Option D"], correct_answer: "Option A,Option B,Option C,Option D" (ALL correct → must be checkbox)
- options: ["Option A", "Option B", "Option C", "Option D"], correct_answer: "Option A,Option B" (multiple correct → must be checkbox)

GOOD multiple_choice (USE THESE):
- options: ["Option A text", "Option B text", "Option C text", "Option D text"], correct_answer: "Option A text" (exactly one correct)
- options: ["Only US president", "Only UK prime minister", "Both", "Neither"], correct_answer: "Only US president" (single correct answer)

GOOD checkbox (USE THESE):
- options: ["Option A", "Option B", "Option C", "Option D"], correct_answer: "Option A,Option C" (exactly 2 correct)
- options: ["Python", "HTTP", "Java", "CSS"], correct_answer: "Python,Java" (2 of 4 correct)

===============================================================================
SEQUENCING QUESTIONS - Detailed Instructions:
- Provide 3-5 elements that MUST be sorted in correct order
- Elements should be: chronological events, steps in a process, sizes, dates
- correct_answer: JSON array AS STRING with exact order
- Example: correct_answer: "[Element1, Element2, Element3]"
- Options must be the elements in WRONG order initially

MATCHING QUESTIONS - Detailed Instructions:
- Provide 3-5 pairs to connect (left-right)
- Left items: Letters A, B, C, D, E with values
- Right items: Matching values/definitions/years
- correct_answer: JSON object AS STRING mapping left to right
- Example: correct_answer: '{{{{"A": "Value1", "B": "Value2", "C": "Value3"}}}}'

CATEGORIZATION QUESTIONS - Detailed Instructions:
- Provide 5-8 items to categorize
- Define 2-3 categories in extra_data.categories
- Each item belongs to EXACTLY ONE category
- correct_answer: JSON object AS STRING
- Example: correct_answer: '{{{{"Item1": "Category1", "Item2": "Category2"}}}}'
- extra_data: '{{{{"categories": ["Category1", "Category2", "Category3"]}}}}'

TEXT_INPUT QUESTIONS - Detailed Instructions:
- Simple factual questions with specific answers
- Use case_insensitive: true for fuzzy matching
- Can also set exact_word: false for partial matches
- correct_answer: The exact expected answer string

QUESTION QUALITY - Make questions ANALYTICAL and THOUGHT-PROVOKING:
- NOT: "Koji je glavni grad Mesopotamije?" (simple recall)
- YES: "Zasto su gradovi Mesopotamije nastajali na rekama? Objasni geografski i ekonomski razlog."
- NOT: "Sta je hram?" (definition only)
- YES: "Cemu su sluzili zikgurati u drevnoj Mesopotamiji i kako se njihova funkcija razlikovala od obicnih hramova?"

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
- Example: "Povrsina trougla se racuna kao polovina proizvoda osnovice i visine: P = (a * h) / 2. Za a=6 i h=4, dobijamo P = (6 * 4) / 2 = 12cm2"

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
- "Tacno je zato sto pise u tekstu" 
- "Odgovor je tacan" 

GOOD explanation examples (USE THESE):
- "Tacan odgovor je 24cm2. Povrsina pravougaonika racuna se kao proizvod stranica: P = a * b = 6 * 4 = 24cm2. Drugi odgovori su pogresni jer koriste pogresnu formulu ili pogresno izracunavaju." 
- "Netacno. Zbir uglova u trouglu uvek iznosi 180 stepeni bez obzira na oblik trougla. Ovo sledi iz Teoreme o zbiru uglova trougla." 
- "Odgovor A je tacan. Koristimo Pitagorinu teoremu: a2 + b2 = c2. Za a=3 i b=4: 9 + 16 = 25, pa je c = 5." 

CRITICAL: USE SERBIAN LATIN SCRIPT ONLY (a, b, c, c, d, dj, e, f, g, h, i, j, k, l, lj, m, n, nj, o, p, r, s, s, t, u, v, z, z)
- DO NOT USE CYRILLIC

Return ONLY valid JSON array. Each object must have:
- question_text, question_type, options, correct_answer, explanation, points
- For sequencing: correct_answer is JSON array as STRING like "[first,second,third]"
- For matching: correct_answer is JSON object as STRING like left-right pairs
- For categorization: add extra_data with categories array
- For text_input: add case_insensitive:true

Text:
{text}
"""
