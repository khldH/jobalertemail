from send_alerts import (
    send_daily_job_alerts,
    get_relevant_jobs,
    save_sent_alerts,
    dynamodb_web_service,
    # local_db,
    # is_prod,
)
from email_template import html_email


def main():
    db = dynamodb_web_service
    aws_db_table_users = db.Table("users")
    aws_users = aws_db_table_users.scan()["Items"]
    for user in aws_users:
        try:
            relevant_jobs_found = get_relevant_jobs(db, user)
            send_daily_job_alerts(db, user, html_email)
            save_sent_alerts(db, user, relevant_jobs_found)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()
