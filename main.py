from serpapi import GoogleSearch
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import time
import json
import csv
import os


load_dotenv()


def get_reviews(place_id):
    all_reviews = []
    next_page_token = ""
    count = 0
    limit_count = 2
    while True:
        count += 1
        params = {
            "engine": "google_maps_reviews",
            "place_id": place_id,
            "api_key": os.getenv("SERP_API_KEY")
        }
        if next_page_token != "":
            params["next_page_token"] = next_page_token
        search = GoogleSearch(params)
        results = search.get_dict()
        if not "reviews" in results:
            return ("Can't find reviews ...")
        all_reviews = all_reviews + results["reviews"]
        if "serpapi_pagination" in results and "next_page_token" in results["serpapi_pagination"]:
            next_page_token = results["serpapi_pagination"]["next_page_token"]
        else:
            break
        if count == limit_count:
            break
    return all_reviews


def rest_reviews(reviews):
    all_keys = set()

    def get_all_keys(json_data, base_key):
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                if isinstance(value, dict):
                    get_all_keys(value, f'{base_key}{key}__')
                else:
                    all_keys.add(f'{base_key}{key}')
        elif isinstance(json_data, list):
            for item in json_data:
                get_all_keys(item, base_key)

    get_all_keys(reviews, '')
    all_keys = list(all_keys)
    all_keys.sort()

    def get_value_from_key(json_data, key):
        try:
            keys = key.split("__")
            result = json_data
            for k in keys:
                result = result[k]
            # if isinstance(result, list):
            #     result = '\n'.join(result)
            return result
        except:
            return None

    rested_reviews = []
    for review in reviews:
        cloned_review = {}
        for key in all_keys:
            cloned_review[key] = get_value_from_key(review, key)
        rested_reviews.append(cloned_review)

    return rested_reviews


public_folder = 'public'
app = Flask(__name__, static_folder=public_folder, static_url_path='/public')
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/review/<place_id>', methods=['GET'])
def get_reviews_router(place_id):
    reviews = get_reviews(place_id)
    if isinstance(reviews, str):
        return jsonify({"error": "Can't find reviews ..."}), 400
    rested_reviews = rest_reviews(reviews)
    if reviews != False and len(reviews) != 0:
        current = time.time()
        json_file = f'{public_folder}/reviews_{place_id}_{current}.json'
        rested_json_file = f'{public_folder}/reviews_rested_{place_id}_{current}.json'
        csv_file = f'{public_folder}/reviews_{place_id}_{current}.csv'
        with open(json_file, 'w', encoding='utf-8') as file:
            json.dump(reviews, file, indent=2)
        with open(rested_json_file, 'w', encoding='utf-8') as file:
            json.dump(rested_reviews, file, indent=2)
        with open(csv_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(rested_reviews[0].keys())
            for item in rested_reviews:
                writer.writerow(item.values())
        return jsonify({"csv_file": csv_file, "json_file": json_file}), 200
    else:
        return jsonify({"error": "Can't find reviews ..."}), 400


if __name__ == '__main__':
    app.run(debug=False, port=3000, host='0.0.0.0')
