# -*- coding: utf8 -*-

import time
import json
import random
import platform
import configparser
from datetime import datetime, timedelta

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as Wait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


config = configparser.ConfigParser()
config.read('config.ini')

PERSON = config['USVISA']['PERSON']
USERNAME = config['USVISA']['USERNAME']
PASSWORD = config['USVISA']['PASSWORD']
SCHEDULE_ID = config['USVISA']['SCHEDULE_ID']
MY_SCHEDULE_DATE = config['USVISA']['MY_SCHEDULE_DATE']
MY_BLOCK_DAY = config['USVISA']['MY_BLOCK_DAY']
COUNTRY_CODE = config['USVISA']['COUNTRY_CODE'] 
FACILITY_ID = config['USVISA']['FACILITY_ID']
CAS_DAYS_IN_COUNTRY = config['USVISA']['CAS_DAYS_IN_COUNTRY']
MESSAGE_SCHEDULE = config['USVISA']['MESSAGE_SCHEDULE']

LOCAL_USE = config['CHROMEDRIVER'].getboolean('LOCAL_USE')
HUB_ADDRESS = config['CHROMEDRIVER']['HUB_ADDRESS']

REGEX_CONTINUE = "//a[contains(text(),'Continuar')]"


STEP_TIME = 0.5  # time between steps (interactions with forms): 0.5 seconds
RETRY_TIME = 1  # wait time between retries/checks for available dates: 1 minutes
EXCEPTION_TIME = 60*5  # wait time when an exception occurs: 30 minutes
COOLDOWN_TIME = 60*60 #60*305  # wait time for take a rest of 1 hour

DATE_URL = f"https://ais.usvisa-info.com/{COUNTRY_CODE}/niv/schedule/{SCHEDULE_ID}/appointment/days/{FACILITY_ID}.json?appointments[expedite]=false"
TIME_URL = f"https://ais.usvisa-info.com/{COUNTRY_CODE}/niv/schedule/{SCHEDULE_ID}/appointment/times/{FACILITY_ID}.json?date=%s&appointments[expedite]=false"
CAS_DATE_URL = f"https://ais.usvisa-info.com/{COUNTRY_CODE}/niv/schedule/{SCHEDULE_ID}/appointment/days/{CAS_DAYS_IN_COUNTRY}.json?consulate_id={FACILITY_ID}&consulate_date=%s&consulate_time=%s&appointments[expedite]=false"
CAS_TIME_URL = f"https://ais.usvisa-info.com/{COUNTRY_CODE}/niv/schedule/{SCHEDULE_ID}/appointment/times/{CAS_DAYS_IN_COUNTRY}.json?date=%s&consulate_id={FACILITY_ID}&consulate_date=%s&consulate_time=%s&appointments[expedite]=false"
APPOINTMENT_URL = f"https://ais.usvisa-info.com/{COUNTRY_CODE}/niv/schedule/{SCHEDULE_ID}/appointment"
CONTINUE_URL = f"https://ais.usvisa-info.com/{COUNTRY_CODE}/niv/schedule/{SCHEDULE_ID}/continue_actions"
EXIT = False

POSSIBLE_DATES = ["-02-22","-02-23","-02-24","-02-27","-02-28","-03-01","-03-03","-03-06","-03-07","-03-08","-03-09","-03-10","-03-13","-03-14","-03-15"]
POSSIBLE_YEAR= "2023"
#POSSIBLE_DATES.reverse()

AUTH_TOKEN=None
YATRI_SESION=None

def send_notification(msg):
    print(f"Sending notification: {msg}")


def get_driver():
    if LOCAL_USE:
        dr = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    else:
        dr = webdriver.Remote(command_executor=HUB_ADDRESS, options=webdriver.ChromeOptions())
    return dr

driver = get_driver()


def login():
    # Bypass reCAPTCHA
    driver.get(f"https://ais.usvisa-info.com/{COUNTRY_CODE}/niv/users/sign_in")
    time.sleep(STEP_TIME)
    a = driver.find_element(By.XPATH, '//a[@class="down-arrow bounce"]')
    a.click()
    time.sleep(STEP_TIME)

    print("Login start...")
    href = driver.find_element(By.XPATH, '//*[@id="header"]/nav/div[2]/div[1]/ul/li[3]/a')
    href.click()
    time.sleep(STEP_TIME)
    Wait(driver, 60).until(EC.presence_of_element_located((By.NAME, "commit")))

    print("\tclick bounce")
    a = driver.find_element(By.XPATH, '//a[@class="down-arrow bounce"]')
    a.click()
    time.sleep(STEP_TIME)

    do_login_action()


