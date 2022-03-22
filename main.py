from email_template import html_email
from send_alerts import (dynamodb_web_service, get_relevant_jobs,  # local_db,
                         save_sent_alerts, send_daily_job_alerts)


def main():
    db = dynamodb_web_service
    _users = db.Table("users")
    users = _users.scan()["Items"]
    for user in users:
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
