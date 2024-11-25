import yt_dlp
import os
import requests
import random
import dotenv
import speech_recognition as sr

from allrecipes import AllRecipes
from flask import Flask, render_template, request, redirect, url_for, jsonify
from io import BytesIO

import google.generativeai as genai
import json_repair

from PIL import Image

app = Flask(__name__)
all_recipes = AllRecipes()

VISION_PROMPT = """Analyse the image and return the following in JSON format:
{
"title": "Name of the dish",
"description": "Description of the dish, with a fun fact about it.",
"ingredients": [
"ingredient1",
"ingredient2"
]
}
"""


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
            uploaded_image_url = upload_image_to_freeimage(image, image_url=image_url)
        else:
            uploaded_image_url = upload_image_to_freeimage(image_file=image_file)
            image = Image.open(image_file)

    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    dish_information = get_dish_information(image)
    dish_name = dish_information['title']
    ingredients = dish_information['ingredients']
    description = dish_information['description']
    youtube_videos = get_youtube_videos(dish_name + " recipe")
    search_results = all_recipes.search(dish_name)

    return render_template(
        'recipe.html',
        youtube_videos=youtube_videos,
        recipe=dish_name,
        ingredients=ingredients,
        description=description,
        image_url=uploaded_image_url,
        search_results=search_results
    )

def upload_image_to_freeimage(image=None, image_url=None, image_file=None):
    api_key = os.environ.get('FREEIMAGE_API_KEY')
    url = "https://freeimage.host/api/1/upload"
    payload = {
        'key': api_key,
        'action': 'upload',
        'format': 'json'
    }

    if image_url:
        payload['source'] = image_url
    elif image_file:
        files = {'source': image_file}
    else:
        raise ValueError("No image source provided")

    response = requests.post(url, data=payload, files=files if image_file else None)
    response.raise_for_status()
    response_data = response.json()
    
    if response_data['status_code'] != 200:
        raise Exception(f"Error uploading image: {response_data}")

    return response_data['image']['url']

def get_dish_information(image: Image) -> dict:
    response = model.generate_content([VISION_PROMPT, image])

    dish_information = json_repair.loads(response.text.strip())

    if not (dish_information and dish_information.get('title') and dish_information.get(
            'description') and dish_information.get('ingredients')):
        return get_dish_information(image)

    return dish_information


def get_youtube_videos(prompt, max_results=10) -> list[str]:
    results = []

    ydl_opts = {
        'quiet': True,
        'default_search': 'ytsearch',  # Use YouTube search
        'max_downloads': max_results,  # Limit the number of results
        'extract_flat': 'in_playlist',  # Ensure only metadata is retrieved
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(
            f"ytsearch{max_results}:{prompt}",
            download=False)

        for entry in info['entries']:
            results.append(entry['id'])

    return results


if __name__ == '__main__':
    # Load environment variables from .env
    dotenv.load_dotenv()

    GEMINI_API_KEY = os.environ["GOOGLE_API_KEY"]

    # Suppress logging warnings
    os.environ["GRPC_VERBOSITY"] = "ERROR"
    os.environ["GLOG_minloglevel"] = "2"
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")

    # Auto reload for changes to project
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    # Run on all interfaces on port 8080 in debug mode
    app.run(debug=True, host='0.0.0.0', port=8080)

# def listen():
# Initialize recognizer
    # recognizer = sr.Recognizer()

    # Use a microphone as source
    # with sr.Microphone() as source:
    #     print("Please say something:")
    #     audio = recognizer.listen(source)

    #     try:
    #         # Recognize speech using Google Web Speech API
    #         text = recognizer.recognize_google(audio)
    #         return {"text":text,
    #                 "error": False,
    #         }
    #     #Error cases
    #     except sr.UnknownValueError:
    #         {
    #             "error": True,
    #             "message": "Let me know if I can help you with anything else"
    #         }
    #     except sr.RequestError as e:
    #         {
    #             "error" : True,
    #             "message": f"Could not request results; {e}"
    #         }
