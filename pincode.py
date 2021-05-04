import datetime
import json
import requests
import pandas as pd
import streamlit as st
from copy import deepcopy
from twilio.rest import Client
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

st.set_page_config(layout='wide', initial_sidebar_state='collapsed')

@st.cache(allow_output_mutation=True, suppress_st_warning=True)

def filter_column(df, col, value):
    df_temp = deepcopy(df.loc[df[col] == value, :])
    return df_temp

def filter_in_stock(df, col):
    df_temp = deepcopy(df.loc[df[col] >= 0, :])
    return df_temp

def get_location(df, col):
    df_temp = deepcopy(df.loc[df[col], :])
    return df_temp

rename_mapping = {
    'date': 'Date',
    'min_age_limit': 'Minimum Age Limit',
    'available_capacity': 'Available Capacity',
    'pincode': 'Pincode',
    'name': 'Hospital Name',
    'state_name' : 'State',
    'district_name' : 'District',
    'block_name': 'Block Name',
    'fee_type' : 'Fees'
    }

st.title('Manasa says lets get vaccinated!')
st.info('The CoWIN APIs are geo-fenced so sometimes you may not see an output! Please try after sometime ')

left_column_1, right_column_1 = st.beta_columns(2)
with left_column_1:
    numdays = st.slider('Select Date Range', 0, 100, 5)

with right_column_1:
    PINCODE = st.text_input("Pincode", "560037")

base = datetime.datetime.today()
date_list = [base + datetime.timedelta(days=x) for x in range(numdays)]
date_str = [x.strftime("%d-%m-%Y") for x in date_list]

final_df = None
for INP_DATE in date_str:
    URL = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/calendarByPin?pincode={}&date={}".format(PINCODE, INP_DATE)
    response = requests.get(URL)
    if (response.ok) and ('centers' in json.loads(response.text)):
        resp_json = json.loads(response.text)['centers']
        if resp_json is not None:
            df = pd.DataFrame(resp_json)
            if len(df):
                df = df.explode("sessions")
                df['min_age_limit'] = df.sessions.apply(lambda x: x['min_age_limit'])
                df['available_capacity'] = df.sessions.apply(lambda x: x['available_capacity'])
                df['date'] = df.sessions.apply(lambda x: x['date'])
                df = df[["date", "available_capacity", "min_age_limit", "pincode", "name", "state_name", "district_name", "block_name", "fee_type"]]
                if final_df is not None:
                    final_df = pd.concat([final_df, df])
                else:
                    final_df = deepcopy(df)
            else:
                print("No Data Found")

if (final_df is None):
    st.error("No Data Found")
else:
    final_df.drop_duplicates(inplace=True)
    final_df.rename(columns=rename_mapping, inplace=True)

    final_df = filter_column(final_df, "Minimum Age Limit", 18)
    final_df = filter_in_stock(final_df, "Available Capacity")
    table = deepcopy(final_df)
    table.reset_index(inplace=True, drop=True)
    st.table(table)

if final_df is not None:
    if (len(final_df) > 0):
        hospitals = []
        [hospitals.append(x) for x in final_df["Hospital Name"] if x not in hospitals]
        sms_text = str("Cowin notification : Run for vaccine at {0}".format(hospitals))

        # To send SMS via Twilio
        account_sid = 'YOUR_TWILIO_ACCOUNT_SID'
        auth_token = 'YOUR_TWILIO_AUTH_TOKEN'
        client = Client(account_sid, auth_token)
        message = client.messages \
            .create(
            body=sms_text,
            from_='+1123456789',  # Twilio  configured mobile number
            to='+919912345678'  # Mobile number that needs to be notified, your personal number
        )

        #Email notify
        fromaddr = "sender@gmail.com"
        toaddr = ["xyz@gmail.com", "abc@gmail.com", "def@yahoo.com"]

        for dest in toaddr:
            msg = MIMEMultipart()
            msg['From'] = fromaddr
            msg['To'] = dest
            msg['Subject'] = "CoWin Notification By Manasa"
            body = str(hospitals)
            msg.attach(MIMEText(body, 'plain'))
            s = smtplib.SMTP('smtp.gmail.com', 587)
            s.starttls()
            s.login(fromaddr, "YOUR_GMAIL_PASSWORD")
            text = msg.as_string()
            s.sendmail(fromaddr, dest, text)
            s.quit()
    else:
        print("Do nothing")
else:
    print("Do nothing")