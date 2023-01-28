# visa_rescheduler
US VISA (usvisa-info.com) appointment re-scheduler

## Prerequisites
- Having a US VISA appointment scheduled already
- [Optional] API token from Pushover and/or a Sendgrid (for notifications)(You also can use the esender.php file in this repo as an email pusher on your website)


## Initial Setup
- Install Google Chrome [for install goto: https://www.google.com/chrome/]
- Install Python v3 [for install goto: https://www.python.org/downloads/]
- Install the required python packages: Just run the bat file in windows. You can check the requirements by editing it as a txt-file.

## How to use
- Initial setup!
- Edit your personal and embassy information [visa.py file].
- [Optional] Edit your push notification accounts information [visa.py].
- [Optional] Edit your site push notification [visa.py and esender.php files].
- Run `python3 visa.py`

## TODO
- Adding a library of countries and their 
- Make timing optimum. (There are lots of unanswered questions. How is the banning algorithm? How can we avoid it? etc.)
- Adding a GUI (Based on PyQt)
- Multi-account support (switching between accounts in Resting times)

## Acknowledgement
Thanks to everyone who participated in this repo. Lots of people are using your excellent product without even appreciating you.
