import pandas as pd
import sys
from glassdoor.glassdoor_scraper import scrape_glassdoor


def usage_error():
    print("USAGE")
    print("-----")
    print("sentiment_scraper.py -l/-f (reviews per company) (company/companies/file path)")
    print("\nEXAMPLES")
    print("--------")
    print("sentiment_scraper.py -l 1000 IBM")
    print('sentiment_scraper.py -l 1000 IBM "Home Depot" "Sherwin Williams"')
    print('sentiment_scraper.py -f 1000 "C:\Sentiment Project\companies.csv"')
    sys.exit()


if __name__ == "__main__":
    debugMode = False
    companies = []
    args = []
    maxReviews = 0

    # Get command line args
    try:
        args = [x for x in sys.argv][1:]
    except IndexError:
        usage_error()

    # Make sure at least 3 parameters are present
    if len(args) >= 3:

        # Enable debug mode if -d is passed
        if '-d' in args:
            print("DEBUG MODE ENABLED. REVIEWS WILL NOT BE SAVED TO THE DATABASE")
            debugMode = True
            args.remove('-d')

        # Get the first parameter which should be the input type
        inputType = args.pop(0)

        # Get the second parameter which should be the maxReviews per company
        try:
            maxReviews = int(args[0])
            args.pop(0)
        except ValueError:
            print("CRITICAL ERROR: '{}' is not a valid value for the max reviews per company parameter!!".
                  format(args[0]))
            usage_error()

        # If the input type is not valid then indicate a usage error
        if inputType not in ['-f', '-l']:
            usage_error()

        # If the input type od -l for list of companies then assume all remaining args are companies
        elif inputType == '-l':
            companies = args

        # If the input type is -f then load companies form csv file
        elif inputType == '-f':
            try:
                companies = list(pd.read_csv(args[0]).iloc[:, 0])
            except FileNotFoundError:
                print("CRITICAL ERROR: '{}' is not a valid file path!!".format(args[0]))
                print('Example File Path: "C:\Folder 1\Folder 2\File.csv"')
                sys.exit()
    else:
        usage_error()

    scrape_glassdoor(companies, max_per_comp=maxReviews, debug_mode=debugMode)

    print("Finished")
