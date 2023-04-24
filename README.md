# visa_rescheduler
US VISA (ais.usvisa-info.com) appointment re-scheduler - Colombian adaptation

## Prerequisites
- Having a US VISA appointment scheduled already
- Google Chrome installed (to be controlled by the script)
- Python v3 installed (for running the script)
- API token from Pushover and/or a Sendgrid (for notifications)


## Initial Setup
- Create a `config.ini` file with all the details required
- Install the required python packages: `pip3 install -r requirements.txt`

## Executing the script
- Simply run `python3 visa.py`
- That's it!

## Acknowledgement
Thanks to @yaojialyu for creating the initial script and to @cejaramillof for adapting it to Colombia!

## Troubleshooting
> Getting "ValueError: There is no such driver by url ..." when executing the script

The format of the urls seem to have changed, so depending on your device you might find this issue. This can be fixed by executing:
`python3 -m pip install webdriver-manager --upgrade`
`python3 -m pip install packaging`