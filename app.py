import streamlit as st
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import nltk
import re
import json
from nltk.corpus import stopwords

# Download stopwords if not already downloaded
nltk.download('stopwords')

# UI
st.set_page_config(page_title="NLP Job Listing Wordcloud", layout="centered")
st.title("Job Listing Wordcloud Generator")

st.markdown("Paste job listings or upload a JSON file to generate a wordcloud.")

# App Description
with st.expander("ℹ️ What does this app do?"):
    st.markdown("""
    **Job Listing Wordcloud Generator** analyzes job postings to create visual word clouds that highlight the most frequently mentioned terms, skills, and requirements.
    
    ### Features:
    - **Text Processing**: Cleans and processes job listing text
    - **Stopword Removal**: Filters out common words (the, and, or, etc.) in English or Spanish
    - **Visualization**: Creates beautiful word clouds showing term frequency
    - **Multiple Input Methods**: Upload JSON files or paste text directly
    - **Download**: Save your wordcloud as a PNG image
    
    ### Use Cases:
    - Identify trending skills in job postings
    - Compare requirements across different companies
    - Analyze job market trends
    - Extract key competencies from job descriptions
    """)

# JSON Format Description
with st.expander("📋 Supported JSON Formats"):
    st.markdown("""
    ### JSON File Structure
    Upload JSON files containing job listings. The app supports these formats:
    
    **1. Array of Job Objects:**
    ```json
    [
        {
            "title": "Data Scientist",
            "description": "We are looking for a data scientist...",
            "requirements": "Python, ML, SQL...",
            "responsibilities": "Build models, analyze data..."
        },
        {
            "title": "ML Engineer", 
            "description": "Join our ML team...",
            "requirements": "TensorFlow, Python..."
        }
    ]
    ```
    
    **2. Single Job Object:**
    ```json
    {
        "title": "NLP Engineer",
        "description": "Work on natural language processing...",
        "requirements": "Python, NLP, Deep Learning..."
    }
    ```
    
    **3. Object with Jobs Array:**
    ```json
    {
        "company": "Tech Corp",
        "jobs": [
            {
                "title": "AI Engineer",
                "description": "Develop AI solutions...",
                "requirements": "Python, TensorFlow..."
            }
        ]
    }
    ```
    
    ### Supported Fields
    The app automatically extracts text from these fields:
    - `description` - Job description text
    - `content` - General content field
    - `text` - Text content
    - `job_description` - Job description
    - `requirements` - Job requirements/skills
    - `responsibilities` - Job responsibilities
    
    **Note**: The app will combine text from all available fields to create the wordcloud.
    """)

# File upload
uploaded_file = st.file_uploader("📁 Upload JSON file (optional):", type=['json'])

# Text input
job_text = st.text_area("📋 Paste job listing(s):", height=300)

# Language selection
language = st.selectbox("🌐 Select language for stopword removal:", ['english', 'spanish'])

# Generate button
if st.button("🚀 Generate Wordcloud"):

    # Process input
    input_text = ""
    
    if uploaded_file is not None:
        try:
            # Read and parse JSON file
            json_data = json.load(uploaded_file)
            
            # Handle different JSON structures
            if isinstance(json_data, list):
                # If it's a list of job objects
                for job in json_data:
                    if isinstance(job, dict):
                        # Extract text from common job listing fields
                        for field in ['description', 'content', 'text', 'job_description', 'requirements', 'responsibilities']:
                            if field in job and job[field]:
                                input_text += str(job[field]) + " "
                    else:
                        input_text += str(job) + " "
            elif isinstance(json_data, dict):
                # If it's a single job object or has a jobs array
                if 'jobs' in json_data and isinstance(json_data['jobs'], list):
                    for job in json_data['jobs']:
                        if isinstance(job, dict):
                            for field in ['description', 'content', 'text', 'job_description', 'requirements', 'responsibilities']:
                                if field in job and job[field]:
                                    input_text += str(job[field]) + " "
                        else:
                            input_text += str(job) + " "
                else:
                    # Single job object
                    for field in ['description', 'content', 'text', 'job_description', 'requirements', 'responsibilities']:
                        if field in json_data and json_data[field]:
                            input_text += str(json_data[field]) + " "
            
            st.success(f"✅ Successfully processed JSON file with {len(json_data) if isinstance(json_data, list) else 1} job listing(s)")
            
        except json.JSONDecodeError:
            st.error("❌ Invalid JSON file. Please check the file format.")
            input_text = ""
        except Exception as e:
            st.error(f"❌ Error processing JSON file: {str(e)}")
            input_text = ""
    
    # Add text area input if provided
    if job_text.strip():
        input_text += " " + job_text.strip()
    
    if not input_text.strip():
        st.warning("Please paste some job listing text or upload a JSON file first.")
    else:
        # Text cleaning
        def clean_text(text):
            text = text.lower()
            text = re.sub(r'[^a-zA-Zñáéíóúü ]', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text

        cleaned_text = clean_text(input_text)
        stop_words = set(stopwords.words(language))
        filtered_words = ' '.join([word for word in cleaned_text.split() if word not in stop_words])

        # Generate wordcloud
        wordcloud = WordCloud(width=800, height=400, background_color='white', collocations=False).generate(filtered_words)

        # Display
        st.subheader("📊 Wordcloud Result")
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)

        # Download option
        wordcloud.to_file("wordcloud.png")
        with open("wordcloud.png", "rb") as img:
            st.download_button("💾 Download Wordcloud as PNG", img, "wordcloud.png", "image/png")
