import csv
from time import sleep
from msedge.selenium_tools import Edge, EdgeOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common import exceptions


def create_webdriver_instance():
    options = EdgeOptions()
    options.use_chromium = True
    driver = Edge(options=options)
    return driver


def login_to_twitter(username, password, driver):
    url = 'https://twitter.com/login'
    try:
        driver.get(url)
        xpath_username = '//input[@name="username"]'
        WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.XPATH, xpath_username)))
        uid_input = driver.find_element_by_xpath(xpath_username)
        uid_input.send_keys(username)
        uid_input.send_keys(Keys.RETURN)
    except exceptions.TimeoutException:
        print("Timeout - login")
        return False
    xpath_password = '//input[@name="password"]'
    WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.XPATH, xpath_password)))
    pwd_input = driver.find_element_by_xpath('//input[@name="password"]')
    pwd_input.send_keys(password)
    try:
        pwd_input.send_keys(Keys.RETURN)
        url = "https://twitter.com/home"
        WebDriverWait(driver, 10).until(expected_conditions.url_to_be(url))
    except exceptions.TimeoutException:
        print("Timeout - Login")
    return True


def find_search_input_and_enter_criteria(search_term, driver):
    try:
        xpath_search = "//input[@aria-label='Search query']"
        WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.XPATH, xpath_search)))
        search_input = driver.find_element_by_xpath(xpath_search)
        search_input.send_keys(search_term)
        search_input.send_keys(Keys.RETURN)
        return True

    except exceptions.TimeoutException:
        print("Timeout - Search")
        return False

def change_page_sort(driver):
    try:

        WebDriverWait(driver, 20).until(expected_conditions.element_to_be_clickable((By.LINK_TEXT, 'Latest')))
        tab = driver.find_element_by_link_text('Latest').click()
        #xpath_tab_state = f'//a[contains(text(),\"Latest\") and @aria-selected=\"true\"]'

    except exceptions.TimeoutException:
        print("Timeout - Sort")
    return

def generate_tweet_id(tweet):
    return ''.join(tweet)


def scroll_down_page(driver, last_position, num_seconds_to_load=0.5, scroll_attempt=0, max_attempts=5):
    end_of_scroll_region = False
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(num_seconds_to_load)
    curr_position = driver.execute_script("return window.pageYOffset;")
    if curr_position == last_position:
        if scroll_attempt < max_attempts:
            end_of_scroll_region = True
        else:
            scroll_down_page(last_position, curr_position, scroll_attempt + 1)
    last_position = curr_position
    return last_position, end_of_scroll_region


def save_tweet_data_to_csv(records, filepath, mode='a+'):
    header = ['User', 'Handle', 'PostDate', 'TweetText', 'ReplyCount', 'RetweetCount', 'LikeCount']
    with open(filepath, mode=mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if mode == 'w':
            writer.writerow(header)
        if records:
            writer.writerow(records)


def collect_all_tweets_from_current_view(driver, lookback_limit=25):
    #check last 25 tweets
    page_cards = driver.find_elements_by_xpath('//article[@data-testid="tweet"]')
    if len(page_cards) <= lookback_limit:
        return page_cards
    else:
        return page_cards[-lookback_limit:]


def extract_data_from_current_tweet_card(card):
    try:
        user = card.find_element_by_xpath('.//span').text
    except exceptions.NoSuchElementException:
        user = ""
    except exceptions.StaleElementReferenceException:
        return
    try:
        handle = card.find_element_by_xpath('.//span[contains(text(), "@")]').text
    except exceptions.NoSuchElementException:
        handle = ""
    try:
        postdate = card.find_element_by_xpath('.//time').get_attribute('datetime')
    except exceptions.NoSuchElementException:
        return
    try:
        _comment = card.find_element_by_xpath('.//div/div/div/div[2]/div[2]/div[2]/div[1]').text
    except exceptions.NoSuchElementException:
        _comment = ""
    tweet_text = _comment
    try:
        reply_count = card.find_element_by_xpath('.//div[@data-testid="reply"]').text
    except exceptions.NoSuchElementException:
        reply_count = ""
    try:
        retweet_count = card.find_element_by_xpath('.//div[@data-testid="retweet"]').text
    except exceptions.NoSuchElementException:
        retweet_count = ""
    try:
        like_count = card.find_element_by_xpath('.//div[@data-testid="like"]').text
    except exceptions.NoSuchElementException:
        like_count = ""

    tweet = (user, handle, postdate, tweet_text, reply_count, retweet_count, like_count)
    return tweet


def main(username, password, search_term, filepath):
    save_tweet_data_to_csv(None, filepath, 'w')  # create file for saving records

    last_position = None
    end_of_scroll_region = False
    unique_tweets = set()

    driver = create_webdriver_instance()
    logged_in = login_to_twitter(username, password, driver)

    if not logged_in:
        return

    search_found = find_search_input_and_enter_criteria(search_term, driver)
    if not search_found:
        return

    change_page_sort(driver)
    tweet_id_count = 0

    while not end_of_scroll_region and tweet_id_count <= 3050:
        cards = collect_all_tweets_from_current_view(driver)
        for card in cards:
            try:
                tweet = extract_data_from_current_tweet_card(card)
            except exceptions.StaleElementReferenceException:
                continue
            if not tweet:
                continue
            tweet_id = generate_tweet_id(tweet)
            if tweet_id not in unique_tweets:
                unique_tweets.add(tweet_id)
                save_tweet_data_to_csv(tweet, filepath)
                tweet_id_count += 1
        last_position, end_of_scroll_region = scroll_down_page(driver, last_position)
    print(tweet_id_count)
    driver.quit()


if __name__ == '__main__':
    usr = "twitterhandle"
    pwd = "password"
    path = 'dune_scrape.csv'
    term = '"dune" min_faves:100 lang:en -filter:links -filter:replies'

    main(usr, pwd, term, path)
