# Python 3.12.6

# Flask para conectar con Python 2.7.16 (cliente)
from flask import Flask, jsonify, request

# Librerias deepface/utilidades
from deepface import DeepFace
import numpy as np
import tempfile
import os

import cv2

# Librerias chatbot
from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Librerias Traductor
from transformers import MarianMTModel, MarianTokenizer

# Servidor Flask
app = Flask(__name__)

# Cargar modelo de chatbot
ESP = False     # false = ingles traducido

if ESP:
    # Español
    # No recomendable ya que no maneja bien conversaciones
    tokenizer = AutoTokenizer.from_pretrained("ostorc/Conversational_Spanish_GPT")
    model = AutoModelForCausalLM.from_pretrained("ostorc/Conversational_Spanish_GPT")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)
else:
    # Ingles
    # Maneja bien conversaciones en inglés
    tokenizer = BlenderbotTokenizer.from_pretrained("facebook/blenderbot-400M-distill")
    model = BlenderbotForConditionalGeneration.from_pretrained("facebook/blenderbot-400M-distill")
    # Modelos para la traducción
    tgt_es_en = "Helsinki-NLP/opus-mt-es-en"
    tgt_en_es = "Helsinki-NLP/opus-mt-en-es"
    # español a ingles
    tok_es_en = MarianTokenizer.from_pretrained(tgt_es_en)
    mod_es_en = MarianMTModel.from_pretrained(tgt_es_en)
    # ingles a español
    tok_en_es = MarianTokenizer.from_pretrained(tgt_en_es)
    mod_en_es = MarianMTModel.from_pretrained(tgt_en_es)

# Traducir segun el modelo (entre ingles y español)
def traducir(text, tokenizer, model):
    # usa pt: pytorch / deeplearning
    inputs = tokenizer([text], return_tensors="pt", padding=True)   # tokenizar para que el modelo entienda
    outputs = model.generate(**inputs)  # aliementar modelo
    return tokenizer.batch_decode(outputs, skip_special_tokens=True)[0] # texto traducido / string

# 1ra parte - deteccion de emociones

# solicitud POST - ruta: /emociones
@app.route('/emociones', methods=['POST'])
def emociones():
    # existe imagen?
        
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        exit()

    ret, frame = cap.read()

    img_path = "emocion.jpg"
    if ret:
        cv2.imwrite(img_path, frame)

    cap.release()

    # Deteccion cara de imagen - Analisis de emociones
    resultado = DeepFace.analyze(img_path=img_path, actions=['emotion'], enforce_detection=False)
    
#    os.remove(img_path) # Eliminar archivo temporal
    emocionD = resultado[0]['dominant_emotion'] # Emocion dominante
    emocion_es = traducir(emocionD, tok_en_es, mod_en_es)   # Traducir
    saludo = f"Hola, veo que te sientes {emocion_es}. ¿Qué ocurrió?"    #saludo de NAO
    return jsonify({"saludo": saludo})  # Mandar saludo a cliente


# 2da parte - conversar con el usuario

# solicitud POST - ruta: /conversar
@app.route('/conversar', methods=['POST'])
def conversacion():
    data = request.json # Cargar mensaje usuario usando Request (libreria)
    # existe mensaje?
    if 'mensaje_usuario' not in data:
        return jsonify({"error": "No hay mensaje del usuario"}), 400

    # guardar mensaje
    entrada = data['mensaje_usuario']

    # Diferenciar entre cual modelo se usa
    if ESP:
        # Español
        ent = entrada + tokenizer.eos_token # mensaje + end of sequence
        enc = tokenizer.encode(ent, return_tensors="pt").to(device) # tokenizar, usa pytorch, guarda datos en el equipo para optimizar
        salida = model.generate(enc, max_length=200, pad_token_id=tokenizer.eos_token_id)
        # genera respuesta, menos de 200 tokens
        reply_es = tokenizer.decode(salida[0], skip_special_tokens=True).strip()
        # respuesta español, sin tokens especiales, sin espacios adicionals
    else:
        # Ingles + Traduccion
        entrada_eng = traducir(entrada, tok_es_en, mod_es_en)   # mensaje de esp a en
        inputs = tokenizer([entrada_eng], return_tensors="pt")  # tokenizar, usa pytorch
        reply_ids = model.generate(**inputs)    # alimentar modelo
        reply_eng = tokenizer.batch_decode(reply_ids, skip_special_tokens=True)[0]  # generar respuesta
        reply_es = traducir(reply_eng, tok_en_es, mod_en_es)    # respuesta de en a esp

    return jsonify({"respuesta_chatbot": reply_es})

# conexion Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)