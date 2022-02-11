import os
from document_search import Document, DocumentSearch
import re
from dotenv import load_dotenv
import boto3
from email_template import html_email
from emailing import Email

load_dotenv()

sender_email = os.getenv('EMAIL_SENDER')
sender_password = os.getenv('EMAIL_SENDER_PASSWORD')

dynamodb_web_service = boto3.resource(
    "dynamodb",
    region_name=os.getenv('AWS_REGION_NAME'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
)


def send_daily_job_alerts(db_con, user, email_template):
    table = db_con.Table("jobs")
    jobs = table.scan()["Items"]
    documents = []
    for job in jobs:
        documents.append(Document(**job))
    if user['is_active']:
        try:
            # print(user)
            document_search = DocumentSearch(documents)
            query = re.sub("[^A-Za-z0-9]+", " ", user['job_description'])
            relevant_jobs = []
            if len(query) > 1:
                relevant_jobs = document_search.search(query)
            if len(relevant_jobs) > 0:
                rows = ""
                for item in relevant_jobs:
                    rows = rows + "<tr><td>" "<a href=" + item['url'] + ">" + str(item['title']) + "</a>" "</td></tr>"
                    rows = rows + "<tr><td>" + str(item['organization']) + "</td></tr>"
                    rows = rows + "<tr><td>" + str(item['days_since_posted']) + " " + "days ago" + "</td></tr>"
                    rows = rows + "<br>"
                if rows:
                    content = email_template.format(jobs=rows, title=len(relevant_jobs),
                                                    saved_alert=user['job_description'])

                    email_title = str(len(relevant_jobs)) + " " + "new" + " " + user['job_description']

                    email = Email(sender_email, sender_password)
                    email.send_message(content, email_title, user['email'])

            return relevant_jobs
        except ValueError as e:
            print(e)