def do_login_action():
    print("\tinput email")
    user = driver.find_element(By.ID, 'user_email')
    user.send_keys(USERNAME)
    time.sleep(random.randint(1, 3))

    print("\tinput pwd")
    pw = driver.find_element(By.ID, 'user_password')
    pw.send_keys(PASSWORD)
    time.sleep(random.randint(1, 3))

    print("\tclick privacy")
    box = driver.find_element(By.CLASS_NAME, 'icheckbox')
    box .click()
    time.sleep(random.randint(1, 3))

    print("\tcommit")
    btn = driver.find_element(By.NAME, 'commit')
    btn.click()
    time.sleep(random.randint(1, 3))

    Wait(driver, 60).until(
        EC.presence_of_element_located((By.XPATH, REGEX_CONTINUE)))
    time.sleep(random.randint(1, 3))
    print("\tlogin successful!")


def get_date():
    #driver.get(DATE_URL)
    time_url = TIME_URL % "2025-05-07"
    global AUTH_TOKEN
    global YATRI_SESION

    driver.get(time_url)
    if not is_logged_in():
        login()
        return get_date()
    else:
        driver.get(CONTINUE_URL)
        AUTH_TOKEN= driver.find_element(by=By.NAME, value='csrf-token').get_attribute('content')
        YATRI_SESION= driver.get_cookie("_yatri_session")["value"]
        date =[{"date":"2025-05-07","business_day":"true"},{"date":"2025-06-04","business_day":"true"},{"date":"2025-06-17","business_day":"true"},{"date":"2025-06-18","business_day":"true"},{"date":"2025-06-20","business_day":"true"},{"date":"2025-06-24","business_day":"true"},{"date":"2025-06-25","business_day":"true"},{"date":"2025-06-27","business_day":"true"}]
        return date


def get_consulado_and_cas_date_time(date):
    time_url = TIME_URL % date
    fetch_Time_Cnsl = "const promiseA = new Promise( (resolutionFunc,rejectionFunc) => {fetch('"+time_url+"').then(response => response.json()).then(data => resolutionFunc( data ) )});"
    fetch_Time_Cnsl+= " result = await  promiseA.then( (data) => data ); return result.available_times[result.available_times.length - 1];"
    time =driver.execute_script(fetch_Time_Cnsl)

    if time and date:                
        date_url = CAS_DATE_URL % (date, time)
        fetch_Date_Asc = "const promiseA = new Promise( (resolutionFunc,rejectionFunc) => {fetch('"+date_url+"').then(response => response.json()).then(data => resolutionFunc( data ) )});"
        fetch_Date_Asc+= " result = await  promiseA.then( (data) => data ); return result;"
        data_asc =driver.execute_script(fetch_Date_Asc)
        
        print(f"Whitout or maybe CAS ({date})")

        if data_asc:
            date_asc = data_asc[-1].get("date")
            time_url = CAS_TIME_URL % (date_asc, date, time)
            fetch_Time_Asc = "const promiseA = new Promise( (resolutionFunc,rejectionFunc) => {fetch('"+time_url+"').then(response => response.json()).then(data => resolutionFunc( data ) )});"
            fetch_Time_Asc+= " result = await  promiseA.then( (data) => data ); return result.available_times[result.available_times.length - 1];"
            time_asc =driver.execute_script(fetch_Time_Asc)

            # gives more possibilities with the last available time but you can try with the first
            if time_asc:                
                return (date, time, date_asc, time_asc)
            else:
                return (None, None, None, None)            
        else:
            return (None, None, None, None)
    else:
        return (None, None, None, None)


