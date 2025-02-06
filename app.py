import streamlit as st
import pandas as pd
import io
import requests
import os
from openai import OpenAI
import base64
from dotenv import load_dotenv
import json
from pathlib import Path

load_dotenv()

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("OpenAI API key not found in secrets or environment variables")
    st.stop()

ITEMS_PER_PAGE = 50
EXCEL_URL = "https://raw.githubusercontent.com/v-heissu/excel-viewer-resto/9a8ded98ec7faf25361de87748c629ea594c6eab/sample_fd.xlsx"
ANALYSIS_CACHE_FILE = "image_analysis_cache.json"

client = OpenAI(api_key=OPENAI_API_KEY)

st.markdown("""
<style>
.floating-container { position: fixed; bottom: 20px; right: 20px; display: flex; flex-direction: column; gap: 10px; z-index: 999; }
.floating-button { background-color: #1f1f1f; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none; text-align: center; }
</style>
""", unsafe_allow_html=True)

def load_or_create_analysis_cache():
    if Path(ANALYSIS_CACHE_FILE).exists():
        with open(ANALYSIS_CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_analysis_cache(cache):
    with open(ANALYSIS_CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def analyze_image(image_url, analysis_cache):
    if image_url in analysis_cache:
        return analysis_cache[image_url]
        
    try:
        image_content = requests.get(image_url).content
        
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": """Analyze this image and provide a JSON with:
                        {
                            "type": ["plate"|"signboard"|"other"],
                            "short_description": "max 5 keywords",
                            "alt": "alt tag content following SEO guidelines",
                            "verbose_description": "detailed description - max 25 words"
                        }"""},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64.b64encode(image_content).decode('utf-8')}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        
        analysis = response.choices[0].message.content
        analysis_cache[image_url] = analysis
        save_analysis_cache(analysis_cache)
        return analysis
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

def add_floating_buttons():
    st.markdown("""
        <div class="floating-container">
            <a href="#top" class="floating-button">⬆️ Top</a>
            <a href="#bottom" class="floating-button">⬇️ Bottom</a>
            <a href="#download" class="floating-button">💾 Download</a>
        </div>
    """, unsafe_allow_html=True)

def validate_and_setup_dataframe(df, analysis_cache):
    if df.empty:
        raise ValueError("Excel file is empty")
        
    required_columns = ['URL', 'ImageURL', 'GooglePlaceID', 'ID']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns: {', '.join(missing_cols)}")
    
    st.session_state.col_mapping = {
        'url': 'URL',
        'image': 'ImageURL',
        'place_id': 'GooglePlaceID',
        'id': 'ID'
    }
    
    # Limit to first 50 rows
    df = df.head(50)
    
    if 'image_analysis' not in df.columns:
        df['image_analysis'] = df[st.session_state.col_mapping['image']].apply(
            lambda x: analyze_image(x, analysis_cache) if pd.notna(x) else None
        )
    
    st.session_state.df = df
    
    if 'da_controllare' not in st.session_state.df.columns:
        st.session_state.df['da_controllare'] = False

def display_data(df, col_mapping):
    for idx in range(len(df)):
        row = df.iloc[idx]
        if pd.notna(row['image_analysis']):
            col1, col2 = st.columns([1, 3])
            with col1:
                try:
                    if pd.notna(row[col_mapping['image']]):
                        st.image(row[col_mapping['image']], width=200)
                    else:
                        st.write("No image")
                except:
                    st.write("Error loading image")
            
            with col2:
                analysis_text = row['image_analysis']
                try:
                    cleaned_text = analysis_text.replace("```json", "").replace("```", "").strip()
                    analysis = json.loads(cleaned_text)
                    st.markdown(f"""**URL:** {row[col_mapping['url']]}  
                    **Place ID:** {row[col_mapping['place_id']]}  
                    **Type:** {analysis.get('type', 'N/A')}  
                    **Short Description:** {analysis.get('short_description', 'N/A')}  
                    **Alt:** {analysis.get('alt', 'N/A')}  
                    **Description:** {analysis.get('verbose_description', 'N/A')}""")
                except json.JSONDecodeError:
                    st.write("Analysis:", analysis_text)
                
                df.iat[idx, df.columns.get_loc('da_controllare')] = st.checkbox(
                    "Da controllare",
                    key=f"check_{idx}",
                    value=df.iat[idx, df.columns.get_loc('da_controllare')]
                )

def handle_download():
    selected_df = st.session_state.df[st.session_state.df['da_controllare']]
    if not selected_df.empty:
        st.markdown('<div id="download"></div>', unsafe_allow_html=True)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            selected_df.to_excel(writer, index=False)
        output.seek(0)
        
        st.download_button(
            "Download Selected",
            output,
            "selected_items.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

def load_excel_file():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(EXCEL_URL, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch Excel file: {response.status_code}")
        
    excel_data = io.BytesIO(response.content)
    excel_data.seek(0)
    return pd.read_excel(excel_data, engine='openpyxl')

def main():
    st.title("Restaurant Cards Image Viewer with AI Analysis")
    
    try:
        analysis_cache = load_or_create_analysis_cache()
        
        if 'df' not in st.session_state:
            with st.spinner('Loading data and analyzing images...'):
                try:
                    df = load_excel_file()
                    validate_and_setup_dataframe(df, analysis_cache)
                except Exception as e:
                    st.error(f"Error reading Excel: {str(e)}")
                    return
        
        # Extract types from analysis for filtering
        types = set()
        for analysis in st.session_state.df['image_analysis'].dropna():
            try:
                analysis_json = json.loads(analysis.replace("```json", "").replace("```", "").strip())
                if isinstance(analysis_json.get('type'), list):
                    types.update(analysis_json['type'])
                else:
                    types.add(analysis_json.get('type'))
            except:
                continue
        
        # Add filter
        selected_types = st.multiselect('Filter by Type:', list(sorted(types)))
        
        # Filter dataframe based on selection
        filtered_df = st.session_state.df
        if selected_types:
            filtered_df = filtered_df[filtered_df['image_analysis'].apply(lambda x: any(t in json.loads(x.replace("```json", "").replace("```", "").strip()).get('type', []) for t in selected_types) if pd.notna(x) else False)]
        
        add_floating_buttons()
        display_data(filtered_df, st.session_state.col_mapping)
        handle_download()
        st.markdown('<div id="bottom"></div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
