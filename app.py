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

def last_day_of_month(any_day):
    # The day 28 exists in every month. 4 days later, it's always next month
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
    # subtracting the number of the current day brings us back one month
    return next_month - datetime.timedelta(days=next_month.day)

st.set_page_config(layout="wide", page_title="Cashflow Simulator", page_icon="🧮")

st.title("📊 Cashflow Simulator")
st.caption("Simulate your income & expense cashflow over the next months!")

# "Let viewers edit your data and see how that impacts the rest of the app!"


input_left, input_right = st.columns((5, 5))
initial_balance = input_left.number_input("Current Balance", value=1000, placeholder="Type the initial balance to consider on cashflow simulation...")
simulation_period = input_right.date_input(
    "Select the simulation period",
    (TOMORROW, END_OF_YEAR),
    TOMORROW,
    DATE_MAX,
    format="YYYY.MM.DD",
)

# name,start_date,end_date,frequency,amount,currency,obs
# Salary,2024-01-25,,monthly,3232,EUR,Electronic Arts
# Rent,2024-01-05,,monthly,-1300,EUR,5D
# Utility,2024-01-15,,monthly,-150,EUR,Electricity+Water+Gas
# Grossery,2024-01-01,,weekly,-100,EUR,Total on the Period
# Ocio,2024-01-01,,weekly,-100,EUR,Total on the Period
# GSD,2024-01-01,,monthly,-501,EUR,2x Comedor + 1x Donation
# Car,2024-05-28,,monthly,-600,EUR,Link&Co
# Iberia Card,2024-05-15,,monthly,0,EUR,Iberia Credit Card
# paga13,2024-06-25,,annual,3232,EUR,Electronic Arts
# paga14,2024-12-25,,annual,3232,EUR,Electronic Arts
# Fatura Iberia,2024-04-15,,none,-1500,EUR,Primeira fatura Iberia Credit Card

@st.cache_data
def get_events_data() -> pd.DataFrame:
    uploadedFile = st.file_uploader("Choose a CSV file",
    type=['csv','xlsx'],
    accept_multiple_files=False,
    key="fileUploader")
    uploaded_files = st.file_uploader(, accept_multiple_files=False, type="csv")
    for uploaded_file in uploaded_files:
        bytes_data = uploaded_file.read()
        st.write("filename:", uploaded_file.name)
        st.write(bytes_data)

        df = pd.read_csv(StringIO('''
    name,start_date,end_date,frequency,amount,currency,obs
    Salary,2024-01-25,,monthly,2000,EUR,Electronic Arts
    Rent,2024-01-05,,monthly,-1000,EUR,5D
    '''), sep=",")
        df.start_date = pd.to_datetime(df.start_date, errors='coerce').dt.date
        df.end_date = pd.to_datetime(df.end_date, errors='coerce').dt.date
        df.amount = df.amount.astype("int64")
        df.currency = df.currency.astype("category")
        df.frequency = df.frequency.astype("category")
        return df.to_dict(orient="records")



# with st.echo():
df = get_events_data()
edited_df = st.data_editor(
    df,
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

# left, middle, right = st.columns((4, 3, 3))
# left.altair_chart(get_age_hist(edited_df), use_container_width=True)
# middle.altair_chart(get_gender_hist(edited_df), use_container_width=True)
# right.altair_chart(get_active_hist(edited_df), use_container_width=True)



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
    return FREQUENCIES[frequency]


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
        if event['amount'] == 0:
            continue
        current_date = get_first_date(event, cf_begin, cf_end)
        while current_date and cf_begin <= current_date <= cf_end:
            if event['end_date'] and current_date < event['end_date']:
                break
            if not current_date in cf_list:
                cf_list[current_date] = []
            cf_list[current_date].append({'name':event['name'], 'value': event['value']})
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

def balance_from_cashflows(initial_date: datetime, initial_balance: int, cashflows: list):
  initial_cf = [{
        'date': initial_date,
        'cashflow': 0,
        'balance': initial_balance,
        'items': []
  }]
  running_balance = initial_balance
  for cf in cashflows:
    running_balance += cf['cashflow']
    cf['balance'] = running_balance
  cf_list = initial_cf + cashflows
  return pd.DataFrame.from_records(cf_list)


@st.cache_data
def get_result_data(df) -> pd.DataFrame:
    df.date = pd.to_datetime(df.date, errors='coerce').dt.date
    df.cashflow = df.cashflow.astype("int64")
    df.balance = df.balance.astype("int64")
    return df

events = get_events_data()
cashflows = generate_cashflows(events, simulation_period)
df_result = balance_from_cashflows(initial_balance_value, simulation_period, cashflows)

tab1, tab2 = st.tabs(["Result Graph", "Result Data"])
with tab1:
    base = alt.Chart(df_result).encode(
        alt.X('yearmonthdate(date):T').axis(title='Date'),
    )
    bar = base.mark_bar().encode(y='cashflow:Q')
    line = base.mark_line(color='red', interpolate='step-after').encode(y='balance:Q')
    chart = (bar + line).properties(height=600) #.interactive()
    st.altair_chart(chart, theme="streamlit", use_container_width=True)
with tab2:
    st.dataframe(df_result, hide_index=True, use_container_width=True)

