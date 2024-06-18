import streamlit as st
import pandas as pd
import dns.resolver
import smtplib
import concurrent.futures
import requests
from io import StringIO

# Function to validate a single email
def validate_email(email):
    try:
        domain = email.split('@')[1]
        records = dns.resolver.resolve(domain, 'MX')
        mx_record = records[0].exchange.to_text()

        server = smtplib.SMTP(timeout=10)
        server.connect(mx_record)
        server.helo(server.local_hostname)
        server.mail('info@yourdomain.com')
        code, message = server.rcpt(email)
        server.quit()

        return code == 250
    except Exception as e:
        return False

# Function to validate emails
def validate_emails(df):
    valid_emails = []
    invalid_emails = []
    spam_emails = []  # Placeholder for spam detection logic

    def validate_and_classify(email):
        if validate_email(email):
            valid_emails.append(email)
        else:
            invalid_emails.append(email)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(validate_and_classify, email) for email in df['email']]
        concurrent.futures.wait(futures)

    return valid_emails, invalid_emails, spam_emails

# Function to load data from GitHub
def load_data_from_github(url):
    response = requests.get(url)
    if response.status_code == 200:
        csv_data = response.content.decode('utf-8')
        df = pd.read_csv(StringIO(csv_data), header=None, names=['email'])
        return df
    else:
        st.error(f"Failed to fetch data from {url}. Status code: {response.status_code}")
        return None

# Streamlit UI
st.title("Email Validation App")

github_url = "https://raw.githubusercontent.com/cycywanyeki20/Delimail/master/Delimail.csv"
uploaded_file = st.file_uploader("Choose a CSV file to validate", type="csv")
sample_size = st.number_input("Number of emails to sample", min_value=10, max_value=500, value=100)

if uploaded_file is not None:
    st.write("Uploaded file:")
    st.write(uploaded_file.name)

    # Load data from uploaded file
    df = pd.read_csv(uploaded_file)

else:
    st.info("No file uploaded. Fetching default data from GitHub...")
    # Load data from GitHub as default
    df = load_data_from_github(github_url)

if df is not None:
    # Sample the data
    sampled_df = df.sample(n=min(sample_size, len(df)), random_state=1)

    # Validate emails
    valid_emails, invalid_emails, spam_emails = validate_emails(sampled_df)

    # Display results
    st.write(f"Total emails sampled: {len(sampled_df)}")
    st.write(f"Valid emails found: {len(valid_emails)}")
    st.write(f"Invalid emails found: {len(invalid_emails)}")
    st.write(f"Spam emails found: {len(spam_emails)}")

    if st.checkbox("Show valid emails"):
        st.write(valid_emails)

    if st.checkbox("Show invalid emails"):
        st.write(invalid_emails)

    if st.checkbox("Show spam emails"):
        st.write(spam_emails)
