import altair as alt
import pandas as pd
import streamlit as st
from io import StringIO
from streamlit_extras.altex import _chart

st.set_page_config(layout="centered", page_title="Cashflow Simulator", page_icon="🧮")

st.title("📊 Cashflow Simulator")
st.caption("Simulate your income & expense cashflow over the next months!")

"Let viewers edit your data and see how that impacts the rest of the app!"


@st.cache_data
def get_data() -> pd.DataFrame:
    df = pd.read_csv(StringIO('''
id,name,start_date,end_date,frequency,amount,currency,obs
1,Salary,2024-01-25,,monthly,3232,EUR,Electronic Arts
2,Rent,2024-01-05,,monthly,-1300,EUR,5D
3,Utility,2024-01-15,,monthly,-150,EUR,Electricity+Water+Gas
4,Grossery,2024-01-01,,weekly,-100,EUR,Total on the Period
5,Ocio,2024-01-01,,weekly,-100,EUR,Total on the Period
6,GSD,2024-01-01,,monthly,-501,EUR,2x Comedor + 1x Donation
7,Car,2024-05-28,,monthly,-600,EUR,Link&Co
8,Iberia Card,2024-05-15,,monthly,0,EUR,Iberia Credit Card
9,paga13,2024-06-25,,annual,3232,EUR,Electronic Arts
10,paga14,2024-12-25,,annual,3232,EUR,Electronic Arts
11,Fatura Iberia,2024-04-15,,none,-1500,EUR,Primeira fatura Iberia Credit Card
'''), sep=",")
    df.start_date = df.start_date.astype("datetime64[ns]")
    df.end_date = df.end_date.astype("datetime64[ns]")
    df.amount = df.amount.astype("int64")
    df.currency = df.currency.astype("category")
    df.frequency = df.frequency.astype("category")
    return df


@st.cache_data
def get_active_hist(df: pd.DataFrame) -> alt.Chart:
    return _chart(
        mark_function="bar",
        data=df.id.sort_index().reset_index(),
        x=alt.X("id:N", title="Active", sort="x"),
        y=alt.Y("amount:N", title=""),
    )


# with st.echo():
df = get_data()
edited_df = st.data_editor(
    df,
    use_container_width=True,
    num_rows="dynamic",
)

st.caption("Modify cells above 👆 or even ➕ add rows, and check out the impacts below 👇")

# left, middle, right = st.columns((4, 3, 3))
# left.altair_chart(get_age_hist(edited_df), use_container_width=True)
# middle.altair_chart(get_gender_hist(edited_df), use_container_width=True)
# right.altair_chart(get_active_hist(edited_df), use_container_width=True)

middle = st.columns((1))
middle.altair_chart(get_active_hist(edited_df), use_container_width=True)