def reschedule_massive(date, time, cas_date, cas_time):
    global EXIT

    print(f"Starting Reschedule ({date})")

    if date and time and cas_date and cas_time:
        data = {
            "utf8": '✓',
            "authenticity_token": AUTH_TOKEN,#driver.find_element(by=By.NAME, value='authenticity_token').get_attribute('value'),
            "confirmed_limit_message": '1',
            "use_consulate_appointment_capacity": 'true',
            "appointments[consulate_appointment][facility_id]": FACILITY_ID,
            "appointments[consulate_appointment][date]": str(date),
            "appointments[consulate_appointment][time]": str(time),
            "appointments[asc_appointment][facility_id]": CAS_DAYS_IN_COUNTRY,
            "appointments[asc_appointment][date]": str(cas_date),
            "appointments[asc_appointment][time]": str(cas_time)
        }

        headers = {
            "User-Agent": driver.execute_script("return navigator.userAgent;"),
            "Referer": APPOINTMENT_URL,
            "Cookie": "_yatri_session=" + YATRI_SESION #driver.get_cookie("_yatri_session")["value"]
        }
        
        print("posteando")
        r = requests.post(APPOINTMENT_URL, headers=headers, data=data)
        print("fechas: ", date, time, cas_date, cas_time)

        if(r.text.find(MESSAGE_SCHEDULE) != -1):
            now = datetime.today()
            f = open("consular_dates.txt", "a")
            f.write("\n"+"Post_Especial: "+str(now)+"\n")
            f.write("\n" +"Post_Especial: "+date+" "+time+" "+cas_date+" "+cas_time+"\n")
            msg = f"Rescheduled Successfully! for {PERSON}: embajada: {date} {time} cas: {cas_date} {cas_time} "

            print("Complety")
            send_notification(msg)
            EXIT = True
            get_out = True
            return get_out
        else:
            now = datetime.today()
            f = open("consular_dates.txt", "a")
            f.write("\n"+"Post_Especial: "+str(now)+"\n")
            f.write("\n" +"Post_Especial: "+date+" "+time+" "+cas_date+" "+cas_time+"\n")
            msg = f"Reschedule puede haber sido, O FALLADO: embajada: {date} {time} cas: {cas_date} {cas_time}"
            send_notification(msg)


def is_logged_in():
    content = driver.page_source
    if(content.find("error") != -1):
        return False
    return True



def get_available_date(dates):
    global finding_count
    
    def is_earlier_masive(date):            
        date_consulado, time_consulado, date_asc, time_asc = get_consulado_and_cas_date_time(date)
        if date_consulado and time_consulado and date_asc and time_asc:
            return reschedule_massive(date_consulado, time_consulado, date_asc, time_asc)

    for POSSIBLE_DATE in POSSIBLE_DATES:
        date = POSSIBLE_YEAR + POSSIBLE_DATE
        if is_earlier_masive(date):
            return
        


def push_notification(dates):
    msg = "date: "
    for d in dates:
        msg = msg + d.get('date') + '; '
    send_notification(msg)


if __name__ == "__main__":
    login()
    retry_count = 0
    finding_count = 0
    
    while 1:
        if retry_count > 40:
            break
        try:
            print("------------------")
            now = datetime.today()
            print(now)
            print(f"Retry count: {retry_count}")
            print(f"Retry finding: {finding_count}")
            print()


            dates = get_date()[:5]

            date = get_available_date(dates)
            
            print()

            if(EXIT):
                print("------------------retry with successfull")
                break
                  
            if finding_count > 150:
                # if we pass the limit of retries, coldown the script for 5 hours
                msg = "Pass the limit, continue in 1 hours, retry number: "+ str(finding_count)
                send_notification(msg)
                time.sleep(COOLDOWN_TIME)
                finding_count = 0
            else:
                time_now = datetime.now() 
                prev_minute = time_now.minute - (time_now.minute % RETRY_TIME)
                time_rounded = time_now.replace(minute=prev_minute, second=0, microsecond=0)
                time_rounded += timedelta(minutes=RETRY_TIME)
                time_to_wait = (time_rounded - datetime.now()).total_seconds()+12
                print(f"Retry in: {time_to_wait}")
                time.sleep(time_to_wait)


        except:
            retry_count += 1
            time.sleep(EXCEPTION_TIME)
        finding_count += 1

    if(not EXIT):
        send_notification("HELP! Crashed.")

##BY "LEAS EL SAMBO" FROM EMBASSY ONLY TO CAS AND EMBASSY SCHEDULER.
