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

# "https://www.facebook.com/pg/AmberHeardOfficial/reviews/", from

class FacebookBot():
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
        print("searchurls", bot_settings['searchurls'])
        self.searchurls = bot_settings['searchurls']

    def check_Login_Not_Now(self):
        try:
            show_more_button = self.driver.find_element_by_xpath('//a[text()="Not Now"]')
            show_more_button.click()
            print('clicked Not Now button!')
            sleep(2)
        except:
            pass
        return

    def scroll_down(self):
        try:
            # scrolling down
            self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            print('Next page!')
            sleep(2)
        except:
            pass
        return
    def scroll_end(self):
        self.driver.find_element_by_tag_name('body').send_keys(Keys.END)
        print('End page!')
        sleep(2)
    def get_posts(self):
        try:
            WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located((By.XPATH, '//div[@id="pagelet_timeline_main_column"]//div[@class="_1xnd"]/div[@class="_4-u2 _4-u8"]')))
            return self.driver.find_elements_by_xpath('//div[@id="pagelet_timeline_main_column"]//div[@class="_1xnd"]/div[@class="_4-u2 _4-u8"]')
        except:
            return []

    def check_post_view_more_comments(self, post):
        try:
            self.scroll_end()
            post.find_element_by_partial_link_text('View more comments').click()
            print('clicked View more comments on post ok!')
            sleep(2)
            return True
        except:
            return False
    def getCommentUserName(self, comment_element):
        try:
            user_name = comment_element.find_element_by_xpath('div[1]//div/span[@class="_6qw4"]').text
        except:
            try:
                user_name = comment_element.find_element_by_xpath('div[1]//div/a[@class="_6qw4"]').text
            except:
                user_name = ''
        return user_name
    def getComment(self, comment_element):
        try:
            return comment_element.find_element_by_xpath('div[1]//div/span[@dir="ltr"]').text
        except:
            return ''
    def getCommentsfromPost(self, post_element):
        try:
            WebDriverWait(post_element, 20).until(
                EC.visibility_of_element_located((By.XPATH, 'div//form[@class="commentable_item"]/div/div[3]/ul/li')))
            return post_element.find_elements_by_xpath('div//form[@class="commentable_item"]/div/div[3]/ul/li')
        except:
            return []

    def scrapefrom(self, url, post_num):
        self.driver.get(url)
        sleep(5)
        print('new scraping from url: ', url)
        condition = True
        sleepGaps = 3
        timesNoincrement = 3
        lastLength = 0
        difLength = 0

        # while condition:
        try:
            self.scroll_down()
            self.check_Login_Not_Now()
            c_posts = self.get_posts()

            # for i in range(len(c_posts)):
            c_post = c_posts[post_num]
            try:
                while self.check_post_view_more_comments(c_post):
                    print('clicked View more comments on this post')
                # self.check_post_view_more_comments(c_post)
                c_comments = self.getCommentsfromPost(c_post)

                for i in range(len(c_comments)):
                    print("comment number : ", i + 1)
                    c_comment = c_comments[i]
                    facebookComment = {}
                    facebookComment["userName"] = self.getCommentUserName(c_comment)
                    facebookComment['comment'] = self.getComment(c_comment)
                    print(facebookComment)
                    if not facebookComment['comment'] in self.scrapingSet:
                        self.scrapingSet.add(facebookComment['comment'])
                        self.scrapingList.append(facebookComment)

            except Exception as e:
                print(e)
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

    def run(self):
        for i in range(6):
            self.scrapefrom(self.searchurls[0], i)
            self.savecsvfile("From_Facebook_post_"+str(i))
        print('running Facebook bot')


def main():
    with open('facebook_config.json') as json_file:
        print('loaded config.json file')
        data = json.load(json_file)
        my_bot = FacebookBot(data)
        my_bot.run()

if __name__ == '__main__':
    main()