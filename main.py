import time
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from twilio.rest import Client
import configparser
import logging

config = configparser.ConfigParser()
config.read('config.ini')

# Twilio Credentials, Account SID and Auth Token
client = Client(config.get('TWILIO', 'twilio_sid'), config.get('TWILIO', 'twilio_token'))


def create_logger(**kwargs):
    """
    Wrapper to create logger for errors and training records
    :param kwargs: filepath to logger as string with logging level
    :return: logger object
    """

    log = logging.getLogger()
    log.setLevel(logging.INFO)

    # Create Log Format(s)
    f_format = logging.Formatter('%(asctime)s:%(processName)s:%(name)s:%(levelname)s:%(message)s')

    # Create Handlers
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.INFO)
    c_handler.setFormatter(f_format)
    log.addHandler(c_handler)

    for filename, level in kwargs.items():
        handler = logging.FileHandler(filename=filename)
        handler.setLevel(level)
        handler.setFormatter(f_format)
        log.addHandler(handler)

    return log


def send_notification(to_number):
    """
    Send an SMS vie Twilio API
    :param to_number: number to receive SMS
    :return:
    """
    client.messages.create(to=to_number,
                           from_=config.get('TWILIO', 'twilio_from_number'),
                           body=f'RTX 3090 FE has been added to your Best Buy cart')


def main():
    """
    Using Selenium, navigate to the RTX 3090 FE Best Buy page, check to see if it is in stock.
    If it is, add it to the cart and notify user. STDOUT is updated every 12 hours after start of script
    :return:
    """

    dict_logs = {
        'logs/e_log.log': logging.ERROR,
        'logs/c_log.log': logging.INFO
    }

    logger = create_logger(**dict_logs)

    # For using Chrome
    browser = webdriver.Chrome('chromedriver.exe')

    url = 'https://www.bestbuy.com/site/nvidia-geforce-rtx-3090-24gb-gddr6x-pci-express-4-0-' \
          'graphics-card-titanium-and-black/6429434.p?skuId=6429434'

    # BestBuy RTX 3090 page
    browser.get(url)

    purchased = False
    increment = 0

    logger.info(f'Starting Web Scraping')
    # Try to add to cart
    while not purchased:

        try:
            # If success, product is out of stock, don't need the return
            browser.find_element_by_class_name("btn-disabled")
            increment += 1
            if increment % (60*12) == 0:  # Update STDOUT every 12 hours
                logger.info(f'Product not available')
            time.sleep(60)
            browser.refresh()

        except NoSuchElementException as e:
            logger.error(e)
            # Product in stock
            add_to_cart_button = browser.find_element_by_class_name('btn-primary')
            # Click the button and end the script
            add_to_cart_button.click()
            send_notification(config.get('TWILIO', 'twilio_to_number'))
            purchased = True

    logger.info('Product is in the shopping cart')

    # Hold the window open until manual purchase can be made
    while True:
        pass


if __name__ == '__main__':
    main()
