from openai import OpenAI
from PIL import Image
import requests
from io import BytesIO
from config import OPENAI_API_KEY_EN, OPENAI_API_KEY_RU


client = OpenAI(api_key=OPENAI_API_KEY_RU, base_url="https://api.proxyapi.ru/openai/v1")
# client = OpenAI(api_key=OPENAI_API_KEY_EN)

response = client.images.generate(
  model="dall-e-3",
  prompt="Ледяной Фьельд — это мир, погруженный в вечную зиму и укрытый толстым слоем снега и льда. Северные ветры несут с собой не только холода, но и мифические создания, обитающие в ледяных пустошах. Природа здесь жестока, а жизнь людей зависит от суровых законов выживания. Деревни раскиданы по подножиям глыб льда, а таинственные ледяные замки прячутся в нескончаемых снежных метелях. В этом мире сражаются герои и искатели приключений, стремящиеся разгадать тайны древнего холода.",
  size="1024x1024",
  n=1,
)

image_url = response.data[0].url

response2 = requests.get(image_url)
img = Image.open(BytesIO(response2.content))

img.show()

