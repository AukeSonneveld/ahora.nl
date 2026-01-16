import os
import time
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. Load Environment Variables
load_dotenv()

# 2. Define Guidelines per Level
LEVEL_GUIDELINES = {
    "A1": "Use very basic phrases and high-frequency vocabulary. Grammar: Use primarily the Present Indicative. Avoid past tenses. Write short, isolated sentences. Avoid idioms. Focus on the most essential information only. Keep it extremely simple.",
    "A2": "Use frequently used expressions related to immediate relevance. Grammar: Use Present, Pretérito Perfecto and Indefinido for actions, and Imperfecto for descriptions. Sentences should be simple but linked with basic connectors (y, pero, porque). Describe the content in simple, concrete terms.",
    "B1": "Use standard language and straightforward vocabulary. Grammar: Use all Past tenses (Indefinido vs Imperfecto) correctly. Use Future Simple. You may use the Present Subjunctive for simple opinions. Text should be connected and clear.",
    "B2": "Write with a degree of fluency and spontaneity. Grammar: Use Conditional, Future Perfect, and Subjunctive moods (Present & Imperfect) freely. Use a wide range of vocabulary. You can explain viewpoints and advantages/disadvantages. The text should be detailed.",
    "C1": "Use flexible and effective language for social and professional purposes. Grammar: Use complex Subjunctive structures and Conditional sentences. The text should be well-structured, allowing for implicit meaning and longer, more complex sentences.",
    "C2": "Write with precision, distinguishing finer shades of meaning. Grammar: Use all tenses and moods freely and precisely (including literary nuances). Reconstruct arguments coherently. The text should be indistinguishable from a high-quality native Spanish newspaper."
}

# 3. Initialize the Model
llm = ChatGroq(
    temperature=0.1,
    model_name="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

# 4. Define Prompts

# Title Prompt
title_prompt = ChatPromptTemplate.from_template(
    """
    Translate the following news headline from Dutch to standard, neutral journalistic Spanish.
    Output ONLY the Spanish title. No quotes, no preamble.

    Dutch Title: {text}
    """
)

# Article Prompt (Full Text)
article_prompt = ChatPromptTemplate.from_template(
    """
    You are an expert translator. 
    Translate the following Dutch news article into Spanish.
    
    TARGET LEVEL: {level}
    GUIDELINES: {guideline}
    
    IMPORTANT INSTRUCTIONS:
    - Translate the ENTIRE text below.
    - **PRESERVE THE PARAGRAPH STRUCTURE**: Keep the same number of paragraphs as the original.
    - Do not output any intro or outro text (like "Here is the translation").
    - Output ONLY the Spanish translation.
    
    Dutch Text: 
    {text}
    """
)

# Create Chains
title_chain = title_prompt | llm | StrOutputParser()
article_chain = article_prompt | llm | StrOutputParser()

def translate_article(title, text):
    """
    Translates title once, and then translates the ENTIRE body text for each level.
    """
    print(f"  > Starting full-text translation for: '{title}'")
    
    # --- Step 1: Translate Title ---
    try:
        title_es = title_chain.invoke({"text": title})
    except Exception as e:
        print(f"    X Error translating title: {e}")
        title_es = title

    # Initialize results storage
    final_output = {
        "title_es": title_es
    }

    # --- Step 2: Loop Levels (Not Paragraphs) ---
    print(f"    - Translating full article across {len(LEVEL_GUIDELINES)} levels...")

    for level, guideline in LEVEL_GUIDELINES.items():
        try:
            # print(f"      - Generating {level} version...")
            
            # Call LLM with the FULL text
            translation = article_chain.invoke({
                "level": level,
                "guideline": guideline,
                "text": text
            })
            
            final_output[level] = translation.strip()
            
            # Rate Limit Protection
            time.sleep(1.0) 
            
        except Exception as e:
            print(f"      X Error on level {level}: {e}")
            final_output[level] = "[Translation Error]"

    return final_output