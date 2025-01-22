import streamlit as st
import pandas as pd

def main():
    st.title("Excel Image Viewer")
    
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
                st.download_button(
                    "Download Selected",
                    selected_df.to_excel(index=False).getvalue(),
                    "selected_items.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

if __name__ == "__main__":
    main()
