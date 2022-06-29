import os
import re
from datetime import datetime
from dateutil import parser

import boto3
from boto3.dynamodb.conditions import Attr
from itsdangerous import BadData, URLSafeSerializer

from document_search import Document, DocumentSearch
from emailing import Email


def get_new_jobs_posted_recently(jobs):
    jobs_posted_recently = []
    for job in jobs:
        if job["source"] == "Somali jobs":
            if job["posted_date"] == "Today":
                job["days_since_posted"] = 0
            elif job["posted_date"] == "Yesterday":
                job["days_since_posted"] = 1
            else:
                job["days_since_posted"] = (
                    datetime.now().date() - parser.parse(job["posted_date"]).date()
                ).days

        else:
            job["days_since_posted"] = (
                datetime.now().date()
                - datetime.fromisoformat(job["posted_date"]).date()
            ).days
        if job["days_since_posted"] <= 3:
            jobs_posted_recently.append(job)
    return jobs_posted_recently


def get_relevant_jobs(jobs, user):
    documents = []
    relevant_jobs = []
    for job in jobs:
        documents.append(Document(**job))
    if user["is_active"] and user["job_description"] is not None:
        try:
            document_search = DocumentSearch(documents)
            if len(user["job_description"].split(",")) > 1:
                for item in user["job_description"].split(","):
                    if len(item.strip()) >= 3:
                        relevant_jobs.extend(document_search.search(item.strip()))
                return relevant_jobs
            query = re.sub("[^A-Za-z0-9]+", " ", user["job_description"])
            if len(query) > 1:
                relevant_jobs.extend(document_search.search(query))
                return relevant_jobs
        except Exception as e:
            print(e)
    return relevant_jobs


def get_jobs_from_followed_orgs(jobs, user):
    jobs_posted_by_orgs_followed = []
    if user["is_active"] and user.get("follows", None):
        for org in user["follows"]:
            for job in jobs:
                if job["organization"] == org:
                    _job = {
                        "id": job["id"],
                        "title": job["title"],
                        "url": job["url"],
                        "source": job["source"],
                        "organization": job["organization"],
                        "posted_date": job["posted_date"],
                        "type": job["type"],
                        "category": job["category"],
                    }
                    if _job["source"] == "Somali jobs":
                        if _job["posted_date"] == "Today":
                            _job["days_since_posted"] = 0
                        elif _job["posted_date"] == "Yesterday":
                            _job["days_since_posted"] = 1
                        else:
                            _job["days_since_posted"] = (
                                datetime.now().date()
                                - parser.parse(_job["posted_date"]).date()
                            ).days

                    else:
                        _job["days_since_posted"] = (
                            datetime.now().date()
                            - datetime.fromisoformat(_job["posted_date"]).date()
                        ).days
                    if _job["days_since_posted"] <= 3 and _job[
                        "category"
                    ].strip() not in ["Tender/Bid/RFQ/RFP", "Course", ""]:
                        jobs_posted_by_orgs_followed.append(_job)
        return jobs_posted_by_orgs_followed
    return []


def send_daily_job_alerts(
    sent_job_alerts,
    user,
    matched_jobs,
    email_template,
    secret_key,
    sender_email,
    sender_password,
):
    sent_job_urls = [] = []
    for job_alert in sent_job_alerts:
        if job_alert["user_id"] == user["id"]:
            sent_job_urls.append(job_alert["job_url"])

    user_relevant_jobs = matched_jobs
    if len(user_relevant_jobs) > 0:
        rows = ""
        count_new_jobs = 0
        first_job_title = ""
        for item in user_relevant_jobs:
            if item["url"] not in sent_job_urls:
                count_new_jobs += 1
                first_job_title = item["title"]
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
                    "<a style={text-decoration:none} href="
                    + item["url"]
                    + ">"
                    + str(item["title"])
                    + "</a>"
                    "</td></tr>"
                )
                rows = rows + "<tr><td>" + str(item["organization"]) + "</td></tr>"
                rows = rows + "<tr><td>" + days_since_posted + "</td></tr>"
                rows = rows + "<br>"
        if rows:
            try:
                s = URLSafeSerializer(secret_key, salt="unsubscribe")
                e = URLSafeSerializer(secret_key, salt="edit")
                unsubscribe_token = s.dumps(user["email"])
                edit_token = e.dumps(user["email"])
                unsubscribe_url = "http://www.diractly.com/unsubscribe/{}".format(
                    unsubscribe_token
                )
                edit_url = "http://www.diractly.com/edit/{}".format(edit_token)

                content = email_template.format(
                    jobs=rows,
                    unsubscribe_url=unsubscribe_url,
                    edit_url=edit_url,
                    title=count_new_jobs,
                    # saved_alert=user["job_description"],
                )
                email_title = (
                    "1 new " + first_job_title + " " + "job has been found for you"
                )
                if count_new_jobs > 1:
                    email_title = (
                        first_job_title
                        + " "
                        + "and"
                        + " "
                        + str(count_new_jobs - 1)
                        + " "
                        + "other new job(s) have been found for you "
                    )
                email = Email(sender_email, sender_password)
                email.send_message(content, email_title, user["email"])
            except Exception as e:
                print(e)
        else:
            print("No new job alerts sent")
    else:
        print("no new matches found")


def save_sent_alerts(sent_job_alerts, user, alerts):
    try:
        for item in alerts:
            sent_job_alerts.put_item(
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
