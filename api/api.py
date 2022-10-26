import time
from flask import Flask, request, jsonify
import sys

sys.path.insert(1, './model/src')
from generate_translations import translate


app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

@app.route('/time')
def get_current_time():
    return {'time': time.time()}


@app.route('/translate', methods=['POST'])
def json_example():
    request_data = request.get_json()
    print(request_data)
    try:
        translations = translate(request_data['source_sentence'].lower())
        print("TRANSLATIONS:", translations)
        return jsonify(translations)
    except:
        error = {"error": "An error occurred translating sentences :("}
        return jsonify(error)  
    
    