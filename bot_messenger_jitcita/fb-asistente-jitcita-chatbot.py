import os
import sys, json, requests
from flask import Flask, request

try:
    import apiai
except ImportError:
    sys.path.append(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    )
    import apiai

app = Flask(__name__)

PAT = 'EAAHlEfzudzEBAD6b2nTAKIeKx6zZAmZAmGongVyVOMd1cFt7ytVS2t57r5yadQxofH5hM4K1wqWmubYr14rPvSQ5IkN8vDSu6RJd9NUKRbZBt9FCF9M7yWgUWiiUYPEpNxepAVnjMDf6JXKPVe4B2VzZBZBnw9rVCFJmjgOk8Dh37H9Iik5HW' # Token de Acceso a la Pagina Facebook

CLIENT_ACCESS_TOKEN = '8ad3602dab1c43f28002d398bacb7e7f' # Token de acceso al cliente del agente de jitcita bot

VERIFY_TOKEN = 'your_webhook_verification_token' #Token de verificacion de conexion entre el pat y el servidor flask

ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN) #Conexion con el agente de DialogFlow


@app.route('/', methods=['GET'])
def handle_verification():
    '''
   Verifica la suscripción de facebook webhook
    Es verdadero cuando VERIFY_TOKEN es igual al token enviado por la aplicación de Facebook
    '''
    if (request.args.get('hub.verify_token', '') == VERIFY_TOKEN):
        print("succefully verified")
        return request.args.get('hub.challenge', '')
    else:
        print("Wrong verification token!")
        return "Wrong validation token"


@app.route('/', methods=['POST'])
def handle_message():
    '''
    Manejador de mensajes enviados por Facebook Messenger a la aplicación
    '''
    data = request.get_json()

    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
                    recipient_id = messaging_event["recipient"]["id"]
                    message_text = messaging_event["message"]["text"]
                    send_message_response(sender_id, parse_user_message(message_text))

    return "ok"


def send_message(sender_id, message_text):
    '''
    Enviar la respuesta al usuario utilizando facebook graph API
    '''
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",

                      params={"access_token": PAT},

                      headers={"Content-Type": "application/json"},

                      data=json.dumps({
                          "recipient": {"id": sender_id},
                          "message": {"text": message_text}
                      }))


def parse_user_message(user_text):
    '''
    Envia el mensaje a API AI que invoca una intención
    y retorna la respuesta en consecuencia
    A la respuesta del bot se agrega con los datos del clima obtenidos desde la consulta via API a OpenWeatherMap
    '''

    request = ai.text_request()
    request.query = user_text
    response = json.loads(request.getresponse().read().decode('utf-8'))
    responseStatus = response['status']['code']
    if (responseStatus == 200):
        print("API AI response", response['result']['fulfillment']['speech'])
        try:

            taller_nombre = response['result']['parameters']['any']
            ci_alumno = response['result']['parameters']['number']
            print("Taller ", taller_nombre)
            print("Cedula ", ci_alumno)
            codigo_inscripcion = '1112'

            return (response['result']['fulfillment']['speech']
                    + codigo_inscripcion)
        except:
            return (response['result']['fulfillment']['speech'])

    else:
        return ("Disculpa, No entiendo la consulta")


def send_message_response(sender_id, message_text):
    sentenceDelimiter = ". "
    messages = message_text.split(sentenceDelimiter)

    for message in messages:
        send_message(sender_id, message)


if __name__ == '__main__':
    app.run()
