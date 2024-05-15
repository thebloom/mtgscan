import logging
import os
import time

import requests
from mtgscan.box_text import BoxTextList
from mtgscan.utils import is_url
from .ocr import OCR

from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential

class Azure(OCR):

    def __init__(self):
        try:
            self.subscription_key = os.environ['VISION_KEY']
            self.text_recognition_url = os.environ['VISION_ENDPOINT'] + "computervision/imageanalysis:analyze?api-version=2024-02-01&features=read"
        except IndexError as e:
            print(str(e))
            print(
                "Azure credentials should be stored in environment variables AZURE_VISION_KEY and AZURE_VISION_ENDPOINT"
            )

    def __str__(self):
        return "Azure"

    def image_to_box_texts(self, image: str, is_base64=False) -> BoxTextList:
        client = ImageAnalysisClient(
            endpoint=os.environ['VISION_ENDPOINT'],
            credential=AzureKeyCredential(os.environ['VISION_KEY'])
        )
        
        visual_features =[
            VisualFeatures.READ,
        ]
        # For URL:
        # result = client.analyze_from_url(
        #     image_url=image,
        #     visual_features=visual_features,
        #     language="en"
        # )
        # For local file: Analyze all visual features from an image stream. This will be a synchronously (blocking) call.
        with open(image, "rb") as f:
            image_data = f.read()
        result = client.analyze(
            image_data=image_data,
            visual_features=visual_features,
            language="en"
        )
        box_texts = BoxTextList()
        if result.read is not None:
            for line in result.read.blocks[0].lines:
                boundingBox = []
                for point in line.bounding_polygon:
                    boundingBox.append(point.x)
                    boundingBox.append(point.y)
                boundingTuple = tuple(boundingBox)
                box_texts.add(boundingTuple, line.text)
        # if result.read is not None:
        #     print(" Read:")
        #     for line in result.read.blocks[0].lines:
        #         print(f"   Line: '{line.text}', Bounding box {line.bounding_polygon}")
        #         for word in line.words:
        #             print(f"     Word: '{word.text}', Bounding polygon {word.bounding_polygon}, Confidence {word.confidence:.4f}")


        # Create an Image Analysis client
        # client = ImageAnalysisClient(
        #     endpoint=os.environ['VISION_ENDPOINT'],
        #     credential=AzureKeyCredential(self.subscription_key)
        # )
        # # [START read]
        # # Load image to analyze into a 'bytes' object
        # with open("decktest.jpeg", "rb") as f:
        #     image_data = f.read()

        # # Extract text (OCR) from an image stream. This will be a synchronously (blocking) call.
        # result = client.analyze(
        #     image_data=image_data,
        #     visual_features=[VisualFeatures.READ]
        # )
        # headers = {'Ocp-Apim-Subscription-Key': self.subscription_key}
        # json, data = None, None
        
        # if is_url(image):
        #     json = {'url': image}
        # else:
        #     headers['Content-Type'] = 'application/json'
        #     data = image
        #     if not is_base64:
        #         with open(image, "rb") as f:
        #             data = f.read()
        # logging.info(f"Send {image} to Azure")
        # response = requests.post(self.text_recognition_url, headers=headers, json=json, data=data)
        # response_data = response.json()
        # box_texts = BoxTextList()
        # print(response_data)
        # for line in response_data["readResult"]["blocks"][0]["lines"]:
        #     boundingBox = []
        #     for point in line["boundingPolygon"]:
        #         boundingBox.append(point["x"])
        #         boundingBox.append(point["y"])
        #     boundingTuple = tuple(boundingBox)
        #     box_texts.add(boundingTuple, line["text"])

        return box_texts
