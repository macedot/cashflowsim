import altair as alt
import pandas as pd
import streamlit as st
from datetime import datetime
from io import StringIO
from streamlit_extras.altex import _chart
from dateutil.relativedelta import relativedelta

TODAY = datetime.now()
TOMORROW = TODAY + relativedelta(days=+1)
END_OF_YEAR = TODAY.date().replace(month=12, day=31)
DATE_MAX = TODAY + relativedelta(years=+1)

INPUT_HEADER = ['name', 'start_date', 'end_date', 'frequency', 'value', 'currency', 'obs']
INPUT_HEADER = ['name', 'start_date', 'end_date', 'frequency', 'value', 'currency', 'obs']
FREQUENCIES = {
    'none': None,
    'daily': relativedelta(days=+1),
    'weekly':  relativedelta(weeks=+1),
    'monthly': relativedelta(months=+1),
    'quarterly': relativedelta(months=+3),
    'semi-annual': relativedelta(months=+6),
    'annual': relativedelta(year=+1),
}


def get_next_date(current_date: datetime, frequency: str) -> datetime:
    if not frequency in FREQUENCIES:
        return None
    return current_date + FREQUENCIES[frequency]


def get_first_date(event: dict, cf_begin: datetime, cf_end: datetime) -> datetime:
    if cf_end < event['start_date']:
        return None  # event starts after end of cashflow period

    if event['end_date']:
        if event['end_date'] < cf_begin:
            return None  # event ends before begin of cashflow period

    if not event['frequency'] or event['frequency'] == 'none' or (event['end_date'] and event['start_date'] == event['end_date']):
        return event['start_date']  # No frequency / start_date equals end_date

    if event['frequency'] == 'daily':
        return cf_begin  # for daily events, return the begin of cashflow period

    current_date = event['start_date']
    while current_date < cf_begin:
        current_date = get_next_date(current_date, event['frequency'])
    return current_date


def generate_cashflows(events: list, cf_period: list[datetime]) -> pd.DataFrame:
    cf_begin, cf_end = cf_period
    assert (cf_begin <= cf_end)
    cf_list = {}
    for event in events:
        if event['value'] == 0:
            continue
        current_date = get_first_date(event, cf_begin, cf_end)
        while current_date and cf_begin <= current_date <= cf_end:
            if event['end_date'] and current_date < event['end_date']:
                break
            if not current_date in cf_list:
                cf_list[current_date] = []
            cf_list[current_date].append({'name': event['name'], 'value': event['value']})
            current_date = get_next_date(current_date, event['frequency'])
    cashflows = []
    for k, v in sorted(cf_list.items()):
        cashflows.append({
            'date': k,
            'cashflow': sum([item['value'] for item in v]),
            'balance': 0,
            'items': v
        })
    return cashflows


def balance_from_cashflows(initial_balance_value: int, simulation_period: tuple, cashflows: list):
    sim_start, _ = simulation_period
    initial_cf = [{
        'date': sim_start,
        'cashflow': 0,
        'balance': initial_balance_value,
        'items': []
    }]
    running_balance = initial_balance_value
    for cf in cashflows:
        running_balance += cf['cashflow']
        cf['balance'] = running_balance
    cf_list = initial_cf + cashflows
    return pd.DataFrame.from_records(cf_list)


def last_day_of_month(any_day):
    # The day 28 exists in every month. 4 days later, it's always next month
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
    # subtracting the number of the current day brings us back one month
    return next_month - datetime.timedelta(days=next_month.day)


st.set_page_config(layout="wide", page_title="Cashflow Simulator", page_icon="🧮")

st.title("📊 Cashflow Simulator")
st.caption("Simulate your income & expense cashflow over the next months!")

"Upload your file and simulate your cashflows!"

input_left, input_middle, input_right = st.columns((5, 5, 5))
initial_balance_value = input_middle.number_input("Current Balance", value=1000,
                                                  placeholder="Type the initial balance to consider on cashflow simulation...")
simulation_period = input_right.date_input(
    "Select the simulation period",
    (TOMORROW, END_OF_YEAR),
    TOMORROW,
    DATE_MAX,
    format="YYYY.MM.DD",
)
uploadedFile = input_left.file_uploader("Choose a CSV file",
                                        type=['csv', 'xlsx'],
                                        accept_multiple_files=False,
                                        key="eventsUploader",
                                        help="Upload a CSV/XLSX file with the columns: '" + ", ".join(INPUT_HEADER) + "'")


def get_events_data(uploadedFile) -> pd.DataFrame:
    df = pd.DataFrame()
    if not uploadedFile is None:
        try:
            df = pd.read_excel(uploadedFile)
        except:
            try:
                df = pd.read_csv(uploadedFile)
            except:
                st.error('Invalid input format', icon="🚨")
                st.stop()
    if df.empty:
        df = pd.read_csv(StringIO(",".join(INPUT_HEADER)), sep=",")
    else:
        for col in df.columns.values.tolist():
            if col not in INPUT_HEADER:
                st.error(f'Invalid column at input file: {col}', icon="🚨")
                st.stop()
    df.start_date = pd.to_datetime(df.start_date, errors='coerce').dt.date
    df.end_date = pd.to_datetime(df.end_date, errors='coerce').dt.date
    df.value = df.value.astype("int64")
    df.currency = df.currency.astype("category")
    df.frequency = df.frequency.astype("category")
    return df.to_dict(orient="records")


df_events = get_events_data(uploadedFile)
df_edited = st.data_editor(
    df_events,
    column_config={
        "start_date": st.column_config.DateColumn(
            "Start Date",
            min_value=TODAY + relativedelta(days=+1),
            max_value=TODAY + relativedelta(years=+1),
            format="YYYY-MM-DD",
            step=1,
        ),
        "end_date": st.column_config.DateColumn(
            "End Date",
            min_value=TODAY + relativedelta(days=+1),
            max_value=TODAY + relativedelta(years=+1),
            format="YYYY-MM-DD",
            step=1,
        ),
    },
    hide_index=True,
    use_container_width=True,
    num_rows="dynamic",
)

st.caption("Modify cells above 👆 or even ➕ add rows, and check out the impacts below 👇")


@st.cache_data
def get_result_data(df) -> pd.DataFrame:
    df.date = pd.to_datetime(df.date, errors='coerce').dt.date
    df.cashflow = df.cashflow.astype("int64")
    df.balance = df.balance.astype("int64")
    return df


cashflows = generate_cashflows(df_edited, simulation_period)
df_result = balance_from_cashflows(initial_balance_value, simulation_period, cashflows)

tab1, tab2 = st.tabs(["Result Graph", "Result Data"])
with tab1:
    base = alt.Chart(df_result).encode(
        alt.X('yearmonthdate(date):T').axis(title='Date'),
        tooltip=['cashflow', 'balance', 'items']
    )
    bar = base.mark_bar().encode(y='cashflow:Q')
line = base.mark_line(color='red',
                      interpolate='step-after',
                      opacity=0.75).encode(y='balance:Q')
chart = (bar + line).properties(height=600)  # .interactive()
st.altair_chart(chart, theme="streamlit", use_container_width=True)
with tab2:
    st.dataframe(df_result, hide_index=True, use_container_width=True)
