import os
import sys
import logging
import logging.handlers as handlers
import datetime
import shutil
import smtplib
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from pprint import pprint
import config
import time
import mailbody
import noreport
# Logging Configuration

logger = logging.getLogger("FileRenamerService")
logger.setLevel(logging.DEBUG)

# maintains log file here  # maintains log file here
Log = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Log")
if not os.path.exists(Log):
    os.mkdir(Log)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# logHandler = handlers.TimedRotatingFileHandler(os.path.join(Log, datetime.datetime.now(
# ).strftime('log_file_%Y_%m_%d.log')), when='midnight', backupCount=10)
logHandler = handlers.RotatingFileHandler(
    os.path.join(Log, datetime.datetime.now().strftime(
        "log_file_%Y_%m_%d.log")),
    maxBytes=5000000,
    backupCount=10,
)
logHandler.setLevel(logging.DEBUG)

# create a logging format
formatter = logging.Formatter(
    "%(asctime)s: [%(thread)d]:[%(name)s]: %(levelname)s:[FileRenamer] - %(message)s"
)
logHandler.setFormatter(formatter)
ch.setFormatter(formatter)

# add the handlers to the logger

logger.addHandler(logHandler)
logger.addHandler(ch)


# GLOBAL VARIABLES
BASE_PATH = os.path.dirname(os.path.realpath(__file__))

logger.debug("Application Initialized...")


def get_csv_report_file(base_dir):
    """
    fetches the report (CSV) file for the today which is current date.
    @Returns :file object
    :base_dir :path

    """

    logger.debug("Fetching report for current date: {}".format(
        datetime.datetime.now().strftime("%d %b %Y")))
    reports = os.path.join(base_dir, 'Reports')
    rep_folder = os.path.join(base_dir, os.path.join(
        reports, datetime.datetime.now().strftime('%Y_%m_%d')))
    for file in os.listdir(rep_folder):
        logger.debug("Report find to be emailed: {}".format(
            os.path.basename(file)))
        return file


def send_email(to, from_email, subject, base_dir, has_attachment=""):
    """
    Send email with attached report to users.

    Returns : status of email sent (200 for success and 500 for any error occured.)
    :to :string (email)
    :from_email :string(email)
    :subject : string
    :base_dir :path

    """
    logger.debug("sending email to users with attached report file...")
    cc_list = config.cc_emails
    reports = os.path.join(base_dir, 'Reports')
    rep_folder = os.path.join(base_dir, os.path.join(
        reports, datetime.datetime.now().strftime('%Y_%m_%d')))
    try:
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['CC'] = ",".join(cc_list)
        msg['To'] = to
        msg['Subject'] = subject

        if has_attachment == "yes":
            body = mailbody.mail_string.format(
                datetime.datetime.now().strftime("%d %b %Y"))
            msg.attach(MIMEText(body, 'html'))
            filename = os.path.join(rep_folder, get_csv_report_file(BASE_PATH))
            attachment = open(os.path.join(rep_folder, filename), 'rb')
            part = MIMEBase('application', 'octet-stream')
            part.set_payload((attachment).read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition',
                            "attachment; filename= "+os.path.basename(filename))
            msg.attach(part)

            recipients = [to]+cc_list
            text = msg.as_string()
            server = smtplib.SMTP(
                config.smtp_host, config.port, config.timeout)
            server.starttls()
            server.login(config.username, config.password)
            server.sendmail(from_email, recipients, text)
            server.quit()

            return {"status": 200}

        else:
            body = noreport.mail_string.format(
                datetime.datetime.now().strftime("%d %b %Y"))
            msg.attach(MIMEText(body, 'html'))
            recipients = [to]+cc_list
            text = msg.as_string()
            server = smtplib.SMTP(
                config.smtp_host, config.port, config.timeout)
            server.starttls()
            server.login(config.username, config.password)
            server.sendmail(from_email, recipients, text)
            server.quit()

            return {"status": 200}
    except Exception as Error:

        if Error:
            logger.debug("Error occured while sending reports")
            logger.debug(Error, exc_info=True)
            return {"status": 500}


if __name__ == '__main__':

    is_available = get_csv_report_file(BASE_PATH)
    if not is_available == None:
        response = send_email(config.email_to_notify,
                              config.username, "OceanFax Transaction Report - {}".format(datetime.datetime.now().strftime("%d %b %Y")), BASE_PATH, has_attachment="yes")

        if not response['status'] == 200:
            logger.debug("Error occured while sending report")
            sys.exit(1)

        else:
            logger.debug("Report has been successfully sent!!!")
            sys.exit(0)
    else:
        response = send_email(config.email_to_notify,
                              config.username, "OceanFax Transaction Report - {}".format(datetime.datetime.now().strftime("%d %b %Y")), BASE_PATH, has_attachment="no")

        if not response['status'] == 200:
            logger.debug("Error occured while sending report")
            sys.exit(1)

        else:
            logger.debug("Email successfully sent!!!")
            sys.exit(0)
