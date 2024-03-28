from collections import defaultdict
from pathlib import Path
import sqlite3

import streamlit as st
import altair as alt
import pandas as pd
import streamlit as st
import pandas as pd
import re
from io import StringIO
import matplotlib.pyplot as plt


st.title("Transaction analysis")
uploaded_file = st.file_uploader("Upload a CSV file for analysis", type=['csv'])

if uploaded_file is not None:
    # Read and decode the uploaded file content
    content = uploaded_file.getvalue().decode('utf-8')

    # Find the start of the actual data, skipping metadata
    header_row_index = None
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('Date,'):
            header_row_index = i
            break

    if header_row_index is not None:
        # Skip metadata lines and read the CSV data into a DataFrame
        content_io = StringIO(content)
        df = pd.read_csv(content_io, skiprows=header_row_index)

        # Clean the 'Narrative' and 'Running Balance' columns from additional formatting
        df['Narrative'] = df['Narrative'].apply(lambda x: re.sub(r'^="|"$', '', x))
        df['Running Balance'] = df['Running Balance'].apply(lambda x: re.sub(r'^="|"$', '', x)).astype(float)

        # Display the cleaned DataFrame
        st.write(df.head())
        st.write(df.columns)
        df = df.rename(columns = {k : "Debit"  for k in df.columns if k.lower().find("debit") > -1 })
        df['Amount'] = df['Debit'].fillna(0.0) + df['Credit'].fillna(0.0)
        daily_balances = df.groupby('Date')['Amount'].sum().sort_index()

        # Compute the running total to simulate the cash balance over time
        cumulative_balance = daily_balances.cumsum()

        # Convert the cumulative balance to units of 1K USD for visualization
        cumulative_balance_in_thousands = cumulative_balance / 1000

        # Plotting the cash balance over time in units of 1K USD
        plt.figure(figsize=(14, 7))
        cumulative_balance_in_thousands.plot(kind='line', marker='o', linestyle='-', color='blue')
        plt.title('Cash Balance Over Time (in units of 1K USD)')
        plt.xlabel('Date')
        plt.ylabel('Cumulative Cash Balance (1K USD)')
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(plt.gcf())
        categories = {
            'Payments': ['payment', 'payroll'],
            'Debit': ['debit'],
            'Credit': ['credit'],
            'Check': ['check', 'cheque'],
            'Internal Transfers': ['internal tfr'],
            'Domestic Wires': ['wire-out dom'],
            'International Wires': ['wire-out intl'],
            'Specific Invoices': ['invoice']
        }


        # Categorization function
        def categorize_transaction(detail):
            for category, keywords in categories.items():
                for keyword in keywords:
                    if keyword in detail.lower():
                        return category
            return 'Other'  # Default category if no keyword matches


        df['Category'] = df['Narrative'].apply(categorize_transaction)


        # Convert 'Date' to datetime and ensure 'Amount' is numeric
        expenses = df[df['Amount'] < 0]
        expenses_df = expenses.copy()
        expenses_df['Date'] = pd.to_datetime(expenses_df['Date'])
        expenses_df['Date'] = pd.to_datetime(expenses_df['Date'])
        expenses_df['Amount'] = pd.to_numeric(expenses_df['Amount'])

        # Filter out income (assuming income has positive amounts, expenses have negative)
        expenses_only_df = expenses_df[expenses_df['Amount'] < 0].copy()

        # Convert expenses to positive values for visualization
        expenses_only_df['Amount'] = expenses_only_df['Amount'].abs()
        print(set(expenses_only_df['Category']))
        # Aggregate expenses by category for a specific day
        # Selecting an example day - replace this with a day you're interested in
        # example_day = expenses_only_df['Date'].dt.date.iloc[0]
        # daily_expenses = expenses_only_df[expenses_only_df['Date'].dt.date == example_day]
        exp_grouped = expenses_only_df.groupby('Category')['Amount'].sum()

        # Plotting daily expenses
        plt.figure(figsize=(8, 8))
        exp_grouped.plot(kind='pie', autopct='%1.1f%%', title=f'Expenses Distribution by Category')
        plt.ylabel('')  # to hide the 'Amount' label
        st.pyplot(plt.gcf())

    else:
        st.write("Header row could not be automatically determined.")
