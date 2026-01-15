import os
import time
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. Load Environment Variables
load_dotenv()

# 2. Define Guidelines per Level
# We store these in a dictionary to inject only the relevant one into the prompt.
LEVEL_GUIDELINES = {
    "A1": "Use very basic phrases and high-frequency vocabulary. Write short, isolated sentences. Avoid idioms. Focus on the most essential information only. Keep it extremely simple.",
    "A2": "Use frequently used expressions related to immediate relevance. Sentences should be simple but linked with basic connectors (y, pero, porque). Describe the content in simple, concrete terms.",
    "B1": "Use standard language and straightforward vocabulary. Text should be connected and clear. Explain main points regarding familiar matters. You may use simple subordinate clauses.",
    "B2": "Write with a degree of fluency and spontaneity. Use a wide range of vocabulary. You can explain viewpoints and advantages/disadvantages. The text should be detailed.",
    "C1": "Use flexible and effective language for social and professional purposes. The text should be well-structured, allowing for implicit meaning and longer, more complex sentences.",
    "C2": "Write with precision, distinguishing finer shades of meaning. Reconstruct arguments coherently. The text should be indistinguishable from a high-quality native Spanish newspaper."
}

# 3. Initialize the Model
llm = ChatGroq(
    temperature=0.1,
    model_name="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

# 4. Define Prompts
# We use StrOutputParser because we just want the raw translated string now, not complex JSON.

# Title Prompt
title_prompt = ChatPromptTemplate.from_template(
    """
    Translate the following news headline from Dutch to standard, neutral journalistic Spanish.
    Output ONLY the Spanish title. No quotes, no preamble.

    Dutch Title: {text}
    """
)

# Paragraph Prompt
paragraph_prompt = ChatPromptTemplate.from_template(
    """
    You are an expert translator. 
    Translate the following Dutch text segment into Spanish.
    
    TARGET LEVEL: {level}
    GUIDELINES: {guideline}
    
    IMPORTANT: 
    - Translate ONLY this specific paragraph. 
    - Maintain the exact information flow. 
    - Output ONLY the Spanish translation.
    
    Dutch Text: 
    {text}
    """
)

# Create Chains
title_chain = title_prompt | llm | StrOutputParser()
paragraph_chain = paragraph_prompt | llm | StrOutputParser()

def translate_article(title, text):
    """
    Translates title once, and then translates the body text paragraph-by-paragraph for each level.
    """
    print(f"  > Starting deep translation for: '{title}'")
    
    # --- Step 1: Translate Title ---
    try:
        title_es = title_chain.invoke({"text": title})
    except Exception as e:
        print(f"    X Error translating title: {e}")
        title_es = title

    # --- Step 2: Prepare Paragraphs ---
    # Split by double newline to get distinct paragraphs
    raw_paragraphs = text.split("\n\n")
    # Filter out empty strings just in case
    paragraphs = [p.strip() for p in raw_paragraphs if p.strip()]

    print(f"    - Detected {len(paragraphs)} paragraphs. Translating across 6 levels...")

    # Initialize results storage
    # content_map will look like: {'A1': ['Para 1', 'Para 2'], 'A2': ['Para 1', 'Para 2']...}
    content_map = {level: [] for level in LEVEL_GUIDELINES.keys()}
    
    # --- Step 3: Loop and Translate ---
    for i, p in enumerate(paragraphs):
        print(f"    - Processing Paragraph {i+1}/{len(paragraphs)}")
        
        for level, guideline in LEVEL_GUIDELINES.items():
            try:
                # Call LLM for this specific paragraph at this specific level
                translation = paragraph_chain.invoke({
                    "level": level,
                    "guideline": guideline,
                    "text": p
                })
                content_map[level].append(translation)
                
                # Rate Limit Protection: Sleep briefly between calls
                # Groq free tier is generous, but this prevents burst limit errors.
                time.sleep(0.5) 
                
            except Exception as e:
                print(f"      X Error on {level} para {i+1}: {e}")
                content_map[level].append("[Translation Error]")

    # --- Step 4: Reassemble ---
    # Join the paragraphs back together with double newlines
    final_output = {
        "title_es": title_es,
        "A1": "\n\n".join(content_map["A1"]),
        "A2": "\n\n".join(content_map["A2"]),
        "B1": "\n\n".join(content_map["B1"]),
        "B2": "\n\n".join(content_map["B2"]),
        "C1": "\n\n".join(content_map["C1"]),
        "C2": "\n\n".join(content_map["C2"]),
    }

    return final_output