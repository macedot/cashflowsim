import altair as alt
import pandas as pd
import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta

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


def is_date_valid(date) -> bool:
    return date and not pd.isnull(date) and date != pd.NaT


def get_next_date(current_date: datetime, frequency: str) -> datetime:
    if not frequency or frequency not in FREQUENCIES or FREQUENCIES[frequency] is None:
        return None
    return current_date + FREQUENCIES[frequency]


def get_first_date(event: dict, cf_begin: datetime, cf_end: datetime) -> datetime:
    start_date = event['start_date']
    if cf_end < start_date:
        return None  # event starts after end of cashflow period

    if is_date_valid(event['end_date']):
        if event['end_date'] < cf_begin:
            return None  # event ends before begin of cashflow period

    if not event['frequency'] or (is_date_valid(event['end_date']) and start_date == event['end_date']):
        return start_date  # No frequency / start_date equals end_date

    if event['frequency'] == 'daily':
        return cf_begin  # for daily events, return the begin of cashflow period

    current_date = start_date
    while current_date < cf_begin:
        current_date = get_next_date(current_date, event['frequency'])
    return current_date


def generate_cashflows(events: list[dict],
                       cf_begin: pd.Timestamp,
                       cf_end: pd.Timestamp) -> pd.DataFrame:
    assert (cf_begin <= cf_end)
    cf_list = {}
    for event in events:
        if event['value'] == 0:
            continue
        current_date = get_first_date(event, cf_begin, cf_end)
        while current_date and cf_begin <= current_date <= cf_end:
            if is_date_valid(event['end_date']) and event['end_date'] < current_date:
                break
            if not current_date in cf_list:
                cf_list[current_date] = []
            cf = {'name': event['name'], 'value': event['value']}
            cf_list[current_date].append(cf)
            current_date = get_next_date(current_date, event['frequency'])
    cashflows = []
    for k, v in sorted(cf_list.items()):
        cashflows.append({
            'date': k,
            'cashflow': sum([item['value'] for item in v]),
            'balance': 0,
            'items': str(v)
        })
    return cashflows


def balance_from_cashflows(initial_balance_value: int,
                           sim_start: pd.Timestamp,
                           cashflows: list) -> pd.DataFrame:
    initial_cf = [{
        'date': sim_start,
        'cashflow': 0,
        'balance': initial_balance_value,
        'items': ''
    }]
    running_balance = initial_balance_value
    for cf in cashflows:
        running_balance += cf['cashflow']
        cf['balance'] = running_balance
    cf_list = initial_cf + cashflows
    return pd.DataFrame.from_records(cf_list)


def create_input_dataframe() -> pd.DataFrame:
    return pd.DataFrame(columns=INPUT_HEADER)


def setup_input_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df['name'] = df['name'].astype("string")
    df['start_date'] = pd.to_datetime(df['start_date'], format='%Y-%m-%d')
    df['end_date'] = pd.to_datetime(df['end_date'], format='%Y-%m-%d')
    df['value'] = df['value'].astype("int64")
    df['frequency'] = df['frequency'].astype("string")
    df['obs'] = df['obs'].astype("string")
    return df


def load_input_data(uploadedFile=None) -> pd.DataFrame:
    df = create_input_dataframe()
    if uploadedFile:
        try:
            df = pd.read_excel(uploadedFile)
        except:
            try:
                df = pd.read_csv(uploadedFile)
            except:
                st.error('Invalid file format', icon="🚨")
                st.stop()
        for col in df.columns.values.tolist():
            if col not in INPUT_HEADER:
                df.drop(columns=[col], inplace=True)
                st.warning(f'Column ignored at input file: {col}', icon="🚨")
    return setup_input_dataframe(df)


def main():
    st.set_page_config(layout='wide', page_title="Cashflow Simulator", page_icon="🧮")
    st.title("📊 Cashflow Simulator")
    st.caption("Simulate your income & expenditure cash flow over the next few months.")

    "Fill in your financial events or upload a file and simulate your cash flows."

    if 'df' not in st.session_state:
        st.session_state.df = load_input_data()

    with st.expander("Simulation Parameters"):
        initial_balance_value = st.number_input("Current Balance",
                                                value=1000,
                                                placeholder="Initial balance to consider on cashflow simulation...")
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
        uploadedFile = st.file_uploader("Upload your saved events file",
                                        type=['csv', 'xlsx'],
                                        accept_multiple_files=False,
                                        key="eventsUploader",
                                        help="Upload a CSV/XLSX file with the columns: '" + ", ".join(INPUT_HEADER) + "'")
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

    eventData = df_edited.to_dict(orient="records")
    sim_start, sim_end = [pd.Timestamp(d) for d in simulation_period]
    cashflows = generate_cashflows(eventData, sim_start, sim_end)
    df_result = balance_from_cashflows(initial_balance_value, pd.Timestamp(TODAY), cashflows)
    tab1, tab2 = st.tabs(["Result Graph", "Result Data"])
    with tab1:
        base = alt.Chart(df_result).encode(
            alt.X('yearmonthdate(date):T').axis(title='Date'),
        )
        bar = base.mark_bar().encode(y='cashflow:Q')
        line = base.mark_line(color='red',
                              thickness=10,
                              interpolate='step-after',
                              opacity=0.75).encode(y='balance:Q')
        chart = (bar + line).properties(height=600)  # .interactive()
        st.altair_chart(chart, theme="streamlit", use_container_width=True)
    with tab2:
        st.dataframe(df_result,
                     hide_index=True,
                     use_container_width=True)


if __name__ == "__main__":
    main()
