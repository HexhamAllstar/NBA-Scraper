import scraper_funcs
import backend
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

options = Options()
options.add_argument("--headless") # create headless option so browser doesn't open on screen.
# create a firefox selenium driver
driver = webdriver.Firefox(firefox_options=options, executable_path="geckodriver.exe")
# get todays date
date = datetime.now()
# use timedelta if you want to start at a specific date
date = date - timedelta(days=0)

# initialise a counter so we can reopen driver every now and then
# I have found that this improves speed and stability
loop_counter = 0

# loop while the date is later than 17th Oct 2017, first day of the season
while date >= datetime.strptime("17/10/2017", "%d/%m/%Y"):

    if (loop_counter % 20) == 0: # every 20 loops close and reopen driver
        driver.close()
        driver = webdriver.Firefox(firefox_options=options, executable_path="geckodriver.exe")
    else:
        pass

    # get all results from the database to check if the current date is already in there
    results = backend.retrieve_all_results()
    if not results.empty:
        dates = results['GameDate']
        dates = dates.apply(lambda d:datetime.strptime(d.split(' ')[0], '%Y-%m-%d').date())
        dates = dates.values
    else:
        dates = []

    # compare current date with list of dates in the results df
    # if it's already there then skip to avoid duplicates
    if date.date() in dates:
        datetest = (date.date() == dates)
        print(date.strftime('%d/%m/%Y') + ' is already in the database.')
        # create a count of how many games are stored in the database vs how many there should be on this date.
        print('There are ' + str(sum(datetest)) + ' games on this date in the database.')
        links = scraper_funcs.get_boxscore_links(date, driver)
        print('There should be ' + str(len(links) -1) + ' games. Consider deleting this date and redownloading if these do not match.')
    # if the current date isn't in the database, go grab the data and insert it
    else:
        # get a list of links for all boxscore buttons on the scores page for the current day
        links = scraper_funcs.get_boxscore_links(date, driver)
        # the first link is always blank, so length 1 means no real links
        if len(links) == 1:
            print(date.strftime('%d/%m/%Y') +  ' : No games played (or no games played yet).')
        else:
            # remove blank from front of list of links
            print(date.strftime('%d/%m/%Y') + ' : ' + str(len(links) - 1) +  ' game(s) played.')
            print('Scraping ....')
            links = links[1:]
            #iterate through the boxscore links, adding resulting dataframes to our database
            driver2 = webdriver.Firefox(firefox_options=options, executable_path="geckodriver.exe")
            scraper_funcs.scrape_and_add(links, driver2) # do the scraping and add results to db
            driver2.close() # we use a new driver for every date, reduces crashing
            
    # once we've added all of the boxscores for the current date, remove 1 from the datetime
    date = date - timedelta(days=1)


# after all of the loops, close the webdriver
driver.close()
