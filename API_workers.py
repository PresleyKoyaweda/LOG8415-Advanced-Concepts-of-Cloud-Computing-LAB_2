from flask import Flask, jsonify, request
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import torch

# Initialiser l'application Flask
app = Flask(__name__)

# Charger le modèle et le tokenizer pré-entraînés DistilBERT
tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
model = DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased', num_labels=2)

# Définir une route pour exécuter le modèle
@app.route('/run_model', methods=['POST'])
def run_model():
    data = request.get_json()
    if 'text' not in data:
        return jsonify({"error": "Aucun texte fourni"}), 400

    input_text = data['text']
    inputs = tokenizer(input_text, return_tensors='pt', padding=True, truncation=True)
    outputs = model(**inputs)
    probabilities = torch.softmax(outputs.logits, dim=-1)
    probabilities_list = probabilities.tolist()[0]

    return jsonify({"input_text": input_text, "probabilities": probabilities_list})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # L'application écoute sur le port 5000
