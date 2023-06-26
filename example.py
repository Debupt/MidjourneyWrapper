import logging
import time

import click

from midjourney_bot import MidjourneyBot, BatchBot


@click.group()
def main():
    pass


@main.command()
@click.option('--prompt', default='a cute fat cat')
def midjourneybot(prompt):
    midjourney_bot = MidjourneyBot()
    midjourney_bot.ask(prompt)

    while True:
        message = midjourney_bot.messages(1)[0]
        if midjourney_bot.validate_image_url(message):
            break
        logging.info(midjourney_bot.content(message))
        time.sleep(5)

    message = midjourney_bot.messages(1)[0]
    image_url = midjourney_bot.get_image_url(message)
    midjourney_bot.save_image(image_url, 'test.png')


@main.command()
@click.option(
    '--prompt',
    default=[
        'A koala eating mango in the Sahara desert in the style of Picasso',
        'tiny cute adorable ginger tabby kitten studio light'
    ],
    multiple=True,
)
def batchbot(prompt):
    batch_bot = BatchBot()
    for item in prompt:
        logging.info(f'{item}')
        batch_bot.prompt(item)

    while True:
        if len(prompt) == len(batch_bot.results.keys()):
            logging.info(batch_bot.results)
            batch_bot.cancel_tasks()
            return
        time.sleep(5)


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger_format = logging.Formatter(
        '[%(levelname)s][%(asctime)s][%(filename)s:%(lineno)d]: %(message)s')

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logger_format)
    logger.addHandler(stream_handler)


if __name__ == "__main__":
    setup_logger()
    main()
