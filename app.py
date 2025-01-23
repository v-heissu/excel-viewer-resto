import streamlit as st
import pandas as pd
import io
import requests

ITEMS_PER_PAGE = 50
EXCEL_URL = "https://github.com/v-heissu/excel-viewer-resto/blob/9a8ded98ec7faf25361de87748c629ea594c6eab/sample_fd.xlsx"

st.markdown("""
<style>
.floating-container { position: fixed; bottom: 20px; right: 20px; display: flex; flex-direction: column; gap: 10px; z-index: 999; }
.floating-button { background-color: #1f1f1f; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none; text-align: center; }
.pagination { padding: 20px; text-align: center; }
</style>
""", unsafe_allow_html=True)

def add_floating_buttons():
   st.markdown("""
       <div class="floating-container">
           <a href="#top" class="floating-button">⬆️ Top</a>
           <a href="#bottom" class="floating-button">⬇️ Bottom</a>
           <a href="#download" class="floating-button">💾 Download</a>
       </div>
   """, unsafe_allow_html=True)

def validate_and_setup_dataframe(df):
   if df.empty:
       raise ValueError("Excel file is empty")
       
   required_columns = ['URL', 'ImageURL', 'GooglePlaceID', 'ID']
   missing_cols = [col for col in required_columns if col not in df.columns]
   if missing_cols:
       raise ValueError(f"Missing columns: {', '.join(missing_cols)}")
       
   st.session_state.df = df
   st.session_state.page = 0
   st.session_state.col_mapping = {
       'url': 'URL',
       'image': 'ImageURL',
       'place_id': 'GooglePlaceID',
       'id': 'ID'
   }
   if 'da_controllare' not in st.session_state.df.columns:
       st.session_state.df['da_controllare'] = False

def display_data_chunk(df, start_idx, end_idx, col_mapping):
   for idx in range(start_idx, min(end_idx, len(df))):
       row = df.iloc[idx]
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
           st.write(f"URL: {row[col_mapping['url']]}")
           st.write(f"Place ID: {row[col_mapping['place_id']]}")
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

def main():
   st.title("Excel Image Viewer")
   add_floating_buttons()

   try:
       if 'df' not in st.session_state:
           with st.spinner('Loading data...'):
               response = requests.get(EXCEL_URL)
               if response.status_code != 200:
                   st.error(f"Failed to fetch Excel file: {response.status_code}")
                   return
               
               excel_data = io.BytesIO(response.content)
               try:
                   df = pd.read_excel(excel_data, engine='openpyxl')
                   validate_and_setup_dataframe(df)
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
