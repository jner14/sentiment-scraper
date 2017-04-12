"""
A module for scraping Glassdoor for company reviews.
"""
import os
import hashlib
import time
import datetime
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from general_utilities.mysql_connection import MySqlConnector
import pandas as pd
import creds

# TODO: Consider saving company name from page to cross reference accuracy of searches
# TODO: Consider adding ability to skip pages already scraped based on how many entries exist in db

os.environ["PATH"] = "chromedriver"
Keys = webdriver.common.keys.Keys
By = webdriver.common.by.By
ActionChains = webdriver.common.action_chains.ActionChains
REVIEW_FIELDS = ['company', 'datetime', 'summary', 'pro', 'con', 'md5']


def _new_search(driver, company_name):
    # Navigate to Glassdoor company reviews search page
    driver.get('https://www.glassdoor.com/Reviews/index.htm')

    # Find search box, enter company name and hit enter
    titleSearch = driver.find_element_by_id('KeywordSearch')
    titleSearch.clear()
    titleSearch.send_keys(company_name)
    titleSearch.send_keys(Keys.ENTER)
    time.sleep(1)


def scrape_glassdoor(companies, max_per_comp=1000, debug_mode=False):
    pageCnt = round(max_per_comp // 10)

    # Create Selenium webdriver using Chrome and chromedriver
    driver = webdriver.Chrome()
    # driver.set_page_load_timeout(10)

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

    for company in companies:

        # Start a new search
        _new_search(driver, company)

        # Check for extra tabs and close them
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            # If not a search page and not the company page
            if 'SRCH' not in driver.current_url and company.split()[0].lower() not in driver.current_url.lower():
                # Close tab unless it is the last, in which case, search again
                if len(driver.window_handles) > 1:
                    driver.close()
                else:
                    _new_search(driver, company)

        # Switch to search tab
        driver.switch_to.window(driver.window_handles[0])

        # Find See All Reviews link and press it
        try:
            allReviewsLink = driver.find_element(By.XPATH, "//a[@class='eiCell cell reviews']")
            allReviewsLink.click()
            time.sleep(1)
        except NoSuchElementException as e:
            print(e)
            print("Skipping company!! Possibly because it was not found")
            continue

        try:
            # Get company reviews url
            companyURL = driver.current_url[:-4]
        except Exception as e:
            # selenium.common.exceptions.TimeoutException: Message: timeout
            print(e)

        # While there are more pages
        companyReviews = pd.DataFrame(columns=REVIEW_FIELDS)
        escape = False
        for i in range(2, pageCnt + 2):
            skipNext = False
            try:
                reviews = pd.DataFrame(columns=REVIEW_FIELDS)

                # Press all the Show More links
                for link in driver.find_elements(By.XPATH, "//span[@class='link moreLink']"):
                    ActionChains(driver).move_to_element(link).click(link).perform()
                    time.sleep(.1)

                # Get the review summaries
                reviews.summary = [x.text.encode() for x in driver.find_elements_by_class_name("reviewLink")]

                # Get pros skipping first one because it's featured
                reviews.pro = [x.text.encode() for x in driver.find_elements_by_class_name("pros")][-len(reviews):]

                # Get Cons skipping first one because it's featured
                reviews.con = [x.text.encode() for x in driver.find_elements_by_class_name("cons")][-len(reviews):]

                # Create a unique hash to identify each review
                reviews.md5 = [hashlib.md5(x+y+z).hexdigest() for x, y, z in reviews[['summary', 'pro', 'con']].values]

                # Add company name and the datetime
                reviews.company = company
                reviews.datetime = datetime.datetime.now()

                # Add to company reviews
                companyReviews = pd.concat([companyReviews, reviews])

            except ValueError as e:
            # ran out of pages  Length of values does not match length of index
                print(e)

            try:

                reviewCount = 0
                # TODO: Try to get reviewCount
                reviewCount = int(driver.find_element(
                    By.XPATH, "//div[@class='padTopSm margRtSm margBot minor']").text.split()[0].replace(',', ''))

                # Exit loop and start search for new company
                if (i - 1) * 10 > reviewCount > 0:
                    break

            except NoSuchElementException as e:
                # Log back in?


                print(e)

            if escape:
                break

            if skipNext:
                continue

            # Get next page url and navigate to it
            nextPageUrl = companyURL + "_P{}.htm".format(i)
            driver.get(nextPageUrl)

        # Add data to database, grouping by md5 to remove duplicates
        companyReviews = companyReviews.groupby('md5', as_index=False).first()
        if debug_mode:
            print(companyReviews)
        else:
        # try:
            # Create a database connection object and write to glassdoor table
            db = MySqlConnector(creds.DB_URL, creds.DB_USR, creds.DB_PWD)
            db.write_table("glassdoor", companyReviews)
            print("Successfully saved {} to the database".format(company))
        # except Exception as e:
        #     print(e)
        #     companyReviews.to_csv("{}-{}".format(company, datetime.datetime.now()))
        #     sys.exit()

    # driver.close()
