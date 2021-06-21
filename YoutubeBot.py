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
        print("searchurls", bot_settings['searchurls'])
        self.searchurls = bot_settings['searchurls']
        print("channels: ", bot_settings['channels'])
        self.channels = bot_settings['channels']
    
    def scrapefrom(self, url):
        self.driver.get(url)
        sleep(8)

        commentCount = 0
        sleepGaps = 3
        delayCommentCount = 5
        delayScrolling = 5
        timesNoincrement = 3
        lastLength = 0
        difLength = 0

        # self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        self.driver.find_element_by_tag_name('body').send_keys(Keys.END)
        sleep(3)
        while True:
            try:
                WebDriverWait(self.driver, delayCommentCount).until(
                    EC.visibility_of_element_located((By.XPATH,'//h2[@id="count"]')))
                commentElement = self.driver.find_element_by_xpath('//h2[@id="count"]')
                commentCount = int(list(commentElement.text.split())[0].replace(',',''))
                print('count :  ', commentCount)
                break
            except:
                # self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
                self.driver.find_element_by_tag_name('body').send_keys(Keys.END)
        while True:
            try:
                WebDriverWait(self.driver, delayScrolling).until(
                    EC.visibility_of_element_located((By.XPATH, '//div[@id="contents"]/ytd-comment-thread-renderer')))

                if commentCount <= len(self.scrapingSet):
                    break
            
                # self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
                self.driver.find_element_by_tag_name('body').send_keys(Keys.END)
                commentList = self.driver.find_elements_by_xpath('//div[@id="contents"]/ytd-comment-thread-renderer')
                for comment in commentList:
                    youtubeComment = {}
                    textList = list(comment.text.split("\n"))
                    youtubeComment['name'] = textList[0]
                    # changeContent['timeAgo'] = textList[1]
                    youtubeComment['comment'] = textList[2]
                    if len(textList[3]) > 9:
                        youtubeComment['comment'] = textList[2] + ' ' + textList[3]
                    if not youtubeComment['name'] in self.scrapingSet:
                        self.scrapingSet.add(youtubeComment['name'])
                        self.scrapingList.append(youtubeComment)
                        print(youtubeComment)
            except Exception as e:
                print(e)
            difLength = len(self.scrapingSet) - lastLength
            lastLength = len(self.scrapingSet)
            if difLength == 0:
                timesNoincrement -= 1
            else:
                timesNoincrement = timesNoincrement
            if timesNoincrement == 0:
                break
            print('Set count: ', len(self.scrapingSet))
            sleep(sleepGaps)

    
    def savecsvfile(self, filename):
        try:
            with open(filename + '.csv', mode='w', encoding='utf-8') as scraping_file:
                if len(self.scrapingList) < 1:
                    return
                csv_writer = csv.DictWriter(scraping_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, fieldnames=self.scrapingList[0].keys())
                csv_writer.writeheader()
                
                for data in self.scrapingList:
                    csv_writer.writerow(data)
                self.scrapingSet = set()
                self.scrapingList = list()
        except IOError:
            print("I/O error")
            pass
    def getrullistfromchannel(self, channelurl):
        self.driver.get(channelurl)
        sleep(10)
        delayScrolling =10
        timesNoincrement = 3
        lastLength = 0
        difLength = 0
        sleepGaps = 3

        # self.driver.find_element_by_tag_name('body').send_keys(Keys.END)
        urlSet = set()
        while 1:
            try:
                self.driver.find_element_by_tag_name('body').send_keys(Keys.END)
                WebDriverWait(self.driver, delayScrolling).until(
                    EC.visibility_of_element_located((By.XPATH, '//div[@id="items"]/ytd-grid-video-renderer')))
                linkList = self.driver.find_elements_by_xpath('//div[@id="items"]/ytd-grid-video-renderer')
                for linkElement in linkList:
                    url = linkElement.find_element_by_xpath('div[1]//h3/a[@id="video-title"]').get_attribute('href')
                    if not url in urlSet:
                        urlSet.add(url)
            except:
                pass
            difLength = len(urlSet) - lastLength
            lastLength = len(urlSet)
            if difLength == 0:
                timesNoincrement -= 1
            else:
                timesNoincrement = timesNoincrement
            if timesNoincrement == 0:
                break
            print('Set count: ', len(urlSet))
            sleep(sleepGaps)
        
        return list(urlSet)


    def run(self):
        for i in range(len(self.searchurls)):
            self.scrapefrom(self.searchurls[i])
            self.savecsvfile("From_Youtube_searchurl_"+str(i))

        print('Job end.')

def main():
    with open('youtube_config.json') as json_file:
        print('loaded config.json file')
        data = json.load(json_file)
        my_bot = YoutubeBot(data)
        my_bot.run()

if __name__ == '__main__':
    main()