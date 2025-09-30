from flask import Flask, request, jsonify
import requests
import json
from robot import Robot
import os
import pika
import threading as th

def handle(ch, method, props, body):
    print("Received response", body)
    message_dict = json.loads(body.decode('utf-8'))

    try:
        update_data={
            'name': props.correlation_id,
            'message': body.decode('utf-8')
        }
        print("Update data:", update_data)
        response = requests.post(f"{back_api}/update", json=update_data)

        if response.status_code == 200:
            print(f"Update notification sent successfully: {response.json()}")
        else:
            print(f"Failed to send update notification: {response.status_code}")
            
    except Exception as e:
        print(f"Error sending update notification: {str(e)}")

app = Flask(__name__)
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='rpc_queue')
result = channel.queue_declare(queue='', exclusive=True)
callback_queue = result.method.queue
channel.basic_consume(callback_queue,handle,auto_ack=True)
back_api=""


@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "ok", "message": "Flask server is running"}), 200

@app.route('/create', methods=['POST'])
def create_model():
    """Endpoint pour créer et entraîner un nouveau modèle"""
    try:
        # Récupération des données JSON de la requête
        data = request.get_json()
        correlation_id = str(data.get('username'))
        data['req']='Create'
        print("Sending data to worker:", data)
        channel.basic_publish(exchange='',
                              routing_key='rpc_queue',
                              properties=pika.BasicProperties(
                                reply_to=callback_queue,
                                correlation_id=correlation_id,
                              ),
                              body=json.dumps(data))
        

        th.Thread(target=channel.start_consuming).start()


        return jsonify({"status": "success", "message": "Model is being created"}), 201
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/predict', methods=['POST'])
def make_prediction():
    """Endpoint pour faire des prédictions avec un modèle existant"""
    try:
        # Récupération des données JSON de la requête
        data = request.get_json()
        model_name = data.get('name')
        data['req']='Predict'
        # Charger le robot depuis le fichier .rbt
        robot = Robot(train=False)
        robot.read_rbt(model_name)
        
        # Générer des prédictions
        result = robot.generate()
        
        # Conversion du résultat PyTorch en liste pour la sérialisation JSON
        result_list = result.tolist() if hasattr(result, 'tolist') else result
        
        return jsonify({"status": "success", "values": result_list}), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/models', methods=['GET'])
def list_models():
    """Endpoint pour lister les modèles disponibles"""
    try:
        models = []
        # Parcourir le répertoire robots pour lister les fichiers .rbt
        for file in os.listdir('./robots'):
            if file.endswith('.rbt'):
                models.append(file[:-4])  # Enlever l'extension .rbt
        
        return jsonify({"status": "success", "models": models}), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/model/<name>', methods=['GET'])
def load_model_info(name):
    """Endpoint pour charger les informations d'un modèle spécifique"""
    try:
        robot = Robot(train=False)
        robot.read_rbt(name)
        
        model_info = {
            "name": name,
            "stock": robot.stock,
            "inputFrequency": robot.inputFrequency,
            "outputFrequency": robot.outputFrequency,
            "inputPeriod": robot.inputPeriod,
            "outputPeriod": robot.outputPeriod,
            "features": robot.features
        }
        
        return jsonify({"status": "success", "model_info": model_info}), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Configuration pour le déploiement dans un environnement Ubuntu
    app.run(host='0.0.0.0', port=5000, debug=True)