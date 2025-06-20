# -*- coding: utf-8 -*-
# Python 2.7.16 para usar con NAO
import json
import os
import time
import requests # libreria para comunicarse con python 3.12.6
from naoqi import ALProxy # control del NAO

# Configurar NAO
IP="192.168.108.36"  # IP NAO
PROXY = 9559   # PORT DEL NAO (cambiar)

tts = ALProxy("ALTextToSpeech", IP, PROXY)
postura = ALProxy("ALRobotPosture", IP, PROXY)
motion = ALProxy("ALMotion", IP, PROXY)

mem = ALProxy("ALMemory", IP, PROXY)


# 1ra parte - deteccion de emociones

def detectar_emocion():
    # 192.168.0.15 es la direccion IPV4 - se halla con ipconfig en terminal
    url = "http://192.168.108.92:5000/emociones"  # ruta Flask

    try:
        # solicitud POST - 'imagen' (parametro que espera el server)
        r = requests.post(url)
        # la respuesta de server se convierte a JSON
        data = json.loads(r.text)
        # extraer el texto de saludo - Emocion detectada
        return data.get("saludo", "")
    except Exception as e:
        print("Error:", str(e)) # error
        return ""


# 2da parte - conversacion robot - usuario

def conversacion(mensaje_usuario):
    url = "http://192.168.108.92:5000/conversar"  # ruta Flask
    # solicitud POST - 'mensaje_usuario' (parametro)
    r = requests.post(url, json={"mensaje_usuario": mensaje_usuario})
    # se envia el mensaje del usuario y retorna la respuesta del chatbot
    return json.loads(r.text).get("respuesta_chatbot", "")

# Esperar a toque en la cabeza
def esperando_accion():
    
    while True:
        sensor = mem.getData("FrontTactilTouched")  # Sensor táctil frontal
        
        if sensor == 1.0:
            print("Sensor activado")
            tts.say("Voy a tomar una foto.")

            # Analizar emoción
            saludo = detectar_emocion()
            if saludo:
                tts.say(saludo.encode("utf-8"))
                print("SALUDO:", saludo)
                
                while True:
                    respuesta_usuario = raw_input("ingrese su respuesta: ")
                    # respuesta_usuario = CODIGO PARA ESCUCHAR AL USUARIO

                    if respuesta_usuario.lower() == "detener":
                        tts.say("Conversación terminada.")
                        print("Fin de la conversación.")
                        break
                    respuesta_bot = conversacion(respuesta_usuario)
                    print("NAO: ", respuesta_bot)
                    tts.say(respuesta_bot.encode("utf-8"))

            print("Esperando próximo toque...")
            time.sleep(2)   # esperar antes de proximo toque

# Iniciar ejecucion
esperando_accion()