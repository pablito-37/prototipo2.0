from flask import Flask, request, jsonify
from flask_cors import CORS  # Importa la extensión CORS
from pymongo import MongoClient
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForQuestionAnswering, pipeline
import nltk
# nltk.download('punkt')
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer
import string

app = Flask(__name__)
CORS(app) 

stemmer = SnowballStemmer("spanish")

def tokenizar_y_stemming(texto, tokenizer):
    tokens = tokenizer.tokenize(tokenizer.decode(tokenizer.encode(texto)))
    tokens_stemmed = [stemmer.stem(token) for token in tokens]
    return tokens_stemmed


def normalizar_texto(texto):
    print("Texto original:", texto)
    texto = texto.lower()
    texto = texto.translate(str.maketrans("", "", string.punctuation))
    print("Texto normalizado:", texto)
    return texto


# Conectar a la base de datos MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client["Prueba"]
contextos = db["contextos"]
calificaciones = db["calificaciones"]

# Cargar el modelo y el tokenizador
the_model = 'mrm8488/distill-bert-base-spanish-wwm-cased-finetuned-spa-squad2-es'
tokenizer = AutoTokenizer.from_pretrained(the_model, do_lower_case=False)
model = AutoModelForQuestionAnswering.from_pretrained(the_model)

# Crear pipeline de contexto y respuesta
nlp = pipeline('question-answering', model=model, tokenizer=tokenizer)


def encontrar_contexto_relacionado(pregunta, coleccion_preguntas, tokenizer):
    print("Texto original antes de normalizar:", pregunta)
    palabras_clave = tokenizar_y_stemming(pregunta, tokenizer)
    print("Texto original después de normalizar:", " ".join(palabras_clave))
    documentos_relacionados = coleccion_preguntas.find({"contexto": {"$regex": "|".join(palabras_clave)}})
    documentos_ordenados = sorted(documentos_relacionados, key=lambda x: len(set(palabras_clave) & set(x["contexto"].lower().split())), reverse=True)

    return documentos_ordenados[0] if documentos_ordenados else None


def calcular_actualizar_promedio_calificaciones(contexto_id, respuesta, calificacion, coleccion_calificaciones):
    respuesta_calificacion = coleccion_calificaciones.find_one({"id_contexto": contexto_id, "respuesta": respuesta})

    if respuesta_calificacion:
        promedio_anterior = respuesta_calificacion["promedio"]
        cantidad_anterior = respuesta_calificacion["cantidad"]

        nuevo_promedio = (promedio_anterior * cantidad_anterior + calificacion) / (cantidad_anterior + 1)
        nueva_cantidad = cantidad_anterior + 1

        coleccion_calificaciones.update_one(
            {"id_contexto": contexto_id, "respuesta": respuesta},
            {"$set": {"fecha": datetime.now(), "promedio": nuevo_promedio, "cantidad": nueva_cantidad}}
        )

        return nuevo_promedio, nueva_cantidad

    else:
        coleccion_calificaciones.insert_one({
            "id_contexto": contexto_id,
            "respuesta": respuesta,
            "fecha": datetime.now(),
            "promedio": calificacion,
            "cantidad": 1
        })

        return calificacion, 1

# Función para obtener la respuesta del modelo de pregunta y respuesta
def obtener_respuesta(pregunta, contexto):
    print("Pregunta:", pregunta)
    print("Contexto:", contexto)
    # Utiliza el pipeline de transformers
    salida = nlp({'question': pregunta, 'context': contexto})

    # Verificar si la confianza de la respuesta es suficiente
    confianza_minima = 0.1
    if salida['score'] >= confianza_minima and len(salida['answer'].split()) >= 3:
        return salida['answer']
    else:
        return "No tengo conocimientos sobre el tema."

# Ruta para manejar la solicitud de pregunta y obtener respuesta
@app.route('/pregunta_respuesta', methods=['POST'])
def pregunta_respuesta():
    data = request.json

    pregunta = data.get('pregunta')
    calificacion = data.get('calificacion')  # Puede ser None si no se proporciona
    
    contexto_relacionado = encontrar_contexto_relacionado(pregunta, contextos, tokenizer)

    
    if contexto_relacionado:
        respuesta = obtener_respuesta(pregunta, contexto_relacionado["contexto"])
        promedio, cantidad_calificaciones = None, None

        if calificacion is not None:
            promedio, cantidad_calificaciones = calcular_actualizar_promedio_calificaciones(contexto_relacionado["_id"], respuesta, calificacion, calificaciones)
        print(respuesta)

        return jsonify({
            'respuesta': respuesta,
            'promedio': promedio,
            'cantidad_calificaciones': cantidad_calificaciones
        })
    
    else:
        return jsonify({'error': 'No se encontró un contexto relacionado en la base de datos.'}), 404

if __name__ == '__main__':
    app.run(debug=True)
