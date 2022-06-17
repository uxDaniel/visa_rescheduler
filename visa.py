# -*- coding: utf8 -*-

import time
import json
import random
import configparser
from datetime import datetime

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as Wait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


config = configparser.ConfigParser()
config.read('config.ini')

USERNAME = config['USVISA']['USERNAME']
PASSWORD = config['USVISA']['PASSWORD']
SCHEDULE_ID = config['USVISA']['SCHEDULE_ID']
MY_SCHEDULE_DATE = config['USVISA']['MY_SCHEDULE_DATE']
MULTIPLE_APPOINTMENTS = config['USVISA']['MULTIPLE_APPOINTMENTS']

SENDGRID_API_KEY = config['SENDGRID']['SENDGRID_API_KEY']
PUSH_TOKEN = config['PUSHOVER']['PUSH_TOKEN']
PUSH_USER = config['PUSHOVER']['PUSH_USER']

LOCAL_USE = config['CHROMEDRIVER'].getboolean('LOCAL_USE')
HUB_ADDRESS = config['CHROMEDRIVER']['HUB_ADDRESS']

COUNTRY_CODE = 'es-co'
DAYS_IN_COUNTRY = '25'
CAS_DAYS_IN_COUNTRY = '26'

REGEX_CONTINUE = "//a[contains(text(),'Continuar')]"


# def MY_CONDITION(month, day): return int(month) == 11 and int(day) >= 5
def MY_CONDITION(month, day): return True # No custom condition wanted for the new scheduled date

STEP_TIME = 0.5  # time between steps (interactions): 0.5 seconds
SLEEP_TIME = 20  # recheck time interval: 20 seconds
EXCEPTION_TIME = 60*5  # recheck exception time interval: 5 minutes
RETRY_TIME = 60*60  # recheck empty list time interval: 60 minutes

DATE_URL = f"https://ais.usvisa-info.com/{COUNTRY_CODE}/niv/schedule/{SCHEDULE_ID}/appointment/days/{DAYS_IN_COUNTRY}.json?appointments[expedite]=false"
CAS_DATE_URL = f"https://ais.usvisa-info.com/{COUNTRY_CODE}/niv/schedule/{SCHEDULE_ID}/appointment/days/{CAS_DAYS_IN_COUNTRY}.json?consulate_id={DAYS_IN_COUNTRY}&consulate_date=%s&consulate_time=9:00&appointments[expedite]=false"
APPOINTMENT_URL = f"https://ais.usvisa-info.com/{COUNTRY_CODE}/niv/schedule/{SCHEDULE_ID}/appointment"
EXIT = False

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def send_notification(msg):
    print(f"Sending notification: {msg}")

    if SENDGRID_API_KEY:
        message = Mail(
            from_email=USERNAME,
            to_emails=USERNAME,
            subject=msg,
            html_content=msg)
        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception as e:
            print(e.message)

    if PUSH_TOKEN:
        url = "https://api.pushover.net/1/messages.json"
        data = {
            "token": PUSH_TOKEN,
            "user": PUSH_USER,
            "message": msg
        }
        requests.post(url, data)


def get_driver():
    if LOCAL_USE:
        dr = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    else:
        dr = webdriver.Remote(command_executor=HUB_ADDRESS, options=webdriver.ChromeOptions())
    return dr

driver = get_driver()


def login():
    # Bypass reCAPTCHA
    driver.get(f"https://ais.usvisa-info.com/{COUNTRY_CODE}/niv")
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
    box.click()
    time.sleep(random.randint(1, 3))

    print("\tcommit")
    btn = driver.find_element(By.NAME, 'commit')
    btn.click()
    time.sleep(random.randint(1, 3))

    Wait(driver, 60).until(
        EC.presence_of_element_located((By.XPATH, REGEX_CONTINUE)))
    print("\tlogin successful!")


def get_date():
    driver.get(DATE_URL)
    if not is_logged_in():
        login()
        return get_date()
    else:
        content = driver.find_element(By.TAG_NAME, 'pre').text
        date = json.loads(content)
        return date


def get_cas_date(date):
    date_url = CAS_DATE_URL % date
    driver.get(date_url)
    content = driver.find_element(By.TAG_NAME, 'pre').text
    date = json.loads(content)
    return date[-1].get("date")


