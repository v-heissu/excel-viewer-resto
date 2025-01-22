import streamlit as st
import pandas as pd

def main():
    st.title("Excel Image Viewer")
    
    uploaded_file = st.file_uploader("Upload Excel file", type=['xlsx'])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        
        # Verify required columns
        required_cols = ['url', 'image-url', 'google-placeid', 'id']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            st.error(f"Missing required columns: {', '.join(missing_cols)}")
            return
            
        # Add checkbox column
        if 'da_controllare' not in df.columns:
            df['da_controllare'] = False
        
        # Display each row
        for idx, row in df.iterrows():
            col1, col2 = st.columns([1, 3])
            
            with col1:
                try:
                    if pd.notna(row['image-url']) and row['image-url'].strip():
                        st.image(row['image-url'], width=200)
                    else:
                        st.write("No image available")
                except Exception as e:
                    st.write("Error loading image")
            
            with col2:
                st.write(f"URL: {row['url']}")
                st.write(f"Place ID: {row['google-placeid']}")
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
