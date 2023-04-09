import time

from midjourney_bot import MidjourneyBot

midjourney_bot = MidjourneyBot()
midjourney_bot.ask('a cute fat cat')

while True:
    message = midjourney_bot.messages(1)[0]
    if midjourney_bot.validate_image_url(message):
        break
    print(midjourney_bot.content(message))
    time.sleep(5)

message = midjourney_bot.messages(1)[0]
image_url = midjourney_bot.get_image_url(message)
midjourney_bot.save_image(image_url, 'test.png')
