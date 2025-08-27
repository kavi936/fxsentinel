from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/stripe-webhook', methods=['POST'])
def stripe_webhook():
    """Minimal Stripe webhook handler"""
    return jsonify({'success': True, 'message': 'Webhook received'}), 200

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'healthy', 'webhook': 'working'})

handler = app
