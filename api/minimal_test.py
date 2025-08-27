from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/minimal', methods=['GET'])
def minimal():
    return jsonify({
        'message': 'Minimal test working!',
        'status': 'success'
    })

handler = app
