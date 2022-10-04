import os

import boto3
from dotenv import load_dotenv
from emailing import Email
import time
from itsdangerous import BadData, URLSafeSerializer
from random import sample

from email_template import html_email
from send_alerts import (
    get_jobs_from_followed_orgs,
    get_relevant_jobs,
    save_sent_alerts,
    send_daily_job_alerts,
    get_new_jobs_posted_recently,
)

load_dotenv()

sender_email = os.getenv("EMAIL_SENDER")
sender_password = os.getenv("EMAIL_SENDER_PASSWORD")
secret_key = os.getenv("SECRET_KEY")

dynamodb_web_service = boto3.resource(
    "dynamodb",
    region_name=os.getenv("AWS_REGION_NAME"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

# local_db = boto3.resource("dynamodb", endpoint_url="http://localhost:8000")


def main():
    # try:
    db = dynamodb_web_service
    users = db.Table("users").scan()["Items"]
    jobs = db.Table("jobs").scan()["Items"]
    sent_job_alerts_table = db.Table("sent_job_alerts")
    sent_job_alerts = sent_job_alerts_table.scan()["Items"]
    jobs_posted_recently = get_new_jobs_posted_recently(jobs)
    for user in users:
        if user["is_active"] and user.get("is_all", None):
            send_daily_job_alerts(
                sent_job_alerts,
                user,
                jobs_posted_recently,
                html_email,
                secret_key,
                sender_email,
                sender_password,
            )
            save_sent_alerts(sent_job_alerts_table, user, jobs_posted_recently)
        else:
            matched_jobs = []
            relevant_jobs_found = get_relevant_jobs(jobs_posted_recently, user)
            matched_jobs.extend(relevant_jobs_found)
            jobs_posted_by_orgs_followed = get_jobs_from_followed_orgs(jobs_posted_recently, user)
            matched_jobs.extend(jobs_posted_by_orgs_followed)
            unique_matched_jobs = [
                dict(job)
                for job in set(tuple(sorted(j.items())) for j in matched_jobs)
            ]
            send_daily_job_alerts(
                sent_job_alerts,
                user,
                unique_matched_jobs,
                html_email,
                secret_key,
                sender_email,
                sender_password,
            )
            save_sent_alerts(sent_job_alerts_table, user, matched_jobs)


# except Exception as e:
#     print(e)


if __name__ == "__main__":
    main()

    # db = dynamodb_web_service
    # users = db.Table("users").scan()["Items"]
    #
    # # edit_token = e.dumps(user["email"])
    # email = Email(sender_email, sender_password)
    # # fifty_random_users = sample(users, 50)
    # # print(len(fifty_random_users))
    # try:
    #     for user in users:
    #         e = URLSafeSerializer(secret_key, salt="edit")
    #         edit_token = e.dumps(user["email"])
    #         edit_url = "http://www.diractly.com/edit/{}".format(edit_token)
    #         if user["is_active"] and user.get("first_name", None) is None:
    #             print(user['email'])
    #             email.send_resource(edit_url,  user['email'])
    #             time.sleep(5)
    # except Exception as e:
    #     print(e)
