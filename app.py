import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

st.title("📅 Dynamic Client Renewal Checker")

# Upload file
uploaded_file = st.file_uploader("Upload file Excel (.xlsx)", type=["xlsx"])

def find_date_columns(df):
    """Find columns that might contain dates (birthday, renewal dates, etc.)"""
    date_columns = []
    for col in df.columns:
        col_lower = str(col).lower()
        # Check for common date column names
        if any(keyword in col_lower for keyword in ['birthday', 'dob', 'birth', 'date', 'renewal', 'premium']):
            # Try to convert sample data to datetime
            try:
                sample_data = df[col].dropna().head(10)
                if len(sample_data) > 0:
                    pd.to_datetime(sample_data, errors='raise')
                    date_columns.append(col)
            except:
                continue
    return date_columns

def find_email_columns(df):
    """Find columns that might contain email addresses"""
    email_columns = []
    for col in df.columns:
        col_lower = str(col).lower()
        if 'email' in col_lower or 'mail' in col_lower:
            email_columns.append(col)
    return email_columns

def calculate_age(birth_date):
    """Calculate age from birth date"""
    today = datetime.now()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

if uploaded_file:
    try:
        # Read all sheets
        excel_file = pd.ExcelFile(uploaded_file)
        sheet_names = excel_file.sheet_names
        
        st.subheader("📋 Available Sheets:")
        st.write(f"Found sheets: {', '.join(sheet_names)}")
        
        # Let user select sheet
        selected_sheet = st.selectbox(
            "Select sheet to analyze:",
            options=sheet_names,
            index=1 if len(sheet_names) > 1 else 0  # Default to second sheet if available
        )
        
        # Read selected sheet
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
        
        # Clean column names (remove extra spaces, etc.)
        df.columns = df.columns.str.strip()
        
        # Show preview
        st.subheader("📊 Preview Data:")
        st.dataframe(df.head())
        
        # Find potential date columns
        date_columns = find_date_columns(df)
        email_columns = find_email_columns(df)
        
        st.subheader("🔍 Detected Columns:")
        st.write(f"**Date columns found:** {', '.join(date_columns) if date_columns else 'None'}")
        st.write(f"**Email columns found:** {', '.join(email_columns) if email_columns else 'None'}")
        
        if not date_columns:
            st.error("No date columns detected. Please check your data format.")
            st.stop()
        
        # Let user confirm/select columns
        col1, col2 = st.columns(2)
        
        with col1:
            birthday_col = st.selectbox(
                "Select Birthday column:",
                options=date_columns,
                index=0
            )
        
        with col2:
            renewal_col = st.selectbox(
                "Select Renewal Date column:",
                options=date_columns,
                index=1 if len(date_columns) > 1 else 0
            )
        
        # Process the data
        if st.button("🔄 Process Data"):
            # Convert date columns
            df[birthday_col] = pd.to_datetime(df[birthday_col], errors='coerce')
            df[renewal_col] = pd.to_datetime(df[renewal_col], errors='coerce')
            
            # Remove rows with invalid dates
            df = df.dropna(subset=[birthday_col, renewal_col])
            
            if df.empty:
                st.error("No valid data found after date conversion.")
                st.stop()
            
            # Calculate age
            df['Age'] = df[birthday_col].apply(calculate_age)
            
            # Task 1: Clients above 25 years old
            st.subheader("📋 Task 1: Clients Above 25 Years Old")
            clients_above_25 = df[df['Age'] > 25].copy()
            
            if not clients_above_25.empty:
                st.write(f"Total clients above 25: {len(clients_above_25)}")
                st.dataframe(clients_above_25)
                
                # Download button for clients above 25
                csv_above_25 = clients_above_25.to_csv(index=False)
                st.download_button(
                    label="⬇️ Download Clients Above 25 (CSV)",
                    data=csv_above_25,
                    file_name="clients_above_25.csv",
                    mime="text/csv"
                )
            else:
                st.info("No clients above 25 found.")
            
            # Task 2: Renewal dates for next two months
            st.subheader("📋 Task 2: Renewals for Next Two Months")
            
            # Get current date and calculate date ranges
            today = datetime.now()
            july_start = datetime(2025, 7, 1)
            july_end = datetime(2025, 7, 31)
            august_start = datetime(2025, 8, 1)
            august_end = datetime(2025, 8, 31)
            
            # Filter for July 2025
            july_renewals = df[
                (df[renewal_col] >= july_start) & 
                (df[renewal_col] <= july_end)
            ].copy()
            
            # Filter for August 2025
            august_renewals = df[
                (df[renewal_col] >= august_start) & 
                (df[renewal_col] <= august_end)
            ].copy()
            
            # Display July renewals
            st.subheader("🗓️ July 2025 Renewals")
            if not july_renewals.empty:
                st.write(f"Total renewals in July 2025: {len(july_renewals)}")
                st.dataframe(july_renewals)
                
                # Extract email list if available
                if email_columns:
                    july_emails = july_renewals[email_columns[0]].dropna().tolist()
                    st.write("📧 **Email List for July:**")
                    st.text_area("July Emails", value="\n".join(july_emails), height=100)
                
                # Download button
                csv_july = july_renewals.to_csv(index=False)
                st.download_button(
                    label="⬇️ Download July Renewals (CSV)",
                    data=csv_july,
                    file_name="july_2025_renewals.csv",
                    mime="text/csv"
                )
            else:
                st.info("No renewals scheduled for July 2025.")
            
            # Display August renewals
            st.subheader("🗓️ August 2025 Renewals")
            if not august_renewals.empty:
                st.write(f"Total renewals in August 2025: {len(august_renewals)}")
                st.dataframe(august_renewals)
                
                # Extract email list if available
                if email_columns:
                    august_emails = august_renewals[email_columns[0]].dropna().tolist()
                    st.write("📧 **Email List for August:**")
                    st.text_area("August Emails", value="\n".join(august_emails), height=100)
                
                # Download button
                csv_august = august_renewals.to_csv(index=False)
                st.download_button(
                    label="⬇️ Download August Renewals (CSV)",
                    data=csv_august,
                    file_name="august_2025_renewals.csv",
                    mime="text/csv"
                )
            else:
                st.info("No renewals scheduled for August 2025.")
            
            # Combined email list for both months
            if email_columns and (not july_renewals.empty or not august_renewals.empty):
                st.subheader("📧 Combined Email List (July + August)")
                all_renewal_emails = pd.concat([july_renewals, august_renewals])[email_columns[0]].dropna().unique()
                st.text_area("All Renewal Emails", value="\n".join(all_renewal_emails), height=150)
                
                # Download email list
                email_df = pd.DataFrame(all_renewal_emails, columns=['Email'])
                csv_emails = email_df.to_csv(index=False)
                st.download_button(
                    label="⬇️ Download Email List (CSV)",
                    data=csv_emails,
                    file_name="renewal_emails_july_august.csv",
                    mime="text/csv"
                )
        
        # Show limitations
        st.subheader("⚠️ Limitations:")
        st.write("""
        1. **Date Format**: The system attempts to auto-detect date formats, but may fail with unusual formats
        2. **Column Detection**: Automatic column detection relies on common keywords (birthday, date, email, etc.)
        3. **Data Quality**: Missing or invalid data will be excluded from results
        4. **Sheet Structure**: Works best with tabular data in standard Excel format
        5. **Age Calculation**: Based on current system date
        6. **Email Extraction**: Requires properly formatted email addresses
        """)
                
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        st.write("Please check your file format and try again.")
        
else:
    st.info("Please upload an Excel file to begin analysis.")
    
    # Show expected format
    st.subheader("📝 Expected Data Format:")
    st.write("""
    Your Excel file should contain columns similar to:
    - **Client Name** (or Name)
    - **NRIC** (or ID)
    - **Birthday** (or DOB, Birth Date)
    - **Phone**
    - **Email**
    - **Policy Number**
    - **Policy Name**
    - **Next Premium Date** (or Renewal Date)
    
    The system will automatically detect date and email columns based on column names.
    """)
    
    # Sample data preview
    sample_data = pd.DataFrame({
        'S/No.': [1, 2, 3],
        'Client Name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
        'NRIC': ['S1234567A', 'S7654321B', 'S1122334C'],
        'Birthday': ['1990-08-15', '1985-09-22', '1992-12-10'],
        'Phone': ['91234567', '98765432', '87654321'],
        'Email': ['john@email.com', 'jane@email.com', 'bob@email.com'],
        'Policy Number': ['POL001', 'POL002', 'POL003'],
        'Next Premium Date': ['2025-07-15', '2025-08-22', '2025-07-10']
    })
    st.dataframe(sample_data)