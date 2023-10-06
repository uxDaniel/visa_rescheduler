# -*- coding: utf8 -*-

import time
import json
import random
import platform
import configparser
from datetime import datetime

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as Wait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.select import Select

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


config = configparser.ConfigParser()
config.read('config.ini')

USERNAME = config['USVISA']['USERNAME']
PASSWORD = config['USVISA']['PASSWORD']
SCHEDULE_ID = config['USVISA']['SCHEDULE_ID']
MY_SCHEDULE_DATE = config['USVISA']['MY_SCHEDULE_DATE']
COUNTRY_CODE = config['USVISA']['COUNTRY_CODE'] 
FACILITY_ID = config['USVISA']['FACILITY_ID']

SENDGRID_API_KEY = config['SENDGRID']['SENDGRID_API_KEY']
PUSH_TOKEN = config['PUSHOVER']['PUSH_TOKEN']
PUSH_USER = config['PUSHOVER']['PUSH_USER']

LOCAL_USE = config['CHROMEDRIVER'].getboolean('LOCAL_USE')
HUB_ADDRESS = config['CHROMEDRIVER']['HUB_ADDRESS']

REGEX_CONTINUE = "//a[contains(text(),'Continue')]"


# def MY_CONDITION(month, day): return int(month) == 11 and int(day) >= 5
def MY_CONDITION(month, day): return True # No custom condition wanted for the new scheduled date

STEP_TIME = 0.5  # time between steps (interactions with forms): 0.5 seconds
RETRY_TIME = 60*3  # wait time between retries/checks for available dates: 3 minutes
EXCEPTION_TIME = 60*30  # wait time when an exception occurs: 30 minutes
COOLDOWN_TIME = 60*60  # wait time when temporary banned (empty list): 60 minutes

DATE_URL = f"https://ais.usvisa-info.com/{COUNTRY_CODE}/niv/schedule/{SCHEDULE_ID}/appointment/days/{FACILITY_ID}.json?appointments[expedite]=false"
TIME_URL = f"https://ais.usvisa-info.com/{COUNTRY_CODE}/niv/schedule/{SCHEDULE_ID}/appointment/times/{FACILITY_ID}.json?date=%s&appointments[expedite]=false"
APPOINTMENT_URL = f"https://ais.usvisa-info.com/{COUNTRY_CODE}/niv/schedule/{SCHEDULE_ID}/appointment"
EXIT = False


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
        caps = DesiredCapabilities.CHROME
        caps['goog:loggingPrefs'] = {'performance': 'ALL'}
        # dr = webdriver.Chrome(desired_capabilities=caps, service=Service(ChromeDriverManager().install()))
        service = Service()
        options = webdriver.ChromeOptions()
        dr = webdriver.Chrome(service=service, options=options)
    else:
        dr = webdriver.Remote(command_executor=HUB_ADDRESS, options=webdriver.ChromeOptions())
    return dr

driver = get_driver()



def process_browser_log_entry(entry):
    response = json.loads(entry['message'])['message']
    return response



def get_date_new(url):
    # no longer able to jump with url, go there by clicking the button
    #driver.get(url)
    continueBtn = driver.find_element(By.XPATH, '//a[contains(text(),"Continue")]')
    continueBtn.click()
    time.sleep(2) # wait for all the data to arrive. 
    # find the 4th item's child element in the list
    serviceList = driver.find_element(By.XPATH, '//ul[@class="accordion custom_icons"]')
    child_elements = serviceList.find_elements_by_css_selector("li")
    # get the 4th chiild item from the list then the first item that
    rescheduleBtn = (child_elements[3].find_elements_by_css_selector("a"))[0]
    rescheduleBtn.click()
    time.sleep(2) # wait for all the data to arrive. 
    realRescheduleBtn = driver.find_element(By.XPATH, '//a[contains(text(),"Reschedule Appointment")]')
    realRescheduleBtn.click()
    time.sleep(2) # wait for all the data to arrive.
    browser_log = driver.get_log('performance')
    events = [process_browser_log_entry(entry) for entry in browser_log]
    events = [event for event in events if 'Network.response' in event['method']]
    targetIndex = -1;
    for event in events:
        if "response" in event["params"] and "url" in event["params"]["response"]:
            if "/appointment/days/" in event["params"]["response"]["url"]:
                print ("Found the target url: " + event["params"]["response"]["url"])
                print ("Index: " + str(events.index(event)))
                targetIndex = events.index(event)
                break
    print("check target index: " + str(targetIndex))
    if targetIndex != -1:
        body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': events[targetIndex]["params"]["requestId"]})
        print("Here is the body: " + str(body))
        available_date = json.loads(body["body"])
        
        return available_date
    else:
        return []


