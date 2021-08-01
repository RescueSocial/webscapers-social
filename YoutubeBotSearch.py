from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from time import sleep
from random import randint
import json
from datetime import date
from datetime import datetime
from selenium.webdriver.common.action_chains import ActionChains
import csv

class YoutubeBot():
    def __init__(self, data):
        self.setdriver(data['selenium_settings'])
        self.set_bot(data['job_settings'])
        self.scrapingList = list()
        self.scrapingSet = set()

    def __del__(self):
        self.driver.quit()

    def setdriver(self, settings):
        print('setting chrome driver')
        options = Options()
        # options.add_argument("window-size={},{}".format(settings['size'][0], settings['size'][1]))
        options.add_argument("--disable-infobars")
        options.add_experimental_option("excludeSwitches", ['enable-automation'])
        if settings['headless'] != "False":
            options.add_argument("headless")
        self.driver = webdriver.Chrome(
            ChromeDriverManager().install(), options=options)

    def set_bot(self, bot_settings):
        print("search_texts", bot_settings['search_texts'])
        self.search_texts = bot_settings['search_texts']
    
    def scrapefromSearchText(self, query):
        url = "https://www.youtube.com/results?search_query="
        words = query.split(" ")
        start_word = 0
        for word in words:
            if start_word > 0:
                url += "+"
            url += word
            start_word += 1
        self.driver.get(url)
        sleep(8)

        sleepGaps = 3
        delayCommentCount = 5
        self.driver.find_element_by_tag_name('body').send_keys(Keys.END)
        sleep(3)
        while True:
            try:
                WebDriverWait(self.driver, delayCommentCount).until(
                    EC.visibility_of_element_located((By.XPATH,'//yt-formatted-string[text()="No more results"]')))
                break
            except:
                self.driver.find_element_by_tag_name('body').send_keys(Keys.END)
        try:
            videos = self.driver.find_elements_by_xpath('//a[@id="video-title"]')
            if len(videos) > 0:
                f = open(query+".csv", "w", encoding='utf-8')
                writer = csv.writer(f)

                # write a row to the csv file
                writer.writerow(["No", "link", "title"])
                idx = 1
                for video in videos:
                    title = video.get_attribute("title")
                    href = video.get_attribute("href")
                    writer.writerow([idx, href, title])
                    idx += 1
                f.close()
        except Exception as e:
            print(e)
        
 
    def run(self):
        for i in range(len(self.search_texts)):
            self.scrapefromSearchText(self.search_texts[i])

def main():
    with open('youtube_search_config.json') as json_file:
        print('loaded config.json file')
        data = json.load(json_file)
        my_bot = YoutubeBot(data)
        my_bot.run()

if __name__ == '__main__':
    main()