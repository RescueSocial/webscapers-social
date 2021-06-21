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
from datetime import datetime, timedelta
from selenium.webdriver.common.action_chains import ActionChains

from actions.tweet import TweetAction
from actions.retweet import ReplytweetAction
from services.db_driver import get_actions, performed_action, get_urls, get_client_name
from services.monitor import post_tweet

class Bot():
    def __init__(self, data):
        self.setdriver(data['selenium_settings'])
        self.set_bot(data['job_settings'])
        self.last_timestamp = datetime.utcnow() - timedelta(days=10)
        self.current_timestamp = datetime.utcnow()
        self.monitoredSet = set()
        self.current_clients = [1]
        self.my_bot_id = 1
        
        self.login(data['login'])
    def init_current_tweet(self):
        self.current_tweet={}
        self.current_tweet['who'] = ""
        if self.driver.current_url == self.monitoring_urls[0]:
            self.current_tweet['who'] = self.current_client_name
        self.current_tweet['how'] = ""
        self.current_tweet['what'] = ""
        self.current_tweet['whom'] = ""
        self.current_tweet['where'] = self.driver.current_url
        self.current_tweet['when'] = str(self.last_timestamp)
        self.current_tweet['replies'] = 0
        self.current_tweet['retweets'] = 0
        self.current_tweet['likes'] = 0
        self.current_tweet['bot'] = self.my_bot_id
        self.current_tweet['client'] = self.current_client_id
        self.current_tweet['monitor_time'] = str(datetime.utcnow())

    def check_url_is_profile(self, url):
        sub_url = url.replace('https://twitter.com/','')
        sub_keywords = sub_url.split('/')
        if len(sub_keywords) < 2:
            return True
        elif len(sub_keywords)==2 and sub_keywords[1]=='with_replies':
            return True
        else:
            return False

    def parse_article(self, article):
        article_texts = list(article.text.split("\n"))
        if len(article_texts) < 4:
            return False
        self.init_current_tweet()
        # Pre Processing 
        try:
            for del_char in ['',' ','·']:
                if del_char in article_texts: article_texts.remove(del_char)
            for del_end_char in ['Promoted','Show this thread']:
                if del_end_char == article_texts[-1]: article_texts.pop(-1)
            for check_digit in ['replies', 'retweets', 'likes']:
                if len(article_texts[-1]) < 6 and article_texts[-1][0].isdigit():
                    article_texts.pop(-1)
            for del_end_char in ['Show this thread']:
                if del_end_char == article_texts[-1]: article_texts.pop(-1)
        except Exception as e:
            print(e)
            pass
        
        print(article_texts)
        whom_when_string = ""
        try:
            time_elements = article.find_elements_by_xpath('div//time')
            when_string = time_elements[0].get_attribute('datetime').split('.')[0].replace('T',' ')
            if len(time_elements) > 1:
                whom_when_string = time_elements[1].get_attribute('datetime').split('.')[0].replace('T',' ')
            self.current_tweet['when'] = when_string
            tweet_time = datetime.strptime(when_string,'%Y-%m-%d %H:%M:%S.%f')
            # print(self.current_tweet['when'])
            if tweet_time < self.last_timestamp or tweet_time >= self.current_timestamp:
                return False
        except:
            pass
        try:
            self.current_tweet['replies'] = int(article.find_element_by_xpath("div//div[contains(@aria-label,'. Reply')]").get_attribute('aria-label').split()[0])
            self.current_tweet['retweets'] = int(article.find_element_by_xpath("div//div[contains(@aria-label,'. Retweet')]").get_attribute('aria-label').split()[0])
            self.current_tweet['likes'] = int(article.find_element_by_xpath("div//div[contains(@aria-label,'. Like')]").get_attribute('aria-label').split()[0])
        except Exception as e:
            print(e)

        
        user_indexs = [i for i, item in enumerate(article_texts) if item.startswith('@')]
        if " Retweeted" in article_texts[0]:
            self.current_tweet['who'] = article_texts[0] + ' for ' + article_texts[user_indexs[0]]
        else:
            self.current_tweet['who'] = article_texts[user_indexs[0]]

        if "Replying to " in article_texts:
            self.current_tweet['how'] = "Reply"
            whoms = [ele.text for ele in article.find_element_by_xpath("div//div[contains(text(),'Replying to ')]").find_elements_by_xpath("*")]
            try:
                replaytoend_index = article_texts.index(whoms[-1],2)
            except:
                replaytoend_index = article_texts.index(' '+whoms[-1],2)
            
            self.current_tweet['whom'] = ' '.join(map(str, whoms))
            main_tweet = article_texts[replaytoend_index+1:]
            self.current_tweet['what'] = ' '.join(map(str, main_tweet))
            if len(self.current_tweet['what']) < 6:
                return False
            # self.current_tweet['what'] = article_texts[replaytoend_index + 1]
        elif "Quote Tweet" in article_texts:
            self.current_tweet['how'] = "QuoteTweet"
            index_quote = article_texts.index("Quote Tweet")
            main_tweet = article_texts[user_indexs[0]+2:index_quote]
            
            self.current_tweet['what'] = ' '.join(map(str, main_tweet))
            if len(self.current_tweet['what']) < 6:
                return False
            quote_tweet = article_texts[index_quote:]
            whom_name = article_texts[user_indexs[-1]]
            self.current_tweet['whom'] = whom_name +'\n'
            self.current_tweet['whom'] += whom_when_string +'\n'
            whom_tweet = ' '.join(map(str, quote_tweet[quote_tweet.index(whom_name)+2:]))
            self.current_tweet['whom'] += whom_tweet

        else:
            self.current_tweet['how'] = "Tweet"
            self.current_tweet['whom'] = "Everyone"
            main_tweet = article_texts[user_indexs[0]+2:]
            self.current_tweet['what'] = ' '.join(map(str, main_tweet))
            if len(self.current_tweet['what']) < 6:
                return False
        print(self.current_tweet)
        return True


    def run(self):
        print('running bot')
        while True:
            self.current_timestamp = datetime.utcnow()
            print('monittoring stamp from {} to {}'.format(str(self.last_timestamp), str(self.current_timestamp)))
            for current_client_id in self.current_clients:
                self.current_client_id = current_client_id
                self.monitoring_urls = get_urls(current_client_id)
                self.current_client_name = "@" + get_client_name(current_client_id)
                
                for monitoring_url in self.monitoring_urls:
                    try:
                        self.driver.get(monitoring_url)
                        print('new monitoring from url: ', monitoring_url)
                        sleep(5)
                    except Exception as e:
                        print(e)
                        continue
                    

                    condition = True
                    sleepGaps = 3
                    timesNoincrement = 3
                    lastLength = 0
                    difLength = 0
                    max_pages = 5

                    while condition:
                        try:
                            if max_pages > 0:
                                print('Next page!')
                                max_pages -= 1
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
                            else:
                                break
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
                                    if self.parse_article(articleList[i]):
                                        mornitored_keyword = self.current_tweet['who']+'_'+str(self.current_tweet['when'])
                                        if not mornitored_keyword in self.monitoredSet:
                                            self.monitoredSet.add(mornitored_keyword)
                                            print(self.current_tweet)
                                            action_json = post_tweet(self.current_tweet)
                                            if action_json['method']=="None":
                                                pass
                                            elif action_json['method']=="Retweet":
                                                if ReplytweetAction.reTweet(driver=self.driver, article=articleList[i]):
                                                    performed_action(action_json['id'])
                                            elif action_json['method']=="Like":
                                                if ReplytweetAction.likeTweet(driver=self.driver, article=articleList[i]):
                                                    performed_action(action_json['id'])
                                except Exception as e:
                                    print(e)
                                    continue

                            
                            #check if endness
                            difLength = len(self.monitoredSet) - lastLength
                            lastLength = len(self.monitoredSet)
                            if difLength == 0:
                                timesNoincrement -= 1
                            else:
                                timesNoincrement = timesNoincrement
                            if timesNoincrement == 0:
                                condition = False
                            print('Set count: ', len(self.monitoredSet))
                            sleep(sleepGaps)
                        except Exception as e:
                            print(e)
            self.last_timestamp = self.current_timestamp
            sleep(1)
        
    def setdriver(self, settings):
        print('setting chrome driver')
        options = Options()
       
        options.add_experimental_option("excludeSwitches", ['enable-automation'])
        options.add_argument("user-data-dir=C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\User Data")
        options.add_argument('--profile-directory=Default')
        self.driver = webdriver.Chrome(
            executable_path='chromedriver.exe', options=options)
       
    def checkLoggedIn(self):
        if self.driver.current_url=='https://twitter.com/home' :
            print('Sucessfully Logged In.')
            return True
        else:
            return False
    def login(self, loginInfo):

        self.driver.get(loginInfo['url'])
        sleep(3)
        if self.checkLoggedIn():
            return True
        try:
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located(
                (By.XPATH, '//input[@name="session[username_or_email]"]'))).send_keys(loginInfo['userId'])
            print('Inserted email correctly.')
            self.driver.find_element(
                By.XPATH, '//input[@name="session[password]"]').send_keys(loginInfo['password'])
            self.driver.find_element(
               By.XPATH, '//input[@name="session[password]"]').send_keys(Keys.RETURN)
            sleep(2)
            try:
                self.driver.find_element(
                    By.XPATH, '//input[@id="challenge_response"]').send_keys(loginInfo['phoneNumber'])
            except Exception as e:
                print(e)
            return self.checkLoggedIn()
        except Exception as e:
            print(e)
            print(
                'Login Failed! sorry please set the config file for login informantion.')
            sleep(randint(1, 5))
            if self.checkLoggedIn():
                print('Sucessfully Logged In.')
                return True
            self.login(loginInfo)
            return False

    def set_bot(self, bot_settings):
        print('setting bot')


def main():
    with open('twitter_bot_settings.json') as json_file:
        print('loaded config.json file')
        data = json.load(json_file)
        my_bot = Bot(data)
        my_bot.run()


if __name__ == '__main__':
    main()