def login():
    # Bypass reCAPTCHA
    driver.get(f"https://ais.usvisa-info.com/{COUNTRY_CODE}/niv")
    time.sleep(STEP_TIME)
    a = driver.find_element(By.XPATH, '//a[@class="down-arrow bounce"]')
    a.click()
    time.sleep(STEP_TIME)

    print("Login start...")
    href = driver.find_element(By.XPATH, '//*[@id="header"]/nav/div[1]/div[1]/div[2]/div[1]/ul/li[3]/a')
   
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


def get_time(date):
    time_url = TIME_URL % date
    driver.get(time_url)
    content = driver.find_element(By.TAG_NAME, 'pre').text
    data = json.loads(content)
    time = data.get("available_times")[-1]
    print(f"Got time successfully! {date} {time}")
    return time


def select_time_manually(date):
    print("---------------TEST START-----------------")
    print("test date: " + str(date))
    year = date["date"].split("-")[0]
    month = date["date"].split("-")[1]
    day = date["date"].split("-")[2]

    datepicker = driver.find_element(By.ID, 'appointments_consulate_appointment_date')
    print("datepicker: " + str(datepicker))
    datepicker.click()
    time.sleep(0.5)
    print("after snap")
    #find the available date button
    print("is there any btn?" + str(len( driver.find_elements(By.XPATH, '//a[@class="ui-state-default"]')) > 0))
    hasDate = len(driver.find_elements(By.XPATH, '//a[@class="ui-state-default"]')) > 0 
    print("First hasDate: " + str(hasDate))
    while not hasDate:
        print("No date available, click next month button")
        print("current hasDate: " + str(hasDate))
        #click next month button
        nextBtn = driver.find_element(By.XPATH, '//a[contains(@class, "ui-datepicker-next ui-corner-all")]')
        print("nextBtn: " + str(nextBtn))
        nextBtn.click()
        time.sleep(0.5)
        #find the available date button
        hasDate = len(driver.find_elements(By.XPATH, '//a[@class="ui-state-default"]')) > 0 
        if hasDate == True:
            hasDate = driver.find_elements(By.XPATH, '//a[@class="ui-state-default"]')
            print("hasDate: " + str(hasDate))
            break
        else:
            continue
    
    parentDateBox = driver.execute_script("return arguments[0].parentNode;", hasDate[0])

    print("web day: " + hasDate[0].text)
    print("day: " + str(int(day)))
    print("web month: " + str(int(parentDateBox.get_attribute("data-month")) + 1))
    print("month: " + str(int(month)))
    print("web year: " + str(parentDateBox.get_attribute("data-year")))
    print("year: " + year)

    if str(int(day)) == hasDate[0].text and str(int(month)) == str(int(parentDateBox.get_attribute("data-month")) + 1) and year == str(parentDateBox.get_attribute("data-year")):
        print("Found the date!")
        parentDateBox.click()
        time.sleep(1) # wait for all the data to arrive. 
        browser_log = driver.get_log('performance')
        events = [process_browser_log_entry(entry) for entry in browser_log]
        events = [event for event in events if 'Network.response' in event['method']]
        targetIndex = -1;
        for event in events:
            if "response" in event["params"] and "url" in event["params"]["response"]:
                if "/appointment/times/" in event["params"]["response"]["url"]:
                    print ("Found the target url: " + event["params"]["response"]["url"])
                    print ("Index: " + str(events.index(event)))
                    targetIndex = events.index(event)
                    break
        if targetIndex != -1:
            body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': events[targetIndex]["params"]["requestId"]})
            print("Here is the TIMES body: " + str(body))
            available_times = json.loads(body["body"])
            return available_times
        else:
            print("Fail to get the available times request body")
            return False


    print("Final hasDate date: " + str(hasDate[0].text))
    #month count starts from 0
    print("Final hasDate month: " + str(parentDateBox.get_attribute("data-month")))
    print("Final hasDate year: " + str(parentDateBox.get_attribute("data-year")))
    #click the available date button
    # for dateButton in hasDate:
    #     if dateButton.text == date:
    #         dateButton.click()
    #         break


