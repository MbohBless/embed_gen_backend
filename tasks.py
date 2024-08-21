from config import create_app #-Line 1
from celery import shared_task 
from time import sleep
from sentence_transformers import SentenceTransformer


flask_app = create_app() 
celery_app = flask_app.extensions["celery"]
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

@shared_task(ignore_results=False)
def generate_text_embeddings(text:str)->list[float]:
    return model.encode(text).tolist()
    