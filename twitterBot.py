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

# "https://twitter.com/amberheardsourc",

class TwitterBot():
    def __init__(self, data):
        self.setdriver(data['selenium_settings'])
        self.set_bot(data['job_settings'])
        self.scrapingSet = set()
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
        print("hashtags:", bot_settings["hashtags"])
        self.hashtags = bot_settings["hashtags"]
        print("searchurls", bot_settings['searchurls'])
        self.searchurls = bot_settings['searchurls']
        print("profiles", bot_settings['profiles'])
        self.profiles = bot_settings['profiles']

    def geturlfromhashtag(self, hashtag):
        return_url = "https://twitter.com/search?q=%23HashTag&src=typed_query"
        return return_url.replace("HashTag", hashtag)
    def getUserName(self, textList):
        if 'Retweeted' in textList[0]:
            return textList[1]
        else:
            return textList[0]
    def scrapefrom(self, url):
        self.driver.get(url)
        sleep(5)
        print('new scraping from url: ', url)
        condition = True
        sleepGaps = 3
        timesNoincrement = 3
        lastLength = 0
        difLength = 0

        while condition:
            try:
                print('Next page!')
                # scrolling down
                self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
                try:
                    show_more = self.driver.find_element_by_xpath('//div[@role="button"]/div/div/span[text()="Show more replies"]')
                    show_more_button = show_more.find_element_by_xpath('../../..')
                    show_more_button.click()
                    print('clicked show more button ok!')
                    sleep(3)
                except:
                    pass
                WebDriverWait(self.driver, 20).until(
                    EC.visibility_of_element_located((By.XPATH, '//article[@role="article"]')))
                articleList = self.driver.find_elements_by_xpath('//article[@role="article"]')
                

                for i in range(len(articleList)):
                    try:
                        try:
                            show_button = articleList[i].find_element_by_xpath('//div[@role="button"]')
                            # show_button.click()
                            if 'show more' in show_button.text:
                                show_button.click()
                            elif 'show' in show_button.text:
                                show_button.click()
                            pass
                        except:
                            pass              
                        twitterContent = {}
                        textList = list(articleList[i].text.split("\n"))
                        if 'Retweeted' in textList[0]:
                            twitterContent['userName'] = textList[1]
                            twitterContent['text'] = textList[5]
                        else:
                            twitterContent['userName'] = textList[0]
                            twitterContent['text'] = textList[4]

                        twitterContent['taggedUserName'] = ''

                        for j in range(5):
                            if '@' in textList[j+1]:
                                twitterContent['taggedUserName'] = textList[j+1]
                                break
                     
                        try:
                            twitterContent['img1'] = articleList[i].find_element_by_xpath(
                                'div[1]/div[1]/div[1]/div[2]/div[2]/div[2]/div[2]//img').get_attribute('src')
                        except:
                            twitterContent['img1'] = ''
                        try:
                            twitterContent['img2'] = articleList[i].find_element_by_xpath(
                                'div[1]/div[1]/div[1]/div[2]/div[2]/div[2]/div[3]//img').get_attribute('src')
                            print('image 2', twitterContent['img2'])
                        except:
                            twitterContent['img2'] = ''
                        print("select number:", i)
                        
                        print(twitterContent)
                        if not twitterContent['text'] in self.scrapingSet:
                            self.scrapingSet.add(twitterContent['text'])
                            self.scrapingList.append(twitterContent)

                    except Exception as e:
                        print(e)
                        continue

                
                #check if endness
                difLength = len(self.scrapingSet) - lastLength
                lastLength = len(self.scrapingSet)
                if difLength == 0:
                    timesNoincrement -= 1
                else:
                    timesNoincrement = timesNoincrement
                if timesNoincrement == 0:
                    condition = False
                print('Set count: ', len(self.scrapingSet))
                sleep(sleepGaps)
            except Exception as e:
                print(e)
        return
    
    def savecsvfile(self, filename):
        try:
            if len(self.scrapingList) > 0:
                with open(filename + '.csv', mode='w', encoding='utf-8') as scraping_file:
                    csv_writer = csv.DictWriter(scraping_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, fieldnames=self.scrapingList[0].keys())
                    csv_writer.writeheader()
                    
                    for data in self.scrapingList:
                        csv_writer.writerow(data)

                    self.scrapingSet = set()
                    self.scrapingList = list()
            else:
                print('scraping data is none! ')
        except IOError:
            print("I/O error")
            pass
    def getrullistfromprofile(self, profileurl, retweet = False):
        self.driver.get(profileurl)
        sleep(5)

        condition = True
        sleepGaps = 3
        timesNoincrement = 3
        lastLength = 0
        difLength = 0
        urlSet = set()

        while condition:
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.visibility_of_element_located((By.XPATH, '//article[@role="article"]')))
                articleList = self.driver.find_elements_by_xpath('//article[@role="article"]')
                for i in range(len(articleList)):
                    try:
                        if not retweet and not 'Amber Heard Italia Fans Retweeted' in articleList[i].find_element_by_xpath('div[1]/div[1]/div[1]/div[1]').text:
                            nexturl = articleList[i].find_element_by_xpath('div/div/div/div[2]/div[2]/div[1]/div/div/div[1]/a').get_attribute('href')
                            if not nexturl in urlSet:
                                urlSet.add(nexturl)
                        elif retweet and 'Amber Heard Italia Fans Retweeted' in articleList[i].find_element_by_xpath('div[1]/div[1]/div[1]/div[1]').text:
                            nexturl = articleList[i].find_element_by_xpath('div/div/div/div[2]/div[2]/div[1]/div/div/div[1]/a').get_attribute('href')
                            if not nexturl in urlSet:
                                urlSet.add(nexturl)
                        else:
                            pass
                    except Exception as e:
                        print(e)
                        continue

                # scrolling down
                self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
                #check if endness
                difLength = len(urlSet) - lastLength
                lastLength = len(urlSet)
                if difLength == 0:
                    timesNoincrement -= 1
                else:
                    timesNoincrement = timesNoincrement
                if timesNoincrement == 0:
                    condition = False
                print('Set urls count: ', len(urlSet))
                sleep(sleepGaps)
            except Exception as e:
                print(e)
        return list(urlSet)
    def run(self):
        for i in range(len(self.searchurls)):
            self.scrapefrom(self.searchurls[i])
            self.savecsvfile("From_Twitter_searchurl_"+str(i))

        print('running bot')


def main():
    with open('twitter_config3.json') as json_file:
        print('loaded config.json file')
        data = json.load(json_file)
        my_bot = TwitterBot(data)
        my_bot.run()

if __name__ == '__main__':
    main()