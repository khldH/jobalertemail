import os

import boto3
from dotenv import load_dotenv

from email_template import html_email
from send_alerts import (
    get_jobs_from_followed_orgs,
    get_relevant_jobs,
    save_sent_alerts,
    send_daily_job_alerts,
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

# local_db = boto3.resource(
#     "dynamodb", endpoint_url="http://localhost:8000", region_name="eu-west-2"
# )


def main():
    try:
        db = dynamodb_web_service
        _users = db.Table("users")
        users = _users.scan()["Items"]
        for user in users:
            matched_jobs = []
            relevant_jobs_found = get_relevant_jobs(db, user)
            matched_jobs.extend(relevant_jobs_found)
            jobs_posted_by_orgs_followed = get_jobs_from_followed_orgs(db, user)
            matched_jobs.extend(jobs_posted_by_orgs_followed)
            unique_matched_jobs = [
                dict(job) for job in set(tuple(sorted(j.items())) for j in matched_jobs)
            ]
            send_daily_job_alerts(
                db,
                user,
                unique_matched_jobs,
                html_email,
                secret_key,
                sender_email,
                sender_password,
            )
            save_sent_alerts(db, user, matched_jobs)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
