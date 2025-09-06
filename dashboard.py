import streamlit as st
import pandas as pd
import io

st.title("Data Analysis Dashboard")

# Upload file
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

# Choose analysis
analysis_type = st.selectbox(
    "Choose Analysis Type",
    ["Summary Statistics", "Column Distribution", "Missing Value Report"]
)

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("### Uploaded Data (first 5 rows)")
    st.dataframe(df.head())

    if st.button("Run Analysis"):
        output = None

        if analysis_type == "Summary Statistics":
            output = df.describe().T
        elif analysis_type == "Column Distribution":
            output = df.nunique().to_frame("Unique Values")
        elif analysis_type == "Missing Value Report":
            output = df.isnull().sum().to_frame("Missing Count")

        st.write("### Analysis Result")
        st.dataframe(output)

        # Download option
        buffer = io.BytesIO()
        output.to_csv(buffer)
        buffer.seek(0)
        st.download_button(
            label="Download Result as CSV",
            data=buffer,
            file_name=f"{analysis_type.replace(' ', '_')}_result.csv",
            mime="text/csv"
        )
