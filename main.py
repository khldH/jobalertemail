from send_alerts import send_daily_job_alerts, dynamodb_web_service
from email_template import html_email


def main():
    aws_db_table_users = dynamodb_web_service.Table('users')
    aws_users = aws_db_table_users.scan()['Items']
    for user in aws_users:
        try:
            matched_jobs = send_daily_job_alerts(dynamodb_web_service, user, html_email)
            print(matched_jobs)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()
