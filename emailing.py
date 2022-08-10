from email.mime.text import MIMEText
from email.utils import formataddr
from smtplib import SMTP


class Email:
    def __init__(self, usr, pwd, server="smtp.gmail.com", port=587):
        self.user = usr
        self.password = pwd
        self.server = server
        self.port = port

    def send_message(self, content: str, subject: str, mail_to: str):
        message = MIMEText(content, "html", "utf-8")
        message["Subject"] = subject
        message["From"] = formataddr(("diractly", self.user))
        message["To"] = mail_to
        try:
            mail_server = SMTP(self.server, self.port)
            mail_server.ehlo()
            mail_server.starttls()
            mail_server.ehlo()
            mail_server.login(self.user, self.password)
            mail_server.sendmail(self.user, mail_to, message.as_string())
            mail_server.quit()
            print("email sent successfully")
        except Exception as e:
            print(e)

    def send_resource(self, resource: str, mail_to: str):
        message = """<html> <head></head> <body> <p>Dear subscriber;<br><br> Thank you for using Diraclty. Please 
        tell us about your experience in this 30 seconds survey.<br> Your feedback will help us create a better 
        experience for you and other subscribers<br><br> <a href="{link}">{text}</a> <br><br>
        - Your friends at Diraclty </p> </body> </html>""".format(
            link=resource, text="Get Started"
        )
        self.send_message(message, "Tell us what you think of Diractly in 30 seconds", mail_to)
