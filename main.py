# pylint: disable=C0116, C0103, W0603
import json
import time
import random
import threading
import os
from flask import Flask, send_from_directory, jsonify, request, render_template_string

app = Flask(__name__)

# Load image list from JSON file
def getSubmissions():
    try:
        with open("submissions.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

INTERVAL = 30  # seconds between image switches
LAST_SWITCH = int(time.time())
index = 0

from flask import Flask, render_template_string

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
@app.errorhandler(404)
def not_found(_):
    return render_template_string('''
        <h1>404 - Not Found</h1>
        <img src="https://http.cat/404" alt="404 Not Found">
    '''), 404
@app.errorhandler(405)
def method_not_allowed(_):
    return render_template_string('''
        <h1>405 - Method Not Allowed</h1>
        <img src="https://httpcats.com/405.jpg" alt="Method Not Allowed">
    '''), 405
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
    secs = updateTimer()
    return jsonify({
        "index": index,
        "url": getSubmissions()[index],
        "seconds_remaining": secs
    })
@app.route("/submit/img", methods=["POST"])
def submitImg():
    data = request.json
    url = data.get("url")
    with open("submissions.json", "r", encoding="utf-8") as f:
        images = json.load(f)
    if url in images:
        return jsonify("Not submitted: Link already in submission list")
    #TODO: check whether link is volatile and move to Catbox
    with open("submissions.json", "w", encoding="utf-8") as f:
        images.append(url)
        f.write(json.dumps(images))
        return jsonify(f"Link submitted successfully!\n{len(images)} submissions so far.")

def updateTimer():
    now = int(time.time())
    seconds_remaining = INTERVAL + LAST_SWITCH - now
    if seconds_remaining <= 0:
        pickNewImg()
    return seconds_remaining

@app.route("/report-image", methods=["POST"])
def report_image():
    data = request.json
    url = data.get("url")
    valid = data.get("valid")
    if not valid:
        removeBroken(url)
    return jsonify({"status": "received"})

def removeBroken(url):
    with open("submissions.json", "r", encoding="utf-8") as f:
        images = json.load(f)
    if url in images:
        images.remove(url)
        with open("submissions.json", "w", encoding="utf-8") as f:
            json.dump(images, f)
        print(f"Removed broken image: {url}")
    pickNewImg()

def pickNewImg():
    global index, LAST_SWITCH
    LAST_SWITCH = int(time.time())
    length = len(getSubmissions())
    if length <= 1:
        index = 0
        return
    index += random.randint(1, length-1)
    index %= length
    #print(f"Switching to image {index}")


def tickThread():
    while True:
        time.sleep(1)
        updateTimer()
stop_flag = threading.Event()
if __name__ == "__main__":
    pickNewImg()  # Initialize with a random image
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true": #pylint: disable=E1101
        threading.Thread(target=tickThread, daemon=True).start()
    else: print("GOTCHA!")
    app.run(host="0.0.0.0", port=8008, debug=True)
    #async: every second, call update timer
