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

class ChangeOrgBot():
    def __init__(self, data):
        self.setdriver(data['selenium_settings'])
        self.set_bot(data['job_settings'])
        self.scrapingList = list()

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
        print("searchurls", bot_settings['searchurls'])
        self.searchurls = bot_settings['searchurls']
    
    def scrapefrom(self, url):
        self.driver.get(url)
        sleep(8)

        sleepGaps = 3
        delayMorebutton = 10

        while True:
            try:
                WebDriverWait(self.driver, delayMorebutton).until(
                    EC.visibility_of_element_located((By.XPATH, '//div[@data-view="components/comments_feed/index"]/div[2]/div[1]/button')))
            except Exception as e:
                print(e)
                break
            self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            
            buttonMore = self.driver.find_element_by_xpath('//div[@data-view="components/comments_feed/index"]/div[2]/div[1]/button')
            buttonMore.click()
            # scrolling down
            sleep(sleepGaps)
        
        dataviewList = self.driver.find_elements_by_xpath('//div[@data-view="components/comments_feed/comment_card"]')
        for dataview in dataviewList:
            changeContent = {}
            textList = list(dataview.text.split("\n"))
            changeContent['name'] = textList[0]
            # changeContent['timeAgo'] = textList[1]
            changeContent['comment'] = textList[2]
            changeContent['loveCount'] = textList[3]
            print(changeContent)
            self.scrapingList.append(changeContent)

    
    def savecsvfile(self, filename):
        try:
            with open(filename + '.csv', mode='w', encoding='utf-8') as scraping_file:
                csv_writer = csv.DictWriter(scraping_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, fieldnames=self.scrapingList[0].keys())
                csv_writer.writeheader()
                
                for data in self.scrapingList:
                    csv_writer.writerow(data)

                self.scrapingList = list()
        except IOError:
            print("I/O error")
            pass

    def run(self):
        for i in range(len(self.searchurls)):
            self.scrapefrom(self.searchurls[i])
            self.savecsvfile("From_ChangeOrg_searchurl_"+str(i))
        
        print('Job end.')


def main():
    with open('change_config.json') as json_file:
        print('loaded config.json file')
        data = json.load(json_file)
        my_bot = ChangeOrgBot(data)
        my_bot.run()

if __name__ == '__main__':
    main()