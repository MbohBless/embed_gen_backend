from tasks import generate_text_embeddings, flask_app, populate_books_data
from celery.result import AsyncResult
from flask import request, jsonify,render_template
from pymongo import MongoClient
import json
from datetime import datetime
from bson import ObjectId
import logging
logging.basicConfig(level=logging.DEBUG)

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)
    
@flask_app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@flask_app.route("/api/embeddings", methods=["GET"])
def embed_test() -> dict[str, object]:
    try:
        # get the json data from the request
        data = request.get_json()
        text = data["text"]
        task = generate_text_embeddings(text)

        # Wait for the result with a timeout
        result = task
        return jsonify({
            "status": "success",
            "embedding": result
        })
    except TimeoutError:
        return jsonify({
            "status": "error",
            "message": "Task timed out. Please try again later."
        }), 504  # HTTP status code 504 Gateway Timeout
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500  # HTTP status code 500 Internal Server Error


@flask_app.route("/api/import-data", methods=["POST"])
def import_data():
    try:
        data = request.get_json()
        logging.info(data)
        connection_string = data["connectionString"]
        if not connection_string:
            return jsonify({
                "status": "error",
                "message": "Connection string is required"
            }), 400
        task = populate_books_data.delay(connection_string)
        return jsonify({
            "status": "success",
            "message": "Import in progress"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@flask_app.route("/api/save-data", methods=["GET"])
def save_data():
    try:
        collections = ["authors", "users", "reviews", "issueDetails"]
        connection_string = "Place your connection string here"
        if not connection_string:
            return jsonify({
                "status": "error",
                "message": "Connection string is required"
            }), 400
        database = "library"
        base_collection = "books"
        db = MongoClient(connection_string)[database]
        # getting all the data from the book collection
        data = list(db[base_collection].find())
        formatted_data = []
        # changing the emneddings dimensions from 1536 to 384 from open source model
        for item in data:
            text = item["longTitle"]+"\n\n"+item["synopsis"]
            formatted_data.append({
                **item,
                "embeddings": generate_text_embeddings(text)
            })
        with open("books.json", "w") as f:
            json.dump(formatted_data, f, indent=4,cls=CustomJSONEncoder)
        for collection in collections:
            collection_data = list(db[collection].find())
            with open(f"{collection}.json", "w") as f:
                json.dump(collection_data, f, indent=4,cls=CustomJSONEncoder)
        return jsonify({
            "status": "success",
            "message": "Data saved successfully"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    flask_app.run(debug=False)