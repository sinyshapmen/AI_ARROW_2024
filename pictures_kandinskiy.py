import json
import time
import requests
import base64
import io
from PIL import Image
from config import PATH 
class Text2ImageAPI:

    def __init__(self, url, api_key, secret_key):
        self.URL = url
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }

    def get_model(self):
        response = requests.get(self.URL + 'key/api/v1/models', headers=self.AUTH_HEADERS)
        data = response.json()
        return data[0]['id']

    def generate(self, prompt, model, images=1, width=1024, height=680):
        params = {
            "type": "GENERATE",
            "numImages": images,
            "width": width,
            "height": height,
            "generateParams": {
                "query": f"{prompt}"
            }
        }

        data = {
            'model_id': (None, model),
            'params': (None, json.dumps(params), 'application/json')
        }
        response = requests.post(self.URL + 'key/api/v1/text2image/run', headers=self.AUTH_HEADERS, files=data)
        data = response.json()
        return data['uuid']

    def check_generation(self, request_id, attempts=10, delay=10):
        while attempts > 0:
            response = requests.get(self.URL + 'key/api/v1/text2image/status/' + request_id, headers=self.AUTH_HEADERS)
            data = response.json()
            if data['status'] == 'DONE':
                return data['images']

            attempts -= 1
            print(-1)
            time.sleep(delay)



# генерация изображений во временный файл   
def temp_picture(prompt: str):
    api = Text2ImageAPI('https://api-key.fusionbrain.ai/', '60BE7FDCC467379AC029C2E62A5E8C51', 'E6DC282C0F845F542D8AEA40F3F3583E')
    model_id = api.get_model()
    uuid = api.generate(prompt, model_id)
    images = api.check_generation(uuid)

    base64_encoded_image = images[0]
    image_bytes = base64.b64decode(base64_encoded_image)
    image = Image.open(io.BytesIO(image_bytes))

    image.save(PATH + 'temp_storage.png')
    return PATH + 'temp_storage.png'

# Функция, которая переводит русские символы в английские.
def rus_to_eng(text):
  text = text.lower()
  translation_table = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i', 
    'й': 'j', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
    'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y',
    'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
  }
  return ''.join([translation_table.get(char.lower(), char) for char in text])


# генерация изображений в постоянный файл
def save_picture(name: str, prompt: str):
    api = Text2ImageAPI('https://api-key.fusionbrain.ai/', '60BE7FDCC467379AC029C2E62A5E8C51', 'E6DC282C0F845F542D8AEA40F3F3583E')
    model_id = api.get_model()
    uuid = api.generate(prompt, model_id)
    images = api.check_generation(uuid)

    base64_encoded_image = images[0]
    image_bytes = base64.b64decode(base64_encoded_image)
    image = Image.open(io.BytesIO(image_bytes))
    
    image.save(PATH + f'game_characters/{rus_to_eng(name)}.png')
    return PATH + f'game_characters/{rus_to_eng(name)}.png'


