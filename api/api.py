import time
from model.src.generate_translations import translate
from flask import Flask, request

app = Flask(__name__)

@app.route('/time')
def get_current_time():
    return {'time': time.time()}


@app.route('/translate', methods=['POST'])
def json_example():
    request_data = request.get_json()
    print(request_data)
    try:
        translate(request_data['source_sentence'])
        return {"translation": "OK"}
    except:
        return "An error occurred translating sentences :("    
    
    