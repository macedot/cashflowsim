"""Cashflow Simulator - Streamlit frontend application.

This module provides the web interface for the cashflow simulation service.
It communicates with the Go backend API for all calculations.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta

from api_client import run_simulation

# Constants
TODAY = datetime.now()
TOMORROW = TODAY + relativedelta(days=+1)
END_OF_YEAR = TODAY.date().replace(month=12, day=31)
DATE_MAX = TODAY + relativedelta(years=+1)

INPUT_HEADER = ['name', 'start_date', 'end_date', 'frequency', 'value', 'obs']
FREQUENCIES = {
    'daily': relativedelta(days=+1),
    'weekly':  relativedelta(weeks=+1),
    'monthly': relativedelta(months=+1),
    'quarterly': relativedelta(months=+3),
    'semi-annual': relativedelta(months=+6),
    'annual': relativedelta(years=+1),
}


def create_input_dataframe() -> pd.DataFrame:
    """Create an empty input dataframe with the required columns."""
    return pd.DataFrame(columns=INPUT_HEADER)


def setup_input_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Set up dataframe column types for input data."""
    df['name'] = df['name'].astype("string")
    df['start_date'] = pd.to_datetime(df['start_date'], format='%Y-%m-%d')
    df['end_date'] = pd.to_datetime(df['end_date'], format='%Y-%m-%d')
    df['value'] = df['value'].astype("int64")
    df['frequency'] = df['frequency'].astype("string")
    df['obs'] = df['obs'].astype("string")
    return df


def load_input_data(uploadedFile=None) -> pd.DataFrame:
    """Load input data from file or create empty dataframe."""
    df = create_input_dataframe()
    if uploadedFile:
        try:
            df = pd.read_excel(uploadedFile)
        except Exception:
            try:
                df = pd.read_csv(uploadedFile)
            except Exception:
                st.error('Invalid file format', icon="🚨")
                st.stop()
        for col in df.columns.values.tolist():
            if col not in INPUT_HEADER:
                df.drop(columns=[col], inplace=True)
                st.warning(f'Column ignored at input file: {col}', icon="🚨")
    return setup_input_dataframe(df)


def main():
    """Main application entry point."""
    st.set_page_config(layout='wide', page_title="Cashflow Simulator", page_icon="🧮")
    st.title("📊 Cashflow Simulator")
    st.caption("Simulate your income & expenditure cash flow over the next few months.")

    st.write("Fill in your financial events or upload a file and simulate your cash flows.")

    if 'df' not in st.session_state:
        st.session_state.df = load_input_data()

    with st.expander("Simulation Parameters"):
        initial_balance_value = st.number_input(
            "Current Balance",
            value=1000,
            placeholder="Initial balance to consider on cashflow simulation..."
        )
        simulation_period = st.date_input(
            "Select the simulation period",
            (TOMORROW, END_OF_YEAR),
            TOMORROW,
            DATE_MAX,
            format="YYYY.MM.DD",
        )

        data_config = {
            "name": st.column_config.TextColumn(
                "Event Name",
                help="Name of the event",
                width="small",
                required=True,
                max_chars=50,
            ),
            "start_date": st.column_config.DateColumn(
                "Start Date",
                width="small",
                required=True,
                format="YYYY.MM.DD",
                step=1,
            ),
            "end_date": st.column_config.DateColumn(
                "End Date",
                width="small",
                format="YYYY.MM.DD",
                step=1,
            ),
            "frequency": st.column_config.SelectboxColumn(
                "Event Frequency",
                help="Frequency of the event",
                width="small",
                options=list(FREQUENCIES.keys()),
            ),
            "value": st.column_config.NumberColumn(
                "Event Value",
                help="Value that the event generates",
                width="small",
                required=True,
                step=1,
            ),
            "obs": st.column_config.TextColumn(
                "Obs",
                help="Personal notes about the event",
                width="medium",
                max_chars=50,
            ),
        }
        uploadedFile = st.file_uploader(
            "Upload your saved events file",
            type=['csv', 'xlsx'],
            accept_multiple_files=False,
            key="eventsUploader",
            help="Upload a CSV/XLSX file with the columns: '" + ", ".join(INPUT_HEADER) + "'"
        )
        if uploadedFile is not None:
            st.success('File loaded successfully', icon="🎉")
            st.session_state.df = load_input_data(uploadedFile)

    df_edited = st.data_editor(
        st.session_state.df,
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        column_config=data_config,
        key="data_editor",
    )

    st.caption("Modify cells above 👆 or even ➕ add rows, and check out the impacts below 👇")

    # Convert data for API call
    eventData = df_edited.to_dict(orient="records")
    sim_start, sim_end = [pd.Timestamp(d) for d in simulation_period]

    # Call simulation API
    cashflows = run_simulation(
        events=eventData,
        initial_balance=float(initial_balance_value),
        sim_start=sim_start,
        sim_end=sim_end,
    )

    if cashflows is None:
        st.error("Failed to run simulation. Please check the error message above.")
        st.stop()

    # Convert API response to DataFrame
    if cashflows:
        df_result = pd.DataFrame(cashflows)
        df_result['date'] = pd.to_datetime(df_result['date'])
        # Convert items list to string for display
        df_result['items'] = df_result['items'].apply(lambda x: str(x) if x else '')
    else:
        # Empty result - show initial balance only
        df_result = pd.DataFrame({
            'date': [sim_start],
            'cashflow': [0],
            'balance': [initial_balance_value],
            'items': [''],
        })

    # Display results
    tab1, tab2 = st.tabs(["Result Graph", "Result Data"])
    with tab1:
        if not df_result.empty:
            base = alt.Chart(df_result).encode(
                alt.X('yearmonthdate(date):T').axis(title='Date'),
            )
            bar = base.mark_bar().encode(y='cashflow:Q')
            line = base.mark_line(
                color='red',
                thickness=10,
                interpolate='step-after',
                opacity=0.75
            ).encode(y='balance:Q')
            chart = (bar + line).properties(height=600)
            st.altair_chart(chart, theme="streamlit", use_container_width=True)
        else:
            st.info("No cashflow data to display.")
    with tab2:
        st.dataframe(df_result, hide_index=True, use_container_width=True)


if __name__ == "__main__":
    main()
