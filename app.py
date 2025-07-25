import streamlit as st
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import nltk
import re
import json
from nltk.corpus import stopwords
import openai
import PyPDF2
import io
import os
from dotenv import load_dotenv

load_dotenv()  # Loads from .env file

openai_api_key = os.getenv("OPENAI_API_KEY")


# Download stopwords if not already downloaded
nltk.download('stopwords')

# UI
st.set_page_config(page_title="NLP Job Listing Wordcloud", layout="centered")
st.title("Job Listing Wordcloud Generator & CV Analysis")

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
    - **CV Analysis**: Upload your CV to get AI-powered matching analysis with job requirements
    
    ### Use Cases:
    - Identify trending skills in job postings
    - Compare requirements across different companies
    - Analyze job market trends
    - Extract key competencies from job descriptions
    - Evaluate CV-job fit using AI analysis
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

        # Store wordcloud and job text in session state
        st.session_state.wordcloud = wordcloud
        st.session_state.job_text = input_text
        st.session_state.filtered_words = filtered_words

# Display wordcloud (either newly generated or cached)
if 'wordcloud' in st.session_state:
    st.subheader("📊 Wordcloud Result")
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.imshow(st.session_state.wordcloud, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig)

    # Download option for wordcloud
    st.session_state.wordcloud.to_file("wordcloud.png")
    with open("wordcloud.png", "rb") as img:
        st.download_button("💾 Download Wordcloud as PNG", img, "wordcloud.png", "image/png")

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return ""

def analyze_cv_job_match(cv_text, job_text, api_key=None):
    """Analyze CV-job match using OpenAI"""
    try:
        # Get API key from environment variable
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Initialize OpenAI client with API key
        client = openai.OpenAI(api_key=openai_api_key)
        
        prompt = f"""
        Analyze how well this CV matches the job requirements. Provide a detailed assessment including:

        **Job Requirements:**
        {job_text[:2000]}...

        **CV Content:**
        {cv_text[:2000]}...

        Please provide:
        1. **Match Status** - If the candidate is a good match, state "✅ MATCH" in bold. If the candidate is not a good match, state "❌ NO MATCH" in bold
        """

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert HR professional and career advisor. Provide honest, constructive feedback on CV-job matching."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error analyzing CV: {str(e)}"

# CV Analysis Section - Only show after wordcloud is generated
if 'job_text' in st.session_state:
    st.markdown("---")
    st.subheader("📄 CV Analysis & Job Matching")

    # CV Upload
    cv_uploaded_file = st.file_uploader("📄 Upload your CV (PDF or TXT):", type=['pdf', 'txt'])

    # Analyze button
    if st.button("🔍 Analyze CV-Job Match"):
        # Get CV text
        cv_content = ""
        
        if cv_uploaded_file is not None:
            if cv_uploaded_file.type == "application/pdf":
                cv_content = extract_text_from_pdf(cv_uploaded_file)
            else:
                cv_content = cv_uploaded_file.getvalue().decode("utf-8")
        
        if not cv_content.strip():
            st.error("❌ Please upload a CV file first.")
        else:
            with st.spinner("🤖 Analyzing your CV against job requirements..."):
                analysis_result = analyze_cv_job_match(cv_content, st.session_state.job_text, None)
                
            st.subheader("📊 CV-Job Match Analysis")
            st.markdown(analysis_result)
            
            # Save analysis
            st.session_state.cv_analysis = analysis_result
            st.session_state.cv_content = cv_content
