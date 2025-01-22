import streamlit as st
import pandas as pd

def main():
   st.title("Excel Image Viewer")
   
   uploaded_file = st.file_uploader("Upload Excel file", type=['xlsx'])
   
   if uploaded_file:
       df = pd.read_excel(uploaded_file)
       
       # Column mapping selection
       col_mapping = {}
       st.subheader("Column Mapping")
       
       all_columns = df.columns.tolist()
       col_mapping['url'] = st.selectbox('Select URL column', [''] + all_columns)
       col_mapping['image'] = st.selectbox('Select Image URL column', [''] + all_columns)
       col_mapping['place_id'] = st.selectbox('Select Place ID column', [''] + all_columns)
       col_mapping['id'] = st.selectbox('Select ID column', [''] + all_columns)
       
       if st.button("Confirm Mapping"):
           if '' in col_mapping.values():
               st.error("Please select all column mappings")
               return
               
           # Add checkbox column
           if 'da_controllare' not in df.columns:
               df['da_controllare'] = False
           
           # Display data
           for idx, row in df.iterrows():
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
                   df.at[idx, 'da_controllare'] = st.checkbox(
                       "Da controllare",
                       key=f"check_{idx}", 
                       value=df.at[idx, 'da_controllare']
                   )
           
           if st.button("Download Selected"):
               selected_df = df[df['da_controllare']]
               if not selected_df.empty:
                   st.download_button(
                       "Click to Download",
                       selected_df.to_excel(index=False).getvalue(),
                       "selected_items.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                   )

if __name__ == "__main__":
   main()
