import streamlit as st
import pandas as pd
import io
import requests

ITEMS_PER_PAGE = 50
EXCEL_URL = "https://github.com/v-heissu/excel-viewer-resto/blob/9a8ded98ec7faf25361de87748c629ea594c6eab/sample_fd.xlsx"

# ... (keep existing styles) ...

def main():
    st.title("Excel Image Viewer")
    
    # Add floating buttons
    st.markdown("""
        <div class="floating-container">
            <a href="#top" class="floating-button">⬆️ Top</a>
            <a href="#bottom" class="floating-button">⬇️ Bottom</a>
            <a href="#download" class="floating-button">💾 Download</a>
        </div>
    """, unsafe_allow_html=True)

    try:
        if 'df' not in st.session_state:
            with st.spinner('Loading data...'):
                response = requests.get(EXCEL_URL)
                if response.status_code != 200:
                    st.error(f"Failed to fetch Excel file. Status code: {response.status_code}")
                    return
                
                excel_data = io.BytesIO(response.content)
                try:
                    df = pd.read_excel(excel_data)
                    if df.empty:
                        st.error("Excel file is empty")
                        return
                        
                    required_columns = ['URL', 'ImageURL', 'GooglePlaceID', 'ID']
                    if not all(col in df.columns for col in required_columns):
                        st.error(f"Missing required columns. Expected: {', '.join(required_columns)}")
                        st.write("Available columns:", df.columns.tolist())
                        return
                        
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
                        
                except Exception as e:
                    st.error(f"Error reading Excel file: {str(e)}")
                    return

        # ... (rest of the code remains the same) ...

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        
if __name__ == "__main__":
    main()
