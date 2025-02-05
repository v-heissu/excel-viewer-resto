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
.pagination { padding: 20px; text-align: center; }
.analysis-box { border: 1px solid #ddd; padding: 10px; margin-top: 10px; border-radius: 5px; }
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
   
   if 'image_analysis' not in df.columns:
       df['image_analysis'] = df[st.session_state.col_mapping['image']].apply(
           lambda x: analyze_image(x, analysis_cache) if pd.notna(x) else None
       )
   
   st.session_state.df = df
   st.session_state.page = 0
   
   if 'da_controllare' not in st.session_state.df.columns:
       st.session_state.df['da_controllare'] = False

def display_data_chunk(df, start_idx, end_idx, col_mapping):
   for idx in range(start_idx, min(end_idx, len(df))):
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

def display_pagination(total_pages):
   cols = st.columns(4)
   with cols[0]:
       if st.button('⏮️ First', key='first'):
           st.session_state.page = 0
   with cols[1]:
       if st.button('◀️ Prev', key='prev') and st.session_state.page > 0:
           st.session_state.page -= 1
   with cols[2]:
       if st.button('Next ▶️', key='next') and st.session_state.page < total_pages - 1:
           st.session_state.page += 1 
   with cols[3]:
       if st.button('Last ⏭️', key='last'):
           st.session_state.page = total_pages - 1
   
   st.write(f'Page {st.session_state.page + 1} of {total_pages}')

def display_data_and_pagination():
   df = st.session_state.df
   total_pages = (len(df) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
   
   col1, col2, col3 = st.columns([1, 2, 1])
   with col2:
       page = st.number_input('Page', min_value=1, max_value=total_pages, value=st.session_state.page + 1)
       st.session_state.page = page - 1
   
   start_idx = st.session_state.page * ITEMS_PER_PAGE
   end_idx = start_idx + ITEMS_PER_PAGE
   
   display_data_chunk(df, start_idx, end_idx, st.session_state.col_mapping)
   
   st.markdown('<div class="pagination">', unsafe_allow_html=True)
   display_pagination(total_pages)
   st.markdown('</div>', unsafe_allow_html=True)

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
   st.title("Excel Image Viewer with AI Analysis")
   add_floating_buttons()

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

       display_data_and_pagination()
       handle_download()
       st.markdown('<div id="bottom"></div>', unsafe_allow_html=True)

   except Exception as e:
       st.error(f"Error: {str(e)}")

if __name__ == "__main__":
   main()
