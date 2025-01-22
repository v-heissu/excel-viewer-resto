import streamlit as st
import pandas as pd

def main():
    st.title("Excel Image Viewer")
    
    uploaded_file = st.file_uploader("Upload Excel file", type=['xlsx'])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        
        # Add checkbox column
        if 'da_controllare' not in df.columns:
            df['da_controllare'] = False
        
        # Display each row
        for idx, row in df.iterrows():
            col1, col2 = st.columns([1, 3])
            
            with col1:
                # Display image
                if pd.notna(row['image-url']):
                    st.image(row['image-url'], width=200)
                else:
                    st.write("No image available")
            
            with col2:
                # Display URL and checkbox
                st.write(f"URL: {row['url']}")
                df.at[idx, 'da_controllare'] = st.checkbox(
                    "Da controllare",
                    key=f"check_{idx}",
                    value=df.at[idx, 'da_controllare']
                )
        
        # Download button
        if st.button("Download Selected"):
            selected_df = df[df['da_controllare']]
            st.download_button(
                "Click to Download",
                selected_df.to_excel(index=False).encode('utf-8'),
                "selected_items.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()