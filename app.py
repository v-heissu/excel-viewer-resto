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
   st.session_state.page = 0
   
   if 'da_controllare' not in st.session_state.df.columns:
       st.session_state.df['da_controllare'] = False