def reschedule(date):
    global EXIT
    print(f"Starting Reschedule ({date})")

    available_date = select_time_manually(date)
    timesBody = select_time_manually(available_date[0])
    print("Here is the timesBody: " + str(timesBody))
    print(timesBody["available_times"])
    if timesBody != False and (len(timesBody["available_times"]) > 0):
        print("if right")
        timeDropDown = driver.find_element(By.ID, 'appointments_consulate_appointment_time')
        timeDropDownSelect = Select(timeDropDown)
        print(str(timesBody["available_times"][0]))
        timeDropDownSelect.select_by_visible_text(str(timesBody["available_times"][0]))
        time.sleep(0.5)
        driver.find_element(By.ID, 'appointments_submit').click()
        time.sleep(0.5)
        driver.find_element(By.XPATH, '//a[contains(text(), "Confirm")]').click()
        print(f"Scheduleing Successful in: ({date})")
        EXIT = True
    else:
        print("else GG")
        return False

    



#--------------------old code--------------------
    # data = {
    #     "utf8": driver.find_element(by=By.NAME, value='utf8').get_attribute('value'),
    #     "authenticity_token": driver.find_element(by=By.NAME, value='authenticity_token').get_attribute('value'),
    #     "confirmed_limit_message": driver.find_element(by=By.NAME, value='confirmed_limit_message').get_attribute('value'),
    #     "use_consulate_appointment_capacity": driver.find_element(by=By.NAME, value='use_consulate_appointment_capacity').get_attribute('value'),
    #     "appointments[consulate_appointment][facility_id]": FACILITY_ID,
    #     "appointments[consulate_appointment][date]": date,
    #     "appointments[consulate_appointment][time]": time,
    # }

    # headers = {
    #     "User-Agent": driver.execute_script("return navigator.userAgent;"),
    #     "Referer": APPOINTMENT_URL,
    #     "Cookie": "_yatri_session=" + driver.get_cookie("_yatri_session")["value"]
    # }

    # print("Rescheduling...")
    # print(data)
    # print(headers)

    # r = requests.post(APPOINTMENT_URL, headers=headers, data=data)
    # if(r.text.find('Successfully Scheduled') != -1):
    #     msg = f"Rescheduled Successfully! {date} {time}"
    #     send_notification(msg)
    #     EXIT = True
    # else:
    #     msg = f"Reschedule Failed. {date} {time}"
    #     send_notification(msg)
#--------------------old code--------------------

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

            dates = get_date_new(APPOINTMENT_URL)[:5]
            # if not dates:
            #   msg = "List is empty"
            #   send_notification(msg)
            #   EXIT = True
            print_dates(dates)
            date = get_available_date(dates)
            print()
            print(f"New date: {date}")
            if date:
                rescheduleRes = reschedule(date)
                if not rescheduleRes:
                    time.sleep(RETRY_TIME)
                    continue
                push_notification(dates)

            if(EXIT):
                print("------------------exit")
                break

            if not dates:
              msg = "List is empty"
              send_notification(msg)
              #EXIT = True
              time.sleep(RETRY_TIME)
            else:
              time.sleep(RETRY_TIME)

        except:
            retry_count += 1
            time.sleep(EXCEPTION_TIME)

    if(not EXIT):
        send_notification("HELP! Crashed.")
