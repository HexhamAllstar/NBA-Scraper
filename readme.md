# NBA-Scraper
This python code is intended to allow somebody to create a local database of all
NBA matches this season, including the final result and the player specific box scores.

To run this code do the following:
1. Clone the repository and create a virtual environment with the packages specified in requirements.txt
2. Download geckodriver.exe for your version of firefox into the same directory.
3. Open scraper_run.py and modify the timedelta and hard-coded date in the while loop to choose the dates to get data between. The code will not download duplicate data.
4. Run scraper_run.py. **Warning this can take several hours if you are scraping the whole season**.
5. Sometimes the geckodriver will stop responding, in which case it won't find any games. If this happens then just change the timedelta and re-run the code from the last good date.
