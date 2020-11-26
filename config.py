import os


username = "sachins@rincon.co.in"
password = os.environ.get("password")
# this can be main admin email id.
email_to_notify = "sachinksalve90@gmail.com"
# all list of cc emails goes here. Add multiple ccs as strings separated by comma e.g ['ex1', 'ex2', 'ex3']
cc_emails = ["sachins@rincon.co.in"]


# EMAIL SMTP CONFIG
# smtp_host = "smtp-mail.outlook.com"
smtp_host = "smtp.gmail.com"
port = 587
timeout = 120  # seconds

# last xx hours report configguration
hours = 24
