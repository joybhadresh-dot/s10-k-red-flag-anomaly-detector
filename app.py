import streamlit as st
from textblob import TextBlob
import textstat
import re
import PyPDF2
import io

# Standard SEC red flag keywords indicative of risk, distress, or corporate law issues
RED_FLAGS = [
    "material weakness", "restatement", "going concern", "sec investigation", 
    "subpoena", "fraud", "litigation", "whistleblower", "default", 
    "breach of covenant", "unregistered sales", "insider trading", "resignation of auditor"
]

def process_uploaded_file(uploaded_file):
    """Dynamically reads PDFs page-by-page or standard files as a single text block."""
    pages_data = []
    file_name = uploaded_file.name.lower()
    
    try:
        # Handle PDFs
        if file_name.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            for i, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if text:
                    clean_text = " ".join(text.split())
                    pages_data.append({"page_num": i + 1, "text": clean_text})
                    
        # Handle TXT, CSV, MD, or any other file type by decoding as raw text
        else:
            text = uploaded_file.read().decode("utf-8")
            if text:
                clean_text = " ".join(text.split())
                # Assign all text to "Page 1" for compatibility with the UI
                pages_data.append({"page_num": 1, "text": clean_text})
                
    except Exception as e:
        st.error(f"Error processing file. Please ensure it is a valid text or PDF document. Details: {e}")
        
    return pages_data

def analyze_document(pages_data, custom_query=""):
    results = {
        "keywords": {},
        "custom_query_snippets": [],
        "full_text": ""
    }
    
    for page in pages_data:
        page_num = page["page_num"]
        page_text = page["text"]
        results["full_text"] += page_text + " "
        
        # 1. Standard Keyword Anomaly Detection with Page Tracking
        for flag in RED_FLAGS:
            pattern = re.compile(r'(.{0,80})(' + re.escape(flag) + r')(.{0,80})', re.IGNORECASE)
            matches = pattern.findall(page_text)
            
            if matches:
                if flag not in results["keywords"]:
                    results["keywords"][flag] = []
                    
                for match in matches:
                    before, kw, after = match
                    snippet = f"...{before.strip()} **{kw}** {after.strip()}..."
                    results["keywords"][flag].append({"page": page_num, "snippet": snippet})
                    
        # 2. Custom Query Detection with Page Tracking
        if custom_query:
            pattern = re.compile(r'(.{0,80})(' + re.escape(custom_query) + r')(.{0,80})', re.IGNORECASE)
            matches = pattern.findall(page_text)
            for match in matches:
                before, kw, after = match
                snippet = f"...{before.strip()} **{kw}** {after.strip()}..."
                results["custom_query_snippets"].append({"page": page_num, "snippet": snippet})
                
    # 3. Aggregate Sentiment and Readability on the full document
    if results["full_text"].strip():
        blob = TextBlob(results["full_text"])
        results["sentiment"] = blob.sentiment.polarity
        results["fog_index"] = textstat.gunning_fog(results["full_text"])
    else:
        results["sentiment"] = 0
        results["fog_index"] = 0
        
    return results

# ==========================================
# UI CONFIGURATION & STYLING
# ==========================================
st.set_page_config(page_title="10-K Red Flag Detector", page_icon="🚩", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 8px; }
    [data-testid="stSidebar"] { background-color: #1e1e1e; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR CONTROLS
# ==========================================
with st.sidebar:
    st.title("⚙️ Control Panel")
    st.write("Upload a corporate disclosure to scan for statutory and operational risks.")
    
    # Removed the 'type' restriction to accept all files
    uploaded_file = st.file_uploader("Upload Document (PDF, TXT, etc.)")
    
    st.divider()
    st.write("### Targeted Search")
    custom_query = st.text_input("Custom keyword (e.g., 'liquidity', 'IFRS', 'deferred tax'):")

# ==========================================
# MAIN DASHBOARD AREA
# ==========================================
st.title("SEC 10-K Red Flag Anomaly Detector 🚩")

if uploaded_file is None:
    st.info("👈 Please upload a document in the sidebar to begin the analysis.")
else:
    with st.spinner("Extracting and analyzing document..."):
        pages_data = process_uploaded_file(uploaded_file)
        
        if not pages_data:
            st.error("Could not extract readable text from this file. It may be empty or an unsupported format (like a JPEG).")
        else:
            results = analyze_document(pages_data, custom_query)
            
            tab1, tab2, tab3 = st.tabs(["📊 Executive Summary", "🚨 Risk Keywords (Red Flags)", "🎯 Custom Query Results"])
            
            # --- TAB 1: SUMMARY ---
            with tab1:
                st.write("### Document Intelligence")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # If it's a text file, it will show as 1 page. If PDF, it shows total pages.
                    st.metric(label="Total Pages Scanned", value=len(pages_data))
                
                with col2:
                    sentiment = results["sentiment"]
                    st.metric(label="Sentiment Polarity (-1.0 to 1.0)", value=round(sentiment, 4))
                
                with col3:
                    fog = results["fog_index"]
                    st.metric(label="Gunning Fog Index", value=round(fog, 2))
                
                st.divider()
                st.write("#### Metric Analysis")
                if sentiment < 0:
                    st.error("**Sentiment:** Negative. This often correlates with operational headwinds or poor financial outlooks.")
                else:
                    st.success("**Sentiment:** Positive/Neutral. Management tone is stable.")
                    
                if fog > 18:
                    st.error("**Readability:** High Anomaly (Fog > 18). The text is extremely complex, suggesting potential obfuscation of underlying issues.")
                elif fog > 14:
                    st.warning("**Readability:** Moderately complex. Standard for legal and accounting filings, but dense.")
                else:
                    st.success("**Readability:** Straightforward and accessible.")

            # --- TAB 2: RED FLAGS ---
            with tab2:
                st.write("### Detected Risk Factors")
                st.write("Click on any detected category to see the exact context.")
                
                if results["keywords"]:
                    for kw, matches in results["keywords"].items():
                        with st.expander(f"⚠️ **{kw.title()}** (Found {len(matches)} time(s))"):
                            for i, match in enumerate(matches):
                                st.markdown(f"📍 **Page {match['page']}**")
                                st.markdown(f"> {match['snippet']}")
                                if i < len(matches) - 1:
                                    st.divider()
                else:
                    st.success("No standard red flag keywords detected in this document.")

            # --- TAB 3: CUSTOM QUERY ---
            with tab3:
                if custom_query:
                    st.write(f"### Results for: '{custom_query}'")
                    snippets = results["custom_query_snippets"]
                    
                    if snippets:
                        st.info(f"Found **{len(snippets)}** occurrence(s).")
                        for match in snippets:
                            st.markdown(f"📍 **Page {match['page']}**")
                            st.markdown(f"> {match['snippet']}")
                            st.divider()
                    else:
                        st.warning(f"No occurrences found for '{custom_query}'.")
                else:
                    st.info("Enter a custom query in the sidebar to search the document.")
