import streamlit as st
from textblob import TextBlob
import textstat
from bs4 import BeautifulSoup 
import re # Added for text pattern matching

# Standard SEC red flag keywords indicative of risk or distress
RED_FLAGS = [
    "material weakness", "restatement", "going concern", "sec investigation", 
    "subpoena", "fraud", "litigation", "whistleblower", "default", 
    "breach of covenant", "unregistered sales", "insider trading", "resignation of auditor"
]

def analyze_10k(text, custom_query=""):
    results = {}
    
    # Clean text to remove extra newlines for a cleaner snippet display
    clean_text = " ".join(text.split())
    
    # 1. Standard Keyword Anomaly Detection with Context Snippets
    found_flags = {}
    for flag in RED_FLAGS:
        # Regex finds the keyword and captures up to 80 characters before and after it
        pattern = re.compile(r'(.{0,80})(' + re.escape(flag) + r')(.{0,80})', re.IGNORECASE)
        matches = pattern.findall(clean_text)
        
        if matches:
            found_flags[flag] = []
            for match in matches:
                before, kw, after = match
                # Format the snippet: trim edges and bold the exact keyword
                found_flags[flag].append(f"...{before.strip()} **{kw}** {after.strip()}...")
                
    results["keywords"] = found_flags
    
    # 2. Custom Query Detection with Context Snippets
    results["custom_query_snippets"] = []
    if custom_query:
        pattern = re.compile(r'(.{0,80})(' + re.escape(custom_query) + r')(.{0,80})', re.IGNORECASE)
        matches = pattern.findall(clean_text)
        for match in matches:
            before, kw, after = match
            results["custom_query_snippets"].append(f"...{before.strip()} **{kw}** {after.strip()}...")
        
    # 3. Sentiment Analysis (Polarity)
    blob = TextBlob(text)
    results["sentiment"] = blob.sentiment.polarity
    
    # 4. Readability / Fog Index
    results["fog_index"] = textstat.gunning_fog(text)
    
    return results

# Streamlit UI Configuration
st.set_page_config(page_title="10-K Red Flag Detector", page_icon="🚩")
st.title("SEC 10-K Red Flag Anomaly Detector 🚩")

# Custom Query Input
st.write("### Search for a Custom Query")
custom_query = st.text_input("Enter a specific keyword to query (e.g., 'liquidity', 'inventory', 'lawsuit'):")

# File Uploader
uploaded_file = st.file_uploader("Upload 10-K Text File (.txt)", type="txt")

if uploaded_file is not None:
    text = uploaded_file.read().decode("utf-8")
    
    if len(text.strip()) == 0:
        st.error("The uploaded file is empty.")
    else:
        st.subheader("Analysis Results")
        with st.spinner("Analyzing large document..."):
            results = analyze_10k(text, custom_query)
            
            # --- Results: Custom Query ---
            if custom_query:
                st.write(f"### 🎯 Query Results for '{custom_query}'")
                snippets = results["custom_query_snippets"]
                if snippets:
                    st.info(f"Found **{len(snippets)}** occurrence(s) in the text.")
                    for i, snippet in enumerate(snippets):
                        # Use blockquotes for readability
                        st.markdown(f"> **{i+1}.** {snippet}")
                else:
                    st.warning(f"No occurrences found for '{custom_query}'.")
            
            # --- Results: Keywords ---
            st.write("### 🔍 Risk Keywords Detected")
            if results["keywords"]:
                for kw, snippets in results["keywords"].items():
                    # st.expander creates a clickable dropdown for each keyword
                    with st.expander(f"⚠️ **{kw.title()}**: Found {len(snippets)} time(s)"):
                        for i, snippet in enumerate(snippets):
                            st.markdown(f"**{i+1}.** {snippet}")
                            st.divider() # Adds a clean line between snippets
            else:
                st.success("No standard red flag keywords detected.")
                
            # --- Results: Sentiment ---
            st.write("### 🧠 Sentiment Analysis")
            sentiment = results["sentiment"]
            st.metric(label="Polarity Score (-1.0 to 1.0)", value=round(sentiment, 4))
            if sentiment < 0:
                st.error("Overall sentiment is negative. This often correlates with operational headwinds.")
            else:
                st.success("Overall sentiment leans positive or neutral.")
                
            # --- Results: Readability ---
            st.write("### 📖 Obfuscation Metric (Gunning Fog Index)")
            fog = results["fog_index"]
            st.metric(label="Fog Index Score", value=round(fog, 2))
            if fog > 18:
                st.error("🚩 **High Anomaly**: Text is extremely complex (Fog > 18). Management may be obfuscating data.")
            elif fog > 14:
                st.warning("Text is moderately complex (Standard for legal filings).")
            else:
                st.success("Readability is straightforward.")
