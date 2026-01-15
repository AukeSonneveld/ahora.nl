import streamlit as st
import json
import os
from datetime import datetime

# --- CONFIGURATION ---
DATA_FILE = "data/news.json"
st.set_page_config(
    page_title="Ahora.nl - Dutch News in Spanish",
    page_icon="🇪🇸",
    layout="centered"
)

# --- LOAD DATA ---
@st.cache_data(ttl=3600)
def load_news():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading news data: {e}")
        return []

articles = load_news()

# --- SIDEBAR (INFO ONLY) ---
st.sidebar.header("About")
st.sidebar.info(
    """
    **Project Info**
    
    This is an AI Portfolio project by Auke Sonneveld.
    
    **Stack:**
    - Source: NOS.nl (Scraped)
    - LLM: Llama 3.3 70B (Groq)
    - Framework: LangChain
    - Frontend: Streamlit
    """
)

# --- TOP LAYOUT (Title + Toggle) ---
col_header, col_toggle = st.columns([5, 1])

with col_toggle:
    # A simple toggle switch
    dark_mode = st.toggle("Dark Mode", value=True)

# --- DYNAMIC CSS (Based on Toggle) ---
text_color = "#FFFFFF" if dark_mode else "#000000"
bg_color = "#0E1117" if dark_mode else "#FFFFFF"
sub_color = "#AAAAAA" if dark_mode else "#555555"

# We inject this CSS to override Streamlit's defaults
st.markdown(f"""
    <style>
    /* 1. Force the main background color */
    .stApp {{
        background-color: {bg_color};
    }}
    
    /* 2. FORCE TEXT COLOR (General) */
    .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp span {{
        color: {text_color} !important;
    }}
    
    /* 3. FORCE TOGGLE LABEL COLOR (Specific Fix) */
    div[data-testid="stToggle"] label p {{
        color: {text_color} !important;
    }}
    
    /* 4. Custom Title Classes */
    .main-title {{
        font-family: 'Helvetica', sans-serif;
        color: #D32F2F !important; /* Spanish Red - Always Red */
        font-size: 3em;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0px;
        margin-top: -20px;
    }}
    .sub-title {{
        text-align: center;
        color: {sub_color} !important;
        font-style: italic;
        margin-bottom: 20px;
    }}
    
    /* 5. Center the radio buttons */
    div[role="radiogroup"] {{
        justify-content: center;
    }}
    
    /* 6. Tweaking the image */
    img {{
        border-radius: 8px;
        margin-bottom: 15px;
    }}
    </style>
""", unsafe_allow_html=True)

# --- MAIN TITLE ---
with col_header:
    st.markdown('<div class="main-title">Ahora.nl</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Dutch News, Adapted for your Spanish Level</div>', unsafe_allow_html=True)

# --- LEVEL SELECTION ---
if "level" not in st.session_state:
    st.session_state.level = "B1"

selected_level = st.radio(
    "Choose your proficiency level:",
    ["A1", "A2", "B1", "B2", "C1", "C2"],
    index=["A1", "A2", "B1", "B2", "C1", "C2"].index(st.session_state.level),
    horizontal=True
)
st.session_state.level = selected_level

st.markdown("---") 

# --- NEWS FEED ---
if not articles:
    st.warning("No news found. Please run the backend pipeline first.")
else:
    for article in articles:
        with st.container():
            # 1. IMAGE
            if article.get("image_url"):
                st.image(article["image_url"], width="stretch")
            else:
                st.empty() 

            # 2. HEADLINES & METADATA
            spanish_title = article.get("title_es", article["title"])
            st.subheader(spanish_title)
            
            if "title_es" in article:
                st.caption(f"🇳🇱 {article['title']}")
            
            date_str = article.get("published", "")
            st.caption(f"📅 {date_str} | Source: NOS.nl")
            
            # 3. CONTENT
            translation_text = article["translations"].get(selected_level, "Translation not available.")
            
            st.markdown(f"{translation_text}")
            
            # 4. EXPANDER
            with st.expander("Show Original Dutch Text"):
                st.write(article.get("original_text", "No original text available."))
                st.caption(f"[Read full article on NOS]({article['url']})")
            
            st.divider()