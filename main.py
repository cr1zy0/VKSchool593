import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import json
import os
import warnings
import lorem
import threading
import yaml



warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s')

def check_captcha(driver, capctha_popup_class):
    try:
        captcha_popup = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.CLASS_NAME, capctha_popup_class))
        )
        logging.info(f"Captcha detected. Waiting for it to be solved... ")
        WebDriverWait(driver, 300).until(
            EC.invisibility_of_element(captcha_popup)
        )
        logging.info(f"Captcha solved. Continuing. ")
    except:
        logging.info(f"No captcha detected. Continuing. ")

def login_to_VK(driver, username, password, iteration):
    buttons = driver.find_elements(By.CLASS_NAME, "vkuiSimpleCell")
    if len(buttons) >= 2:
        buttons[1].click()
        logging.info(f"Button clicked. (Thread {iteration})")
        time.sleep(2)
    else:
        logging.info(f"Button not found. (Thread {iteration})")

    login_field = driver.find_element(By.NAME, 'login')
    login_field.send_keys(username)
    continue_btn = driver.find_element(By.CLASS_NAME, 'vkuiButton__in')
    continue_btn.click()
    check_captcha(driver, 'vkc__CaptchaPopup__popupContainer')
    time.sleep(2)
    password_field = driver.find_element(By.NAME, 'password')
    password_field.send_keys(password)
    continue_btn = driver.find_element(By.CLASS_NAME, 'vkuiButton__in')
    continue_btn.click()
    check_captcha(driver, 'vkc__CaptchaPopup__popupContainer')
    continue_btn = driver.find_element(By.CLASS_NAME, 'vkuiButton__content')
    continue_btn.click()
    if save_cookies(driver, iteration):
        logging.info(f'Login successful.')
    else:
        logging.error('Incorrect loggin or password')
        driver.quit()
    

def is_cookies_file_valid(file_path):
    if not os.path.exists(file_path):
        return False
    if os.stat(file_path).st_size == 0:
        return False
    return True

def save_cookies(driver, iteration):
    with open(f'cookies/cookies({iteration}).txt','w') as file:
        cookies = driver.get_cookies()
        if cookies[0]['domain'] == 'web.vk.me':
            json.dump(cookies, file)
            logging.info(f'Cookies saved.')
            return True
        else:
            logging.warning('Cookies wasnt saved')
            return False

def load_cookies(driver, filename):
    with open(filename, "r") as file:
        cookies = json.load(file)
    
    for cookie in cookies:
        cookie.pop("expiry", None)
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            logging.warning(f"Error adding cookie {cookie['name']}: {e} ")
    driver.refresh()

def get_user_data():
    with open('data.txt','r') as data:
        return data.read().split()
    
def select_chat(driver):
    prev_url = driver.current_url
    while driver.current_url == prev_url:
        logging.info(f'Waiting for chat selection... ')
        time.sleep(2)
    logging.info(f'Chat selected. ')

def send_message(driver):
    try:
        input_field = driver.find_element(By.CLASS_NAME, 'ComposerInput__input')
        message = lorem.paragraph()
        input_field.send_keys(message)
        input_field.send_keys(Keys.ENTER)
        logging.info(f"Message sent: {message} ")
    except Exception as e:
        logging.warning(f"Error sending message: {e} ")
    
def get_config(path)->dict:
    with open(path, 'r') as file:
        data = yaml.safe_load(file)
    return data

def worker(i):
    try:
        start_event.clear()
        driver = webdriver.Chrome()
        if not is_cookies_file_valid(f'cookies/cookies({i}).txt'):
            driver.get("https://web.vk.me/")
            time.sleep(2)
            login_to_VK(driver, get_user_data()[2 * i], get_user_data()[2 * i + 1], i)
            time.sleep(2)
            select_chat(driver)
            time.sleep(2)
            start_event.set()
            while True:
                send_message(driver)
                time.sleep(get_config('config.yaml')['delay'])
        else:
            driver.get("https://web.vk.me/")
            time.sleep(2)
            load_cookies(driver, f'cookies/cookies({i}).txt')
            time.sleep(2)
            select_chat(driver)
            time.sleep(2)
            start_event.set()
            while True:
                send_message(driver)
                time.sleep(get_config('config.yaml')['delay'])

    except Exception as e:
        logging.warning(f"Error in thread {i}: {e}")
    finally:
        driver.quit()

def start_threads():
    user_count = int(len(get_user_data()) / 2)
    threads = []
    for i in range(user_count):
        thread = threading.Thread(target=worker, args=(i,), name=f'Thread-{i}')
        threads.append(thread)
        thread.start()
        start_event.wait()
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    start_event = threading.Event()
    start_threads()
