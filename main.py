import os
import tempfile
import requests
import random
import dotenv

from allrecipes import AllRecipes
from flask import Flask, render_template, request, redirect, url_for, jsonify
from io import BytesIO

import google.generativeai as genai
import json_repair

from googleapiclient.discovery import build
from PIL import Image

app = Flask(__name__)
all_recipes = AllRecipes()

VISION_PROMPT = "Analyse the image and return ONLY the name of the dish."


@app.route("/")
def main():
    articles = all_recipes.homepage()

    random.shuffle(articles)

    return render_template("home.html", articles=articles)


@app.route("/search")
def search():
    query = request.args.get("query").strip()

    # Redirect to homepage if query not found
    if not query:
        return redirect(url_for('main'))

    search_results = all_recipes.search(query)

    return render_template(
        "search.html",
        query=query,
        search_results=search_results)


@app.route("/image", methods=["GET", "POST"])
def image():
    image_url = request.form.get('image_url')
    image_file = request.files.get('image')

    if not image_url and not image_file:
        if request.method == 'GET':
            return redirect(url_for('main'))

        return jsonify({"error": "No image URL or file provided"}), 400

    try:
        if image_url:
            response = requests.get(image_url)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
        else:
            file_path = os.path.join("static", "uploads", image_file.filename)
            image_file.save(file_path)
            image_url = file_path
            image = Image.open(file_path)
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    genai.configure(api_key=GEMINI_API_KEY)

    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    response = model.generate_content([VISION_PROMPT, image])

    dish_name = response.text.strip()
    youtube_videos = get_youtube_videos(dish_name + " recipe")

    print(image_url)
    return render_template('recipe.html', youtube_videos=youtube_videos, recipe=dish_name, image_url=image_url)


def get_youtube_videos(prompt, max_results=10) -> list[str]:
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    results = []

    request = youtube.search().list(
        q=prompt,
        part='snippet',
        maxResults=max_results
    )

    responses = request.execute()

    for item in responses['items']:
        if item['id']['kind'] == 'youtube#video':
            video_id = item['id']['videoId']
            results.append(video_id)

    return results


if __name__ == '__main__':
    # Load environment variables from .env
    dotenv.load_dotenv()

    GEMINI_API_KEY = os.environ["GOOGLE_API_KEY"]
    YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]

    # Auto reload for changes to project
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    # Run on all interfaces on port 8080 in debug mode
    app.run(debug=True, host='0.0.0.0', port=8080)
