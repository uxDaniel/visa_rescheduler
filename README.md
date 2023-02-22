# visa_rescheduler
The visa_rescheduler is a bot for US VISA (usvisa-info.com) appointment rescheduling. This bot can help you reschedule your appointment to your desired time period.

## Prerequisites
- Having a US VISA appointment scheduled already.
- [Optional] API token from Pushover and/or a Sendgrid (for notifications)(You also can use the esender.php file in this repo as an email pusher on your website)

## Attention
- Right now, there are lots of unsupported embassies in our repository. A list of supported embassies is presented in the 'embassy.py' file.
- To add a new embassy (using English), you should find the embassy's "facility id." To do this, using google chrome, on the booking page of your account, right-click on the location section, then click "inspect." Then the right-hand window will be opened, highlighting the "select" item. You can find the "facility id" here and add this facility id in the 'embassy.py' file. There might be several facility ids for several different embassies. They can be added too. Please use the picture below as an illustration of the process.
![Finding Facility id](https://github.com/Soroosh-N/us_visa_scheduler/blob/main/_img.png?raw=true)

## Initial Setup
- Install Google Chrome [for install goto: https://www.google.com/chrome/]
- Install Python v3 [for install goto: https://www.python.org/downloads/]
- Install the required python packages: Just run the bat file in the Microsoft Windows. Or run the below commands:
```
pip install requests==2.27.1
pip install selenium==4.2.0
pip install webdriver-manager==3.7.0
pip install sendgrid==6.9.7
```

## How to use
- Initial setup!
- Edit information [config.ini.example file]. Then remove the ".example" from file name.
- [Optional] Edit your push notification accounts information [config.ini.example file].
- [Optional] Edit your website push notification [config.ini.example and esender.php files].
- Run visa.py file, using `python3 visa.py`

## TODO
- Make timing optimum. (There are lots of unanswered questions. How is the banning algorithm? How can we avoid it? etc.)
- Adding a GUI (Based on PyQt)
- Multi-account support (switching between accounts in Resting times)
- Add a sound alert for different events.
- Extend the embassies list.

## Acknowledgement
Thanks to everyone who participated in this repo. Lots of people are using your excellent product without even appreciating you.
