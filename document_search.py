from dataclasses import dataclass
from datetime import datetime
from dateutil import parser
from typing import List, Optional

from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class Document(BaseModel):
    """job"""

    id: str
    title: Optional[str]
    url: Optional[str]
    posted_date: Optional[str]
    category: Optional[str]
    organization: Optional[str]
    location: Optional[str]
    source: Optional[str]
    type: Optional[str]

    @property
    def full_text(self):
        return " ".join(
            [self.title, self.type, self.location, self.organization]
        )


class DocumentSearch(TfidfVectorizer):
    def __init__(self, documents: List):
        self.documents = documents
        super(DocumentSearch, self).__init__(stop_words="english")

    def search(self, query):
        """
        Search; this will return documents that contain words from the query,
        and rank them
        Parameters:
          - query: the query string

        """
        results = []
        try:
            vec_query = self.fit_transform([query]).toarray()
            for idx, document in enumerate(self.documents):
                doc = document.full_text
                vec_document = self.transform([doc]).toarray()
                similarity = cosine_similarity(vec_query, vec_document)
                if similarity >= 0.80:
                    job = {"id": document.id, "title": document.title, "url": document.url, "source": document.source,
                           "organization": document.organization, "posted_date": document.posted_date,
                           "type": document.type, "category": document.category, "days_since_posted": 1}
                    results.append(job)
                    # if document.source == "Somalijobs":
                    #     if document.posted_date == "Today":
                    #         job["days_since_posted"] = 0
                    #     elif document.posted_date == "Yesterday":
                    #         job["days_since_posted"] = 1
                    #     else:
                    #         job["days_since_posted"] = (
                    #             datetime.now().date()
                    #             - parser.parse(document.posted_date).date()
                    #         ).days
                    #
                    # else:
                    #     job["days_since_posted"] = (
                    #         datetime.now().date()
                    #         - datetime.fromisoformat(document.posted_date).date()
                    #     ).days
                    # if job["days_since_posted"] <= 3 and job[
                    #     "category"
                    # ].strip() not in ["Tender/Bid/RFQ/RFP", "Course", ""]:

            return results
            # sorted(results, key=lambda item: item["days_since_posted"], reverse=False)
        except Exception as e:
            print(e)
            raise ValueError("not a valid sentence")
