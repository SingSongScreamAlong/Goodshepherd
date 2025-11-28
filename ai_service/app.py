from flask import Flask, request, jsonify
from transformers import pipeline

app = Flask(__name__)

# Load threat detection model (using sentiment as proxy for threat level)
threat_pipeline = pipeline("text-classification", model="cardiffnlp/twitter-roberta-base-sentiment-latest")

@app.route('/detect_threat', methods=['POST'])
def detect_threat():
    """Detect threat level in text using sentiment analysis as proxy"""
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    result = threat_pipeline(text)
    
    # Map sentiment labels to threat levels
    # LABEL_0: Negative (potentially threatening)
    # LABEL_1: Neutral
    # LABEL_2: Positive
    label = result[0]['label']
    confidence = result[0]['score']
    
    if label == 'LABEL_0':
        threat_level = 'high'
    elif label == 'LABEL_1':
        threat_level = 'medium'
    else:
        threat_level = 'low'
    
    return jsonify({
        'threat_level': threat_level,
        'confidence': confidence,
        'original_label': label
    })

@app.route('/translate', methods=['POST'])
def translate_text():
    """Translate text between languages"""
    data = request.get_json()
    text = data.get('text', '')
    source_lang = data.get('source_lang', 'en')
    target_lang = data.get('target_lang', 'fr')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        model_name = f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"
        translator = pipeline("translation", model=model_name)
        result = translator(text)
        return jsonify({
            'translated_text': result[0]['translation_text'],
            'source_lang': source_lang,
            'target_lang': target_lang
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/score_severity', methods=['POST'])
def score_severity():
    """Score severity based on threat keywords (MVP implementation)"""
    data = request.get_json()
    text = data.get('text', '').lower()
    
    # Define threat keywords
    threat_words = [
        'crisis', 'attack', 'violence', 'emergency', 'threat', 'danger',
        'conflict', 'war', 'terrorism', 'unrest', 'protest', 'riot'
    ]
    
    # Count matches
    threat_count = sum(1 for word in threat_words if word in text)
    
    # Determine severity
    if threat_count >= 3:
        severity = 'high'
    elif threat_count >= 1:
        severity = 'medium'
    else:
        severity = 'low'
    
    return jsonify({
        'severity': severity,
        'threat_count': threat_count,
        'detected_words': [word for word in threat_words if word in text]
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print("Starting AI Service on port 5000...")
    app.run(debug=True, port=5000)
