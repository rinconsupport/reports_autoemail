import os
import sys
import logging
import logging.handlers as handlers
from datetime import datetime, timedelta
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
import pyodbc
import csv

# Logging Configuration

logger = logging.getLogger("Esperti Reporting Service")
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
    os.path.join(Log, datetime.now().strftime(
        "log_file_%Y_%m_%d.log")),
    maxBytes=5000000,
    backupCount=10,
)
logHandler.setLevel(logging.DEBUG)

# create a logging format
formatter = logging.Formatter(
    "%(asctime)s: [%(thread)d]:[%(name)s]: %(levelname)s:[EmailReporting] - %(message)s"
)
logHandler.setFormatter(formatter)
ch.setFormatter(formatter)

# add the handlers to the logger

logger.addHandler(logHandler)
logger.addHandler(ch)


# GLOBAL VARIABLES
BASE_PATH = os.path.dirname(os.path.realpath(__file__))

logger.debug("Application Initialized...")


def create_report_folder():
    reports = os.path.join(BASE_PATH, 'Reports')
    if not os.path.exists(reports):
        os.mkdir(reports)
        logger.debug("Folder has been created")
        return reports
    return reports


def db_connection():
    try:
        logger.debug("Connecting to SQL DB...")
        cnxn = pyodbc.connect(
            r'DRIVER={ODBC Driver 17 for SQL Server};SERVER=.\SQLEXPRESS;DATABASE=AutoReply;UID=sa;PWD=sadmin@123')
        cursor = cnxn.cursor()
    except Exception as ConnectionError:
        logger.debug(ConnectionError, exc_info=True)
        return False
    logger.debug("<<<<CONNECTED TO DB>>>>")
    return cursor


def db_to_csv(hours=config.hours):
    logger.debug("Fetching data from SQL table...")
    query = db_connection()
    if query:

        current_date = datetime.today().strftime(
            "%Y-%m-%d %H:%M:%S")

        dt_range = datetime.strptime(
            current_date, "%Y-%m-%d %H:%M:%S") - timedelta(hours=hours)

        print(dt_range)

        query.execute(r"SELECT * from esperti_reports WHERE NOT (action_time > '{}' OR action_time < '{}')".format(
            current_date, dt_range))

        reports = create_report_folder()

        rep_folder = os.path.join(
            reports, datetime.now().strftime('%Y_%m_%d'))

        if not os.path.exists(rep_folder):
            os.mkdir(rep_folder)

        csv_file = os.path.join(rep_folder, datetime.now().strftime(
            '%Y_%m_%d_daily_report.csv'))

        try:
            with open(csv_file, "w", newline="") as csv_f:
                csv_writer = csv.writer(csv_f)
                csv_writer.writerow([i[0]
                                     for i in query.description])  # write headers
                csv_writer.writerows(query)
                logger.debug(
                    "Data has been fetched from table and dumped to csv file")

                return {"status": "CSV_GENERATED"}
        except Exception as Error:
            logger.debug("Could not generate csv file...")
            logger.debug(Error, exc_info=True)
    else:
        logger.debug("Error connecting SQL Server")
        return False


def get_csv_report_file(base_dir):
    """
    fetches the report (CSV) file for the today which is current date.
    @Returns :file object
    :base_dir :path

    """

    logger.debug("Fetching report for current date: {}".format(
        datetime.now().strftime("%d %b %Y")))
    reports = os.path.join(base_dir, 'Reports')
    rep_folder = os.path.join(base_dir, os.path.join(
        reports, datetime.now().strftime('%Y_%m_%d')))

    if os.path.isdir(rep_folder):
        for file in os.listdir(rep_folder):
            logger.debug("Report find to be emailed: {}".format(
                os.path.basename(file)))
            return file
    else:
        return None


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
        reports, datetime.now().strftime('%Y_%m_%d')))
    try:
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['CC'] = ",".join(cc_list)
        msg['To'] = to
        msg['Subject'] = subject

        if has_attachment == "yes":
            body = mailbody.mail_string.format(
                datetime.now().strftime("%d %b %Y"))
            msg.attach(MIMEText(body, 'html'))
            filename = os.path.join(rep_folder, get_csv_report_file(BASE_PATH))
            attachment = open(os.path.join(rep_folder, filename), 'rb')
            part = MIMEBase('application', 'octet-stream')
            part.set_payload((attachment).read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition',
                            "attachment; filename= "+os.path.basename(filename))
            msg.attach(part)

        else:
            body = noreport.mail_string.format(
                datetime.now().strftime("%d %b %Y"))
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

    generate_csv = db_to_csv()

    if generate_csv['status'] == 'CSV_GENERATED':

        is_available = get_csv_report_file(BASE_PATH)
        if not is_available == None:
            response = send_email(config.email_to_notify,
                                  config.username, "OceanFax Transaction Report - {}".format(datetime.now().strftime("%d %b %Y")), BASE_PATH, has_attachment="yes")

            if not response['status'] == 200:
                logger.debug("Error occured while sending report")
                sys.exit(1)

            else:
                logger.debug("Report has been successfully sent!!!")
                sys.exit(0)
        else:
            response = send_email(config.email_to_notify,
                                  config.username, "OceanFax Transaction Report - {}".format(datetime.now().strftime("%d %b %Y")), BASE_PATH, has_attachment="no")

            if not response['status'] == 200:
                logger.debug("Error occured while sending report")
                sys.exit(1)

            else:
                logger.debug("Email successfully sent!!!")
                sys.exit(0)
    else:
        logger.debug("Error connecting SQL DB..")
