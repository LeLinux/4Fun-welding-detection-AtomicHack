import io
import cv2
import torch
import base64
import random
import telebot
from PIL import Image
import supervision as sv
from config import Config
import pathlib
temp = pathlib.PosixPath
pathlib.PosixPath = pathlib.WindowsPath


bot = telebot.TeleBot(Config.TOKEN)
model = torch.hub.load('content/yolov5', 'custom', path='content/best.pt', source='local')
colors = [
    (random.randint(0, 255) for _ in range(3))
    for _ in range(100)
]


def get_multiline_string(*args: str):
    return '\n'.join(args)


def save_predictions(prediction, image):
    with open('content/tmp/tmp.txt', 'w') as file:
        w, h = image.size
        json = results_to_json(prediction)
        for box in json[0]:
            xmin, ymin, xmax, ymax = box["bbox"]
            file.write(f'{box["class"]} {(xmin + xmax) / w / 2} {(ymin + ymax) / h / 2} {(xmax - xmin) / w} {(ymax - ymin) / h}\n')


def results_to_json(results):
    ''' Converts yolo model output to json (list of list of dicts)'''
    return [
                [
                    {
                    "class": int(pred[5]),
                    "class_name": model.model.names[int(pred[5])],
                    "bbox": [int(x) for x in pred[:4].tolist()], #convert bbox results to int from float
                    "confidence": float(pred[4]),
                    }
                for pred in result
                ]
            for result in results.xyxy
            ]


@bot.message_handler(commands=["start"])
def start_info(message: telebot.types.Message):
    text = get_multiline_string(
        "Приветствуем Вас в боте для определение дефектов сварных швов!",
        "",
        "Вы можете прислать либо фотографию, после чего бот пришлет Вам найденные дефекты.",
        "",
        "<b>Команда 4FUN:</b>",
        "• Быков Дмитрий",
        "• Горбунов Сергей",
        "• Морозов Лукьян",
        "• Плащинский Николай",
        "",
       # "<b>Ссылка на GitHub репозиторий:</b>",
       # f"{Config.REPOSITORY}"
    )
    bot.send_message(message.chat.id, text, parse_mode='html')


@bot.message_handler(content_types=['photo'])
def compressed_image_input(message: telebot.types.Message):
    photo = message.photo[-1]
    file_info = bot.get_file(photo.file_id)
    image_data = bot.download_file(file_info.file_path)
    image = Image.open(io.BytesIO(image_data))

    results = model(image)
    detections = sv.Detections.from_yolov5(results)

    if len(results_to_json(results)[0]) == 0:
        bot.reply_to(message, "На фотографии не было найдено дефектов.")
        return

    box_annotator = sv.BoxAnnotator()
    labels = [
        f"{model.model.names[class_id]} {confidence:.2f}"
        for class_id, confidence in zip(detections.class_id, detections.confidence)
    ]
    annotated_image = box_annotator.annotate(
        scene=image.copy(),
        detections=detections,
        labels=labels,
    )
    save_predictions(results, annotated_image)

    bot.send_photo(message.chat.id, photo=annotated_image, caption="Просим присылать фото как файл, чтобы избежать потери качества")
    with open("content/tmp/tmp.txt", 'rb') as file:
        obj = io.BytesIO(file.read())
        obj.name = 'prediction.txt'
        bot.send_document(message.from_user.id, document=obj)
    print('used')


@bot.message_handler(
    content_types=['document'],
    func=lambda message: message.document.mime_type in ["image/jpeg", "image/png"]
)
def raw_image_input(message: telebot.types.Message):
    file_info = bot.get_file(message.document.file_id)
    image_data = bot.download_file(file_info.file_path)
    image = Image.open(io.BytesIO(image_data))

    results = model(image)
    detections = sv.Detections.from_yolov5(results)

    if len(results_to_json(results)[0]) == 0:
        bot.reply_to(message, "На фотографии не было найдено дефектов.")
        return

    box_annotator = sv.BoxAnnotator()
    labels = [
        f"{model.model.names[class_id]} {confidence:.2f}"
        for class_id, confidence in zip(detections.class_id, detections.confidence)
    ]
    annotated_image = box_annotator.annotate(
        scene=image.copy(),
        detections=detections,
        labels=labels,
    )
    save_predictions(results, annotated_image)

    bot.send_photo(message.chat.id, photo=annotated_image)
    with open("content/tmp/tmp.txt", 'rb') as file:
        obj = io.BytesIO(file.read())
        obj.name = 'prediction.txt'
        bot.send_document(message.from_user.id, document=obj)
    print('used')


@bot.message_handler(content_types=['document'], func=lambda message: message.document.mime_type == "application/zip")
def hello(message: telebot.types.Message):
    bot.reply_to(message, "123")


@bot.message_handler(commands=['hello'])
def hello(message: telebot.types.Message):
    bot.reply_to(message, 'Hello world!')


if __name__ == "__main__":
    bot.polling(none_stop=True)
