"""A module for scraping Glassdoor for company reviews.

This module is the driver for a Glassdoor scraper. It controls the process of
instantiating a Selenium browser to scrape, and controls that browser throughout 
the entire process. It also handles parsing and storing our results. 

Usage: 

    python job_scraper.py <job title> <job location>
"""
import sys
import os
import random
import hashlib
import time
import datetime
import pytz
from selenium import webdriver
from general_utilities.parsing_utilities import parse_num
from general_utilities.mysql_connection import MySqlConnector
import pandas as pd
import creds


# wd = os.path.abspath('.')
# sys.path.append(wd + '/../')
Keys = webdriver.common.keys.Keys
By = webdriver.common.by.By
ActionChains = webdriver.common.action_chains.ActionChains

def scrape_job_page(driver, job_title, job_location):
    """Scrape a page of reviews from Glassdoor.

    Args: 
        driver: Selenium webdriver
        job_title: str
        job_location: str
    """

    current_date = str(datetime.datetime.now(pytz.timezone('US/Mountain')))
    json_dct = {'search_title': job_title,
                'search_location': job_location,
                'search_date': current_date, 'job_site': 'glassdoor'}

    jobs = driver.find_elements_by_class_name('jobListing')

    mongo_update_lst = [query_for_data(driver, json_dct, job, idx) for
            idx, job in enumerate(jobs[:-1])]

    store_in_mongo(mongo_update_lst, 'job_postings', 'glassdoor')


def query_for_data(driver, json_dct, job, idx):
    """Grab all info. from the job posting
    
    This will include the job title, the job location, the 
    posting company, the date posted, and then any stars assigned. 
    After grabbing this information, click and get the job posting's
    actual text. 

    Args: 
        driver: Selenium webdriver
        json_dct: dict 
            Dictionary holding the current information that is being stored
            for that job posting. 
        job: Selenium WebElement
        idx: int
            Holds the # of the job posting the program is on (0 indexed here). 

    Return: dct
    """

    posting_title = job.find_element_by_class_name('title').text
    split_posting_company = job.find_element_by_class_name(
            'companyInfo').text.split()
    posting_location = job.find_element_by_xpath(
            "//div//span[@itemprop='jobLocation']").text
    try:
        posting_date = job.find_element_by_class_name('minor').text
    except:
        posting_date = ''

    # I couldn't think of any clearly better way to do this. If they have 
    # a number of stars, it comes in the posting companies text. I guess
    # I could have done a search and replace, but I'd rather slightly adjust
    # some functionality I already have (i.e. parse_num) than build another
    # function to find the number of stars, store it, and then replace it with
    # empty text. 
    if parse_num(' '.join(split_posting_company), 0):
        num_stars = split_posting_company[0]
        posting_company = ' '.join(split_posting_company[1:])
        out_json_dct = gen_output(json_dct.copy(), posting_title,
                posting_location, posting_date, posting_company, num_stars)
    else:
        posting_company = ' '.join(split_posting_company)
        out_json_dct = gen_output(json_dct.copy(), posting_title,
                posting_location, posting_date, posting_company)

    out_json_dct['posting_txt'] = grab_posting_txt(driver, job, idx)
    return out_json_dct


def gen_output(json_dct, *args):
    """Prep json_dct to be stored in Mongo. 

    Add in all of the *args into the json_dct so that we can store it 
    in Mongo. This function expects that the *args come in a specific order, 
    given by the tuple of strings below (it'll hold the keys to use to store 
    these things in the json_dct). 'num_stars' isn't necessarily expected 
    to be passed in (whereas everything else is). 

    Args: 
        json_dct: dict
            Dictionary that currently stores a couple of things, to be 
            added to using *args. 
        *args: Tuple
            Holds what to add to the json_dct. 

    Return: dct
    """
    keys_to_add = ('job_title', 'location', 'date', 'company', 'num_stars')
    for arg, key in zip(args, keys_to_add):
        if arg:
            json_dct[key] = arg

    return json_dct


def grab_posting_txt(driver, job, idx):
    """Grab the job posting's actual text. 

    Args: 
        driver: Selenium webdriver
        job: Selenium WebElement
            Holds a reference to the current job the program is on. 
        idx: int
    
    Return: str (posting text)
    """

    job_link = job.find_element_by_class_name('jobLink')
    job_link.send_keys(Keys.ENTER)
    job_link.send_keys(Keys.ESCAPE)

    try:
        print(job.find_element_by_class_name('reviews-tab-link').text)
    except:
        pass

    time.sleep(random.randint(3, 7))
    texts = driver.find_elements_by_class_name('jobDescriptionContent')

    return texts[idx].text