def select_date(date):
    time.sleep(STEP_TIME)
    month = driver.find_element(By.CSS_SELECTOR, '#ui-datepicker-div > .ui-datepicker-group-first .ui-datepicker-month')
    year = driver.find_element(By.CSS_SELECTOR, '#ui-datepicker-div > .ui-datepicker-group-first .ui-datepicker-year')
    expected_month = MONTHS[int(date[5:7]) - 1]
    expected_year = date[0:4]
    tries = 0

    while month.text != expected_month or year.text != expected_year and tries < 24:
        next_button = driver.find_element(By.CSS_SELECTOR, '.ui-datepicker-next.ui-corner-all')
        next_button.click()
        month = driver.find_element(By.CSS_SELECTOR, '#ui-datepicker-div > .ui-datepicker-group-first .ui-datepicker-month')
        year = driver.find_element(By.CSS_SELECTOR, '#ui-datepicker-div > .ui-datepicker-group-first .ui-datepicker-year')
        tries += 1

    if tries == 24:
        print("Could not find expected month/year")
        return False
    
    day_button = driver.find_element(By.XPATH, f'//a[text()="{date[8:10].lstrip("0")}"]')
    day_button.click()


def fill_form(date, appointment_office):
    time.sleep(STEP_TIME)
    date_input = driver.find_element(By.ID, f'appointments_{appointment_office}_appointment_date')
    date_input.click()

    select_date(date)
    time.sleep(STEP_TIME)
    # Calls the select_date function twice because sometimes it doesn't populate the time options
    date_input.click()
    select_date(date)

    # Sleeps waiting for the time's options to load
    time.sleep(2)
    time_select = Select(driver.find_element(By.ID, f'appointments_{appointment_office}_appointment_time'))
    time_select.select_by_index(0)
    

def fill_consulate_reschedule_form(date):
    print(f"Filling consulate reschedule form for {date}")
    fill_form(date, "consulate")


def fill_asc_reschedule_form(date):
    print(f"Filling CAS reschedule form for {date}")
    fill_form(date, "asc")


def submit_reschedule_form():
    reschedule_btn = driver.find_element(By.ID, 'appointments_submit')
    reschedule_btn.click()

    confirm_btn = driver.find_element(By.CSS_SELECTOR, 'a.button.alert')
    confirm_btn.click()


def reschedule(date):
    global EXIT
    print(f"Starting Reschedule ({date})")

    msg = f"Ready to reschedule for {date}"
    send_notification(msg)
    EXIT = True
    
    cas_date = get_cas_date(date)
    time.sleep(STEP_TIME)
    driver.get(APPOINTMENT_URL)

    if MULTIPLE_APPOINTMENTS:
        btn = driver.find_element(By.NAME, 'commit')
        btn.click()

    fill_consulate_reschedule_form(date)

    if cas_date:
        fill_asc_reschedule_form(cas_date)
        time.sleep(STEP_TIME)
        submit_reschedule_form()
        send_notification("Reschedule finished!")
    else:
        print("Could not find CAS date")
        send_notification("Could not find CAS date, please continue manually")


def is_logged_in():
    content = driver.page_source
    if(content.find("error") != -1):
        return False
    return True


def print_dates(dates):
    print("Available dates:")
    for d in dates:
        print("%s \t business_day: %s" % (d.get('date'), d.get('business_day')))
    print()


last_seen = None


def get_available_date(dates):
    global last_seen

    def is_earlier(date):
        my_date = datetime.strptime(MY_SCHEDULE_DATE, "%Y-%m-%d")
        new_date = datetime.strptime(date, "%Y-%m-%d")
        result = my_date > new_date
        print(f'Is {my_date} > {new_date}:\t{result}')
        return result

    print("Checking for an earlier date:")
    for d in dates:
        date = d.get('date')
        if is_earlier(date) and date != last_seen:
            _, month, day = date.split('-')
            if(MY_CONDITION(month, day)):
                last_seen = date
                return date


def push_notification(dates):
    msg = "date: "
    for d in dates:
        msg = msg + d.get('date') + '; '
    send_notification(msg)


if __name__ == "__main__":
    login()
    retry_count = 0
    while 1:
        if retry_count > 6:
            break
        try:
            print("------------------")
            print(datetime.today())
            print(f"Retry count: {retry_count}")
            print()

            dates = get_date()[:5]
            print_dates(dates)
            if dates and retry_count > 0:
                send_notification("Got dates!")
                retry_count = 0
            date = get_available_date(dates)
            print()
            print(f"New date: {date}")
            if date:
                push_notification(dates)
                reschedule(date)

            if(EXIT):
                print("------------------exit")
                break

            if not dates:
              if retry_count == 0:
                msg = "List is empty. Sleeping process for a while"
                send_notification(msg)
              time.sleep(RETRY_TIME)
              retry_count += 1
            else:
              time.sleep(SLEEP_TIME)
              retry_count = 0

        except:
            retry_count += 1
            time.sleep(EXCEPTION_TIME)

    if(not EXIT):
        send_notification("HELP! Crashed.")
