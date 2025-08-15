# pylint: disable=C0116, C0103, W0603
import json
import time
import random
import threading
import os
from flask import Flask, send_from_directory, jsonify, request, render_template_string

app = Flask(__name__)

# Load image list from JSON file
def getSelections():
    try:
        with open("selections.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"img": [], "quote": []}

INTERVAL = 30  # seconds between image switches
LAST_SWITCH = int(time.time())

app = Flask(__name__)

@app.errorhandler(Exception)
def handle_error(e):
    # Get status code from the exception (default to 500 if not available)
    code = getattr(e, 'code', 500)

    # Only serve images for 4xx and 5xx errors
    if 400 <= code < 600:
        return render_template_string(f'''
            <h1>{code} - Error</h1>
            <img src="https://http.cat/{code}" alt="HTTP {code}">
        '''), code

    # For other errors, return the default
    return str(e), code
#get the favicon
@app.route("/favicon.ico")
def favicon():
    return send_from_directory(".", "favicon.ico")
@app.route("/")
def serve_index():
    print("new logon")
    return send_from_directory(".", "index.html")
@app.route("/submit")
def serve_submit():
    return send_from_directory(".", "submit.html")

@app.route("/current")
def current_image():
    selections = getSelections()
    secs = updateTimer()
    return jsonify({
        "img": selections["img"],
        "quote": selections["quote"],
        "seconds_remaining": secs
    })
@app.route("/submit/<category>", methods=["POST"])
def submit_generic(category):
    data = request.json
    value = data.get("value") or data.get("url")  # support both field names
    if not value:
        return jsonify({"error": "No value provided"}), 200
    try:
        with open("submissions.json", "r", encoding="utf-8") as f:
            submissions = json.load(f)
    except FileNotFoundError:
        submissions = {}
    # Ensure category exists in the JSON
    if category not in submissions or not isinstance(submissions[category], list):
        return jsonify({"error": f"Category '{category}' does not exist"}), 200
    # Prevent duplicates
    if value in submissions[category]:
        return jsonify(f"Not submitted: Already in '{category}' list"), 200
    # Append new value
    submissions[category].append(value)
    with open("submissions.json", "w", encoding="utf-8") as f:
        json.dump(submissions, f, ensure_ascii=False, indent=2)
    return jsonify(f"Submitted successfully to '{category}'!\n{len(submissions[category])} items so far.")

def updateTimer():
    now = int(time.time())
    seconds_remaining = INTERVAL + LAST_SWITCH - now +1 
    if seconds_remaining <= 1:
        selectAll()
    return seconds_remaining

@app.route("/report/<category>", methods=["POST"])
def report_image(category):
    data = request.json
    url = data.get("url")
    valid = data.get("valid")
    if not valid: #TODO: Verify on server that broken stuff is actually broken
        removeBroken(category, url)
    return jsonify({"status": "received"})

def removeBroken(category, url):
    with open("submissions.json", "r", encoding="utf-8") as f:
        images = json.load(f)[category]
    if url in images:
        images.remove(url)
        with open("submissions.json", "w", encoding="utf-8") as f:
            json.dump(images, f)
        print(f"Removed broken image: {url}")
    reroll(category, url)

#TODO: Overhaul this to building a selections.json from submissions.json
#      and seperate function replacing individual categories if broken
def selectAll():
    global LAST_SWITCH
    LAST_SWITCH = int(time.time())
    selections = getSelections()
    with open("submissions.json", "r", encoding="utf-8") as f:
        submissions = json.load(f)
        for category in submissions:
            #Select a random item from each category, but not the same one as last time
            new = None
            while (new is None or new == selections.get(category)) and len(submissions[category]) > 1:
                new = random.choice(submissions[category])
            selections[category] = new
    with open("selections.json", "w", encoding="utf-8") as f:
        json.dump(selections, f, ensure_ascii=False, indent=2)

def reroll(category, invalid):
    selections = dict()
    submissions = dict()
    with open("selections.json", "r", encoding="utf-8") as f:
        selections = json.load(f)
    with open("submissions.json", "r", encoding="utf-8") as f:
        submissions = json.load(f)
        #delete invalid item, then pick a new one
        submissions[category].remove(invalid)
        selections[category] = random.choice(submissions[category])
    #Save new lists
    with open("selections.json", "w", encoding="utf-8") as f:
        json.dump(selections, f, ensure_ascii=False, indent=2)
    with open("submissions.json", "w", encoding="utf-8") as f:
        json.dump(submissions, f, ensure_ascii=False, indent=2)

def tickThread():
    while True:
        time.sleep(1)
        updateTimer()
stop_flag = threading.Event()
if __name__ == "__main__":
    selectAll()  # Initialize with a random image
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true": #pylint: disable=E1101
        threading.Thread(target=tickThread, daemon=True).start()
    else: print("GOTCHA!")
    app.run(host="0.0.0.0", port=8008, debug=True)
    #async: every second, call update timer
