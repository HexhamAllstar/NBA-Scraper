from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from string import ascii_lowercase, digits
from datetime import datetime
import time
import pandas as pd

pd.options.mode.chained_assignment = None  # default='warn'

def get_boxscore_links(date, driver):
    """This function takes in a datetime object representing the date of interest
    and returns a list of links to all boxscores from that day (if there were any games).
    If the code notices that there are any games in progress for that day, it will not return
    anything because this could lead to games being missed"""

    # common part of the url for all scores pages
    base_url = "http://stats.nba.com"

    # get the day, month and year of the required date and turn into strings
    day = date.strftime('%d')
    month = date.strftime('%m')
    year = date.strftime('%Y')

    # create the url of the scores page for the given day
    url = base_url + '/scores/' +  month + '/' + day + '/' +  year

    driver.get(url) # point the selenium driver to the score page
    timeout=5

    # check that specific element has loaded before getting soup.
    try:
        element_present = EC.presence_of_element_located((By.XPATH, "//*[@class='linescores']"))
        WebDriverWait(driver, timeout).until(element_present)
    except TimeoutException:
        print("Website timed out, check your connection to the internet.")

    #create a soup of the displayed elements
    soup = BeautifulSoup(driver.page_source, "html.parser")

    links = [] # initialise empty list
    # find all of the <a> elements that have text Box score
    # these are buttons on the page that have a relative link stored
    # in their href attribute.
    for a in soup.find_all('a', text="Box Score"):
        # for each <a> element found, take the href and append it to links
        links.append(a['href'])
    return links

def get_boxscore(boxscore_url, driver):
    """This function takes in a string of the format '/game/GAMEID/'
    where GAMEID  is a 10 digit unique ID for the game. It returns a
    representation of the boxscore for that game."""

    # common part of the url for all scores pages
    base_url = "http://stats.nba.com"

    # create the url of the page for the given game
    url = base_url + boxscore_url

    driver.get(url) # point the selenium driver to the score page

    #create a soup of the displayed elements
    passed = False
    while passed == False:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        divs = soup.find_all('div', "game-summary-team__name")
        # get team names from div with the above class
        try:
            teamNames=[]
            for div in divs:
            # The actual text is stored in an <a> tag that is the child
            # of the divs found above.
                teamNames.append(div.contents[0].text)
            passed = True
        except ValueError:
            time.sleep(3)

    passed = False
    while passed == False:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        divs = soup.find_all('div',"game-summary-team__right")
        # get scores from above class
        scores = []
        try:
            for div in divs:
                scores.append(''.join(c for c in div.text if c in digits))
            passed = True
        except ValueError:
            time.sleep(3)

    # get game date from div above
    passed = False
    while passed == False:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        divs = soup.find_all('div','game-summary__date')
        try:
            gamedate = divs[0].text
            gamedate = datetime.strptime(gamedate, '%b  %d, %Y')
            passed = True
        except ValueError:
            time.sleep(3)

    # get gameid from the provided url
    gameid = boxscore_url.split('/')[-2]

    # create a dataframe for the game result
    result = [gameid, gamedate, teamNames[0], scores[0], teamNames[1], scores[1]]
    result = pd.DataFrame(result).T
    result.columns = ['GameID','GameDate','HomeTeam','HomeScore','AwayTeam','AwayScore']

    # find the boxscore tables on the page
    passed = False
    while passed == False:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        tables = soup.find_all('div','nba-stat-table__overflow')

        try:
            tables = soup.find_all('div','nba-stat-table__overflow')
            homedict = get_table_contents(tables[0])
            awaydict = get_table_contents(tables[1])
            passed = True
        except IndexError:
            time.sleep(2)

    #turn the dictionaries into dataframes
    columns = ['Player Name','Min','FGM','FGA','FG%','3PM','3PA','3P%','FTM','FTA' \
    , 'FT%','OREB','DREB','REB','AST','TOV','STL','BLK','PF','PTS','+/-']

    home_df = pd.DataFrame.from_dict(orient='index', data=homedict)
    home_df.columns = columns
    away_df = pd.DataFrame.from_dict(orient='index', data=awaydict)
    away_df.columns = columns

    # add column indicating starter and teamNamesand gameid
    home_df['Team'] = teamNames[0]
    away_df['Team'] = teamNames[1]
    home_df['Starter'] = 0
    home_df['Starter'][home_df.index < 5] = 1
    away_df['Starter'] = 0
    away_df['Starter'][away_df.index < 5] = 1
    home_df['GameID'] = gameid
    away_df['GameID'] = gameid

    return(result, home_df, away_df)

def get_table_contents(table):
    """This function takes in html code for a table on the boxscore
    page of an NBA game. It returns a dictionary that uses the row number
    as the keys and the items are the table rows"""

    # in the first table (home team), find all rows ('tr') within
    # body of table ('tbody')
    trows = table.tbody.find_all('tr')
    tabledict = {} # empty dict
    # for each row in the table body
    for index, row in enumerate(trows):
        # find the columns
        cols = row.find_all('td')
        # empty list to store text from each column
        rowtext = []
        # for each column
        for col in cols:
            # append the text of the column to rowtext
            coltext = col.text
            rowtext.append(coltext)
        # the first 5 players have their starting position appended
        # to their name i.e. 'Lebron James F'. We remove this.
        if index in range(5):
            newname = ''
            for substring in rowtext[0].split(' ')[:-1]:
                newname += substring + ' '
                rowtext[0] = newname[:-1]
        # players not in the starting 5 have a space at the append
        # i.e. 'Lebron James ', we remove this.
        else:
            rowtext[0] = rowtext[0][:-1]

        # store the row in dictionary with key as the position in the table
        tabledict[index] = rowtext
    # return the dictionary
    return tabledict
