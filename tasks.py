from config import create_app  # -Line 1
from celery import shared_task
from time import sleep
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import json


flask_app = create_app()
celery_app = flask_app.extensions["celery"]
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


@shared_task(ignore_results=False)
def generate_text_embeddings(text: str) -> list[float]:
    return model.encode(text).tolist()


@shared_task(ignore_results=False)
def populate_books_data(connection_string: str) -> str:
     collections = ["authors", "users", "reviews", "issueDetails", "books"]
     database = "library"
     db = MongoClient(connection_string)[database]
     for collection in collections:
         with open(f"{collection}.json") as f:
                collection_data = json.load(f)
                db[collection].insert_many(collection_data)
                db[collection].create_index("_id")

     return "Data imported successfully"
     