def check_if_next(driver, num_pages):
    """Check if there is a next page of job results to grab. 

    Args: 
        driver: Selenium webdriver 
        num_pages: int
            Holds the total number of pages that the original search showed. 

    Return: bool
    """

    try:
        next_link = driver.find_element_by_xpath("//li[@class='next']")
        page_links = driver.find_elements_by_xpath(
                "//li//span[@class='disabled']")
        last_page = check_if_last_page(page_links, num_pages)
        if last_page:
            return False
        time.sleep(random.randint(3, 6))
        next_link.click()
        return True
    except Exception as e:
        print(e)
        return False


def check_if_last_page(page_links, num_pages):
    """Parse page links list. 

    Figure out if current page is the last page. 

    Args: 
        page_links: list
            Holds Selenium WebElements that refer to page links. 
        num_pages: int

    Return: bool or int
    """

    if len(page_links) == 1:
        return False
    else:
        elem1_text = page_links[0].text
        elem2_text = page_links[1].text
        if elem1_text:
            return int(elem1_text) == num_pages
        elif elem2_text:
            return int(elem2_text) == num_pages

if __name__ == '__main__':

    try:
        companies = [x for x in sys.argv][1:]
    except IndexError:
        raise Exception('Program needs one or more company names!')

    # Create a database connection object
    db = MySqlConnector(creds.DB_URL, creds.DB_USR, creds.DB_PWD)

    # Create Selenium webdriver using Chrome and chromedriver
    driver = webdriver.Chrome()

    for company in companies:

        # Navigate to Glassdoor company reviews search page
        driver.get('https://www.glassdoor.com/Reviews/index.htm')
        driver.maximize_window()

        # Find Sign In link and click it
        signInLink = driver.find_element_by_class_name("sign-in")
        signInLink.click()
        time.sleep(1)

        # Find user name and password fields and enter them
        uNameField = driver.find_element_by_id("signInUsername")
        uNameField.send_keys(creds.GLASSDOOR_USR)
        uPwdField = driver.find_element_by_id("signInPassword")
        uPwdField.send_keys(creds.GLASSDOOR_PSD)
        uPwdField.send_keys(Keys.ENTER)
        time.sleep(1)

        # Find search box, enter company name and hit enter
        titleSearch = driver.find_element_by_id('KeywordSearch')
        titleSearch.clear()
        titleSearch.send_keys(company)
        titleSearch.send_keys(Keys.ENTER)
        time.sleep(1)

        # Switch to new tab if one was opened
        driver.switch_to.window(driver.window_handles[-1])

        # Find See All Reviews link and press it
        try:
            allReviewsLink = driver.find_element(By.XPATH, "//a[@class='eiCell cell reviews']")
            allReviewsLink.click()
            time.sleep(1)
        except Exception as e:
            print(e)
            print("Skipping company!!")
            continue

        # While there are more pages
        hasNextPage = True
        while hasNextPage:
            reviews = pd.DataFrame(columns=['company', 'datetime', 'summary', 'pro', 'con', 'md5'])

            # Press all the Show More links
            for link in driver.find_elements(By.XPATH, "//span[@class='link moreLink']"):
                ActionChains(driver).move_to_element(link).click(link).perform()
                time.sleep(.1)

            # Get the review summaries
            reviews.summary = [x.text.encode() for x in driver.find_elements_by_class_name("reviewLink")]

            # Get pros skipping first one because it's featured
            reviews.pro = [x.text.encode() for x in driver.find_elements_by_class_name("pros")][1:]

            # Get Cons skipping first one because it's featured
            reviews.con = [x.text.encode() for x in driver.find_elements_by_class_name("cons")][1:]

            # Create a unique hash to identify each review
            reviews.md5 = [hashlib.md5(x+y+z).hexdigest() for x, y, z in
                           reviews[['summary', 'pro', 'con']].values]

            # Add company name and the datetime
            reviews.company = company
            reviews.datetime = datetime.datetime.now()

            # Add data to database
            db.write_table("glassdoor", reviews)

            # TODO: Make sure duplicates aren't entered in db

            # TODO: Keep current companies reviews in memory and check for duplicates

            # TODO: Skip pages already scraped

            # TODO: Setup secondary Glassdoor account

            # TODO: Optimize for speed

            # Get next link and press it
            try:
                driver.find_element_by_class_name("next").click()
            except Exception as e:
                hasNextPage = False
                print(e)


    driver.close()

# File snapshot =((TakesScreenshot)driver).getScreenshotAs(OutputType.FILE);  javascript example of screenshot