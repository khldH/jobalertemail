import os
import re
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Attr
from dotenv import load_dotenv
from itsdangerous import BadData, URLSafeSerializer

from document_search import Document, DocumentSearch
from emailing import Email

load_dotenv()

sender_email = os.getenv("EMAIL_SENDER")
sender_password = os.getenv("EMAIL_SENDER_PASSWORD")
is_prod = os.getenv("is_prod")
secret_key = os.getenv("SECRET_KEY")

dynamodb_web_service = boto3.resource(
    "dynamodb",
    region_name=os.getenv("AWS_REGION_NAME"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

# local_db = boto3.resource("dynamodb", endpoint_url="http://localhost:8000")


def get_relevant_jobs(db_con, user):
    table = db_con.Table("jobs")
    jobs = table.scan()["Items"]
    documents = []
    for job in jobs:
        documents.append(Document(**job))
    if user["is_active"]:
        try:
            # print(user)
            document_search = DocumentSearch(documents)
            query = re.sub("[^A-Za-z0-9]+", " ", user["job_description"])
            if len(query) > 1:
                relevant_jobs = document_search.search(query)
                # print(relevant_jobs)
                return relevant_jobs
        except Exception as e:
            print(e)
    return []


def send_daily_job_alerts(db_con, user, email_template):
    table_sent_job_alerts = db_con.Table("sent_job_alerts")
    alerts = table_sent_job_alerts.scan(
        FilterExpression=Attr("user_id").eq(user["id"])
    )["Items"]
    sent_job_urls = []
    if len(alerts):
        for alert in alerts:
            sent_job_urls.append(alert["job_url"])
    user_relevant_jobs = get_relevant_jobs(db_con, user)
    if len(user_relevant_jobs) > 0:
        rows = ""
        count_new_jobs = 0
        for item in user_relevant_jobs:
            if item["url"] not in sent_job_urls:
                count_new_jobs += 1
                days_since_posted = ""
                if item["days_since_posted"] == 0:
                    days_since_posted += "today"
                elif item["days_since_posted"] == 1:
                    days_since_posted += "yesterday"
                else:
                    days_since_posted += (
                        str(item["days_since_posted"]) + " " + "days ago"
                    )
                rows = (
                    rows + "<tr><td>"
                    "<a href=" + item["url"] + ">" + str(item["title"]) + "</a>"
                    "</td></tr>"
                )
                rows = rows + "<tr><td>" + str(item["organization"]) + "</td></tr>"
                rows = rows + "<tr><td>" + days_since_posted + "</td></tr>"
                rows = rows + "<br>"
        if rows:
            try:
                s = URLSafeSerializer(secret_key, salt="unsubscribe")
                token = s.dumps(user["email"])
                url = "http://localhost:8001/unsubscribe/{}".format(token)
                # rows = rows + "<tr><td>" + url + "</td></tr>"

                content = email_template.format(
                    jobs=rows,
                    unsubscribe_url=url,
                    title=count_new_jobs,
                    saved_alert=user["job_description"],
                )
                email_title = (
                    str(count_new_jobs) + " " + "new" + " " + user["job_description"]
                )
                email = Email(sender_email, sender_password)
                email.send_message(content, email_title, user["email"])
            except Exception as e:
                print(e)
        else:
            print("No new job alerts sent")
    else:
        print("no new matches found")


def save_sent_alerts(db_con, user, alerts):
    aws_db_table_sent_job_alerts = db_con.Table("sent_job_alerts")
    try:
        for item in alerts:
            aws_db_table_sent_job_alerts.put_item(
                Item={
                    "user_id": user["id"],
                    "job_id": item["id"],
                    "job_url": item["url"],
                    "user_id_job_url": user["id"] + item["url"],
                    "created_at": datetime.utcnow().isoformat(),
                }
            )
    except Exception as e:
        print(e)
