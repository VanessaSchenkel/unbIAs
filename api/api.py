import time
from model.src.generate_translations import get_source_sentence
from flask import Flask, request

app = Flask(__name__)

@app.route('/time')
def get_current_time():
    return {'time': time.time()}


@app.route('/translate', methods=['POST'])
def json_example():
    request_data = request.get_json()
    print(request_data)
    get_source_sentence(request_data['source_sentence'] )
    return {"translation": "OK"}
    