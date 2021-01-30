from notifiers import get_notifier
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


options = Options()
options.headless = True

driver = webdriver.Firefox(options=options)
driver.get('https://www.youtube.com/c/theWalrusStreet/community')
assert "theWalrus Street - YouTube" in driver.title

yt_element = driver.find_element_by_id('header-author')

if 'hours ago' in yt_element.text:
    print('Working')
else:
    print('Not Working ')