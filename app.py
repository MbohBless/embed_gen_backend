from tasks import generate_text_embeddings, flask_app
from celery.result import AsyncResult
from flask import request, jsonify


@flask_app.route("/embeddings", methods=["GET"])
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

if __name__ == "__main__":
    flask_app.run(debug=True)
