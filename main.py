from email_template import html_email
from send_alerts import (dynamodb_web_service, get_relevant_jobs, #local_db,
                         save_sent_alerts, send_daily_job_alerts)


def main():
    db = dynamodb_web_service
    aws_db_table_users = db.Table("users")
    aws_users = aws_db_table_users.scan()["Items"]
    for user in aws_users:
        # print(user)
        try:
            relevant_jobs_found = get_relevant_jobs(db, user)
            # print(relevant_jobs_found)
            send_daily_job_alerts(db, user, html_email)
            save_sent_alerts(db, user, relevant_jobs_found)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()
