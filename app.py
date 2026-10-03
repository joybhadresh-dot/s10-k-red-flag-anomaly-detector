import streamlit as st
from textblob import TextBlob
import textstat

# Standard SEC red flag keywords indicative of risk or distress
RED_FLAGS = [
    "material weakness",
    "restatement",
    "going concern",
    "sec investigation",
    "subpoena",
    "fraud",
    "litigation",
    "whistleblower",
    "default",
    "breach of covenant",
    "unregistered sales",
    "insider trading",
    "resignation of auditor"
]

def analyze_10k(text):
    results = {}
    
    # 1. Keyword Anomaly Detection
    found_flags = {}
    lower_text = text.lower()
    for flag in RED_FLAGS:
        count = lower_text.count(flag)
        if count > 0:
            found_flags[flag] = count
    results["keywords"] = found_flags
    
    # 2. Sentiment Analysis (Polarity)
    blob = TextBlob(text)
    results["sentiment"] = blob.sentiment.polarity
    
    # 3. Readability / Fog Index (High index = potential obfuscation)
    results["fog_index"] = textstat.gunning_fog(text)
    
    return results

# Streamlit UI Configuration
st.set_page_config(page_title="10-K Red Flag Detector", page_icon="🚩")
st.title("SEC 10-K Red Flag Anomaly Detector 🚩")
st.write("""
Upload a text extract from an SEC 10-K filing. This tool analyzes the text for **risk keywords**, 
**negative sentiment**, and **linguistic obfuscation** (overly complex language used to hide poor performance).
""")

# File Uploader
uploaded_file = st.file_uploader("Upload 10-K Text File (.txt)", type="txt")

if uploaded_file is not None:
    text = uploaded_file.read().decode("utf-8")
    
    if len(text.strip()) == 0:
        st.error("The uploaded file is empty.")
    else:
        st.subheader("Analysis Results")
        with st.spinner("Analyzing document..."):
            results = analyze_10k(text)
            
            # --- Results: Keywords ---
            st.write("### 🔍 Risk Keywords Detected")
            if results["keywords"]:
                for kw, count in results["keywords"].items():
                    st.warning(f"**{kw.title()}**: Found {count} time(s)")
            else:
                st.success("No standard red flag keywords detected.")
                
            # --- Results: Sentiment ---
            st.write("### 🧠 Sentiment Analysis")
            sentiment = results["sentiment"]
            st.metric(label="Polarity Score (-1.0 to 1.0)", value=round(sentiment, 4))
            if sentiment < 0:
                st.error("Overall sentiment is negative. This often correlates with operational headwinds.")
            elif sentiment < 0.05:
                st.warning("Sentiment is highly neutral/cautious.")
            else:
                st.success("Overall sentiment leans positive.")
                
            # --- Results: Readability ---
            st.write("### 📖 Obfuscation Metric (Gunning Fog Index)")
            fog = results["fog_index"]
            st.metric(label="Fog Index Score", value=round(fog, 2))
            
            st.caption("*The Fog Index estimates the years of formal education needed to understand the text on a first reading.*")
            if fog > 18:
                st.error("🚩 **High Anomaly**: Text is extremely complex (Fog > 18). Management may be using dense jargon to obfuscate underlying issues.")
            elif fog > 14:
                st.warning("Text is moderately complex, which is standard for legal filings but borders on difficult.")
            else:
                st.success("Readability is straightforward and well within standard corporate limits.")
