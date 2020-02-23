import smtplib
import logging
import os


try:
    USER_PASSWORD = os.environ['MAIL_PASSWORD']
except KeyError:
    logging.error('MAIL_PASSWORD environment variable is not set. Please fix')
    raise Exception('MAIL_PASSWORD environment variable is not set. Please fix')

USER_FROM = "gjl.safebox@gmail.com"
# EMAIL_LIST=["operations@greyjuicelab.com","anadon@greyjuicelab.com"]
EMAIL_LIST = ['mpalop@gmail.com']


def send_email(subject, body):
    user_to = EMAIL_LIST
    message = "From: {}\nTo: {}\nSubject: {}\n\n{}".format(USER_FROM, ", ".join(user_to), subject, body)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(USER_FROM, USER_PASSWORD)
        server.sendmail(USER_FROM, user_to, message)
        server.close()
        logging.info('successfully sent the mail')
    except Exception as e:
        print(str(message[81:86]))
        print("----------------")
        logging.info('failed to send mail. message:\n{}\nerror:\n{}'.format(message, e))
