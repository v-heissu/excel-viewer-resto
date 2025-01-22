import streamlit as st
import pandas as pd
import io

# Add custom CSS for floating buttons
st.markdown("""
<style>
.floating-container {
   position: fixed;
   bottom: 20px;
   right: 20px;
   display: flex;
   flex-direction: column;
   gap: 10px;
   z-index: 999;
}
.floating-button {
   background-color: #1f1f1f;
   color: white;
   padding: 10px 20px;
   border-radius: 5px;
   text-decoration: none;
   text-align: center;
}
</style>
""", unsafe_allow_html=True)

def main():
   st.title("Excel Image Viewer")
   
   # Add floating buttons container
   st.markdown("""
       <div class="floating-container" id="floating-buttons">
           <a href="#top" class="floating-button">⬆️ Top</a>
           <a href="#bottom" class="floating-button">⬇️ Bottom</a>
           <a href="#download" class="floating-button">💾 Download</a>
       </div>
   """, unsafe_allow_html=True)
   
   uploaded_file = st.file_uploader("Upload Excel file", type=['xlsx'])
   
   if uploaded_file:
       df = pd.read_excel(uploaded_file)
       
       if 'col_mapping' not in st.session_state:
           st.session_state.col_mapping = {}
       
       st.subheader("Column Mapping")
       all_columns = df.columns.tolist()
       
       col_mapping = {
           'url': st.selectbox('Select URL column', [''] + all_columns),
           'image': st.selectbox('Select Image URL column', [''] + all_columns),
           'place_id': st.selectbox('Select Place ID column', [''] + all_columns),
           'id': st.selectbox('Select ID column', [''] + all_columns)
       }
       
       if st.button("Confirm Mapping"):
           if '' in col_mapping.values():
               st.error("Please select all column mappings")
               return
           st.session_state.col_mapping = col_mapping
           
       if 'col_mapping' in st.session_state and st.session_state.col_mapping:
           if 'da_controllare' not in df.columns:
               df['da_controllare'] = False
           
           for idx, row in df.iterrows():
               col1, col2 = st.columns([1, 3])
               with col1:
                   try:
                       if pd.notna(row[st.session_state.col_mapping['image']]):
                           st.image(row[st.session_state.col_mapping['image']], width=200)
                       else:
                           st.write("No image")
                   except:
                       st.write("Error loading image")
               
               with col2:
                   st.write(f"URL: {row[st.session_state.col_mapping['url']]}")
                   st.write(f"Place ID: {row[st.session_state.col_mapping['place_id']]}")
                   df.at[idx, 'da_controllare'] = st.checkbox(
                       "Da controllare",
                       key=f"check_{idx}",
                       value=df.at[idx, 'da_controllare']
                   )
           
           selected_df = df[df['da_controllare']]
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
   
   # Add bottom anchor
   st.markdown('<div id="bottom"></div>', unsafe_allow_html=True)

if __name__ == "__main__":
   main()
