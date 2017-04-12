# Sentiment Scraper

This is a web-scraper to scrape
[Glassdoor](https://www.glassdoor.com/index.htm) and in the future possibly other websites for company reviews.

## Setup

In addition to downloading or cloning the repo you must also:

#### Install Chome and Python 3.6 64bit
 - Requires Chrome.  The chromedriver, which is used to control it, is already included.
 - Requires Python 3.6 64bit.  Might work with other versions of Python 3, but they are untested.

#### Install Python Packages
 - pandas
 - selenium
 - numpy
 - beautifulsoup4
 - SQLAlchemy

#### Finally
Open creds.py in notepad or an IDE of your choice and enter your username and password for glassdoor and any other websites that will be scraped.  Also enter the database URL, user name, and password.

## Usage

```python
python sentiment_scraper.py -l/-f (reviews per company) (company/companies/filepath)
```

#### Examples

 - If the '-l' (list) input type parameter is given, any number of companies can be passed if separated by spaces.
```python
python sentiment_scraper.py -l 1000 IBM
python sentiment_scraper.py -l 1000 IBM Microsoft Google
```
 - Make sure to put quotes around anything that has spaces whether it is a company name or file path.
 ```python
python sentiment_scraper.py -l 1000 IBM "Home Depot" "Sherwin Williams"
```
 - If the csv file containing the list of companies is present in the sentiment-scraper directory then only the file name is required, but otherwise the complete path is necessary.
```python
python sentiment_scraper.py -f 1000 companies.csv
python sentiment_scraper.py -f 1000 "C:\Sentiment Project\companies.csv"
```

 - Also note, that when loading companies from a csv file make sure that the first row is a header and that the company names are in the first column.
