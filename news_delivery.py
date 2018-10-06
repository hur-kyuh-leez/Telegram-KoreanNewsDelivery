"""Sends Korean News to Telegram Channels"""



#-*- coding: utf-8 -*-
from selenium import webdriver
import requests
import time
import re
from datetime import datetime
import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
import signal
from googletrans import Translator
from PRIVATE_INFO import chat_id, bot





def today_is(sys='Windows'):
    # on Mac or Linux ('%-m월 %-d일') / on Windows ('%#m월 %#d일')

    if sys == 'Mac':
        KR_month_day = datetime.now(pytz.timezone('Asia/Seoul')).strftime('%-m월 %-d일')

    elif sys == 'Windows':
        KR_month_day = datetime.now(pytz.timezone('Asia/Seoul')).strftime('%#m월 %#d일')
    day = datetime.now(pytz.timezone('Asia/Seoul')).weekday()
    return KR_month_day, day


def news(KR_month_day, screenshot=False):
    browser = webdriver.PhantomJS(r'C:\Program Files (x86)\phantomjs-2.1.1-windows\bin\phantomjs')
    browser.implicitly_wait(3)
    url = "http://cwsjames.tistory.com/category/%EB%89%B4%EC%8A%A4%EC%8A%A4%ED%81%AC%EB%9E%A9"
    browser.get(url)
    news = browser.find_element_by_partial_link_text("신문브리핑(2018년 %s)" % KR_month_day).click()
    news = browser.find_element_by_xpath('// *[ @ id = "content"] / div[1] / div[2] / div[2]').text
    browser.service.process.send_signal(signal.SIGTERM)  # kill the specific phantomjs child proc
    browser.quit()
    news = news.encode('utf-8')
    news = re.sub(r'\#.*?\#', KR_month_day, news)
    news = news.replace('#', '')
    advertisement = 'COIN 고래 픽 공개채널: @CryptoWhaleDetector\nKorean News Delivery open channel: @KoreanNewsDelivery'
    news = str('%s\n%s' %(advertisement,news))
    if screenshot == True:
        browser.save_screenshot('result.png')
    return news


def translate_to_en(string):
    translator = Translator()
    translated = translator.translate(string, src='ko', dest='en').text
    return translated


def send_telegram_message(bot, chat_id, string):
    telegram_url = 'https://api.telegram.org/bot%s/sendMessage?chat_id=%s&text=%s' % (bot, chat_id, string)
    r = requests.post(telegram_url)
    print(r.text)
    if r.status_code == 200:
        send_counter = 1
    else:
        send_counter = 0
    return r.text, r.status_code, send_counter


def delivery(translate=False):
    KR_month_day, day = today_is()
    print(KR_month_day.decode('utf-8'))
    print(KR_month_day, day)
    if day in [0, 1, 2, 3, 4]: # mon ~ fri
        kor = news(KR_month_day)
        # send it, if reached maxium length then, it will fail
        kor_text, kor_status_code, kor_send_counter = send_telegram_message(bot, chat_id, kor)



        if translate == True:
            eng = "\n".join(str(translate_to_en(i)) for i in kor.split('\n'))
            print(eng)
            eng_text, eng_status_code, eng_send_counter = send_telegram_message(bot, chat_id, eng)
            if eng_send_counter != 1:
                a, b = eng[:len(eng) / 2], eng[len(eng) / 2:]
                send_telegram_message(bot, chat_id, a)
                send_telegram_message(bot, chat_id, b)
                a, b = '', ''


        if kor_send_counter != 1:

            a, b = kor[:len(kor) / 2], kor[len(kor) / 2:]
            send_telegram_message(bot, chat_id, a)
            time.sleep(10)
            if kor_send_counter == 1:
                send_telegram_message(bot, chat_id, b)
                a, b = '', ''




def main():
    """Run delivery() Mon~Thu at 9am in Seoul Time."""
    scheduler = BlockingScheduler(timezone=pytz.timezone('Asia/Seoul'))
    scheduler.add_job(delivery, 'cron', day_of_week='mon-fri', hour=9)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == '__main__':
    main()

