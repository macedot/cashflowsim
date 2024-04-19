import altair as alt
import pandas as pd
import streamlit as st
from datetime import datetime
from io import StringIO
from streamlit_extras.altex import _chart
from dateutil.relativedelta import relativedelta

st.set_page_config(layout="wide", page_title="Cashflow Simulator", page_icon="🧮")

st.title("📊 Cashflow Simulator")
st.caption("Simulate your income & expense cashflow over the next months!")

# "Let viewers edit your data and see how that impacts the rest of the app!"

# TODO: Add Today/Current Balance
# TODO: Add Simulation Start Date Widget
# TODO: Add Simulation End Date Widget

@st.cache_data
def get_events_data() -> pd.DataFrame:
    df = pd.read_csv(StringIO('''
uuid,name,start_date,end_date,frequency,amount,currency,obs
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
    df.set_index("uuid")
    df.start_date = df.start_date.astype("datetime64[ns]")
    df.end_date = df.end_date.astype("datetime64[ns]")
    df.amount = df.amount.astype("int64")
    df.currency = df.currency.astype("category")
    df.frequency = df.frequency.astype("category")
    return df


NOW = datetime.now()

# with st.echo():
df = get_events_data()
edited_df = st.data_editor(
    df,
    column_config={
        "start_date": st.column_config.DateColumn(
            "Start Date",
            min_value=NOW + relativedelta(days=+1),
            max_value=NOW + relativedelta(years=+1),
            format="YYYY-MM-DD",
            step=1,
        ),
        "end_date": st.column_config.DateColumn(
            "End Date",
            min_value=NOW + relativedelta(days=+1),
            max_value=NOW + relativedelta(years=+1),
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


@st.cache_data
def get_result_data() -> pd.DataFrame:
    df = pd.read_csv(StringIO('''
date,cashflow,balance,items
2024-04-19,0,0,[]
2024-04-22,500,500,"[{name:Grossery,value:-100},{name:Car,value:-600},{name:Link&Co Sub,value:-200},{name:Extra,value:1500},{name:Ocio,value:-100}]"
2024-04-25,3872,4372,"[{name:Salary,value:3232},{name:Reembolso Watch,value:460},{name:Reembolso Bills,value:180}]"
2024-04-29,-200,4172,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-05-01,-501,3671,"[{name:GSD,value:-501}]"
2024-05-05,-1300,2371,"[{name:Rent,value:-1300}]"
2024-05-06,-200,2171,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-05-13,-200,1971,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-05-15,-650,1321,"[{name:Utility,value:-150},{name:Credit Card,value:-500}]"
2024-05-20,-200,1121,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-05-22,-600,521,"[{name:Car,value:-600}]"
2024-05-25,3232,3753,"[{name:Salary,value:3232}]"
2024-05-27,-200,3553,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-06-01,-501,3052,"[{name:GSD,value:-501}]"
2024-06-03,-200,2852,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-06-05,-1300,1552,"[{name:Rent,value:-1300}]"
2024-06-10,-200,1352,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-06-15,-650,702,"[{name:Utility,value:-150},{name:Credit Card,value:-500}]"
2024-06-17,-200,502,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-06-22,-600,-98,"[{name:Car,value:-600}]"
2024-06-24,-200,-298,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-06-25,6464,6166,"[{name:Salary,value:3232},{name:paga13,value:3232}]"
2024-07-01,-701,5465,"[{name:Grossery,value:-100},{name:GSD,value:-501},{name:Ocio,value:-100}]"
2024-07-05,-1300,4165,"[{name:Rent,value:-1300}]"
2024-07-08,-200,3965,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-07-15,-850,3115,"[{name:Utility,value:-150},{name:Grossery,value:-100},{name:Credit Card,value:-500},{name:Ocio,value:-100}]"
2024-07-22,-800,2315,"[{name:Grossery,value:-100},{name:Car,value:-600},{name:Ocio,value:-100}]"
2024-07-25,3412,5727,"[{name:Salary,value:3232},{name:Reembolso Bills,value:180}]"
2024-07-29,-200,5527,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-08-01,-501,5026,"[{name:GSD,value:-501}]"
2024-08-05,-1500,3526,"[{name:Rent,value:-1300},{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-08-12,-200,3326,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-08-15,-650,2676,"[{name:Utility,value:-150},{name:Credit Card,value:-500}]"
2024-08-19,-200,2476,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-08-22,-600,1876,"[{name:Car,value:-600}]"
2024-08-25,3232,5108,"[{name:Salary,value:3232}]"
2024-08-26,-200,4908,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-09-01,-501,4407,"[{name:GSD,value:-501}]"
2024-09-02,-200,4207,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-09-05,-1300,2907,"[{name:Rent,value:-1300}]"
2024-09-09,-200,2707,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-09-15,-650,2057,"[{name:Utility,value:-150},{name:Credit Card,value:-500}]"
2024-09-16,-200,1857,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-09-22,-600,1257,"[{name:Car,value:-600}]"
2024-09-23,-200,1057,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-09-25,3232,4289,"[{name:Salary,value:3232}]"
2024-09-30,-200,4089,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-10-01,-501,3588,"[{name:GSD,value:-501}]"
2024-10-05,-1300,2288,"[{name:Rent,value:-1300}]"
2024-10-07,-200,2088,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-10-14,-200,1888,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-10-15,-650,1238,"[{name:Utility,value:-150},{name:Credit Card,value:-500}]"
2024-10-21,-200,1038,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-10-22,-600,438,"[{name:Car,value:-600}]"
2024-10-25,3412,3850,"[{name:Salary,value:3232},{name:Reembolso Bills,value:180}]"
2024-10-28,-200,3650,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-11-01,-501,3149,"[{name:GSD,value:-501}]"
2024-11-04,-200,2949,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-11-05,-1300,1649,"[{name:Rent,value:-1300}]"
2024-11-11,-200,1449,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-11-15,-650,799,"[{name:Utility,value:-150},{name:Credit Card,value:-500}]"
2024-11-18,-200,599,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-11-22,-600,-1,"[{name:Car,value:-600}]"
2024-11-25,3032,3031,"[{name:Salary,value:3232},{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-12-01,-501,2530,"[{name:GSD,value:-501}]"
2024-12-02,-200,2330,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-12-05,-1300,1030,"[{name:Rent,value:-1300}]"
2024-12-09,-200,830,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-12-15,-650,180,"[{name:Utility,value:-150},{name:Credit Card,value:-500}]"
2024-12-16,-200,-20,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-12-22,-600,-620,"[{name:Car,value:-600}]"
2024-12-23,-200,-820,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2024-12-25,6464,5644,"[{name:Salary,value:3232},{name:paga14,value:3232}]"
2024-12-30,-200,5444,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2025-01-01,-501,4943,"[{name:GSD,value:-501}]"
2025-01-05,-1300,3643,"[{name:Rent,value:-1300}]"
2025-01-06,-200,3443,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2025-01-13,-200,3243,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2025-01-15,-650,2593,"[{name:Utility,value:-150},{name:Credit Card,value:-500}]"
2025-01-20,-200,2393,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2025-01-22,-600,1793,"[{name:Car,value:-600}]"
2025-01-25,3412,5205,"[{name:Salary,value:3232},{name:Reembolso Bills,value:180}]"
2025-01-27,-200,5005,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2025-02-01,-501,4504,"[{name:GSD,value:-501}]"
2025-02-03,-200,4304,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2025-02-05,-1300,3004,"[{name:Rent,value:-1300}]"
2025-02-10,-200,2804,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2025-02-15,-650,2154,"[{name:Utility,value:-150},{name:Credit Card,value:-500}]"
2025-02-17,-200,1954,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2025-02-22,-600,1354,"[{name:Car,value:-600}]"
2025-02-24,-200,1154,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2025-02-25,3232,4386,"[{name:Salary,value:3232}]"
2025-03-01,-501,3885,"[{name:GSD,value:-501}]"
2025-03-03,-200,3685,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2025-03-05,-1300,2385,"[{name:Rent,value:-1300}]"
2025-03-10,-200,2185,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2025-03-15,-650,1535,"[{name:Utility,value:-150},{name:Credit Card,value:-500}]"
2025-03-17,-200,1335,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2025-03-22,-600,735,"[{name:Car,value:-600}]"
2025-03-24,-200,535,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2025-03-25,3232,3767,"[{name:Salary,value:3232}]"
2025-03-31,-200,3567,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2025-04-01,-501,3066,"[{name:GSD,value:-501}]"
2025-04-05,-1300,1766,"[{name:Rent,value:-1300}]"
2025-04-07,-200,1566,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2025-04-14,-200,1366,"[{name:Grossery,value:-100},{name:Ocio,value:-100}]"
2025-04-15,-650,716,"[{name:Utility,value:-150},{name:Credit Card,value:-500}]"
'''), sep=",")
    df.date = df.date.astype("datetime64[ns]")
    df.cashflow = df.cashflow.astype("int64")
    df.balance = df.balance.astype("int64")
    return df

df_result = get_result_data()

tab1, tab2 = st.tabs(["Result Graph", "Result Data"])
with tab1:
    base = alt.Chart(df_result).encode(x='date:O')
    bar = base.mark_bar().encode(y='cashflow:Q')
    line =  base.mark_line(color='red', interpolate='step-after').encode(y='balance:Q')
    chart = (bar + line).interactive().properties(height=600)
    st.altair_chart(chart, theme="streamlit", use_container_width=True)
with tab2:
    st.dataframe(df_result.style.hide(axis="index"), use_container_width=True)

