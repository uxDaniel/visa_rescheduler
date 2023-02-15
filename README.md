# visa_rescheduler
US VISA (usvisa-info.com) appointment re-scheduler

## Prerequisites
- Having a US VISA appointment scheduled already
- [Optional] API token from Pushover and/or a Sendgrid (for notifications)(You also can use the esender.php file in this repo as an email pusher on your website)

## Attention
- Right now, there are lots of countries which are not supported. List of supported countries is presented in 'embassy.py' file.

## Initial Setup
- Install Google Chrome [for install goto: https://www.google.com/chrome/]
- Install Python v3 [for install goto: https://www.python.org/downloads/]
- Install the required python packages: Just run the bat file in windows. Or run the below commands:
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
- Run `python3 visa.py`

## TODO
- Make timing optimum. (There are lots of unanswered questions. How is the banning algorithm? How can we avoid it? etc.)
- Adding a GUI (Based on PyQt)
- Multi-account support (switching between accounts in Resting times)
- Add sound alert for different events.
- Extend the embassies list.

## Acknowledgement
Thanks to everyone who participated in this repo. Lots of people are using your excellent product without even appreciating you.
