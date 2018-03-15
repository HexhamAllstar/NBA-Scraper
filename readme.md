# NBA-Scraper
This python code is intended to allow somebody to create a local database of all
NBA matches this season, including the final result and the player specific box scores.

To run this code do the following:
1. Clone the repository and create a virtual environment with the packages specified in requirements.txt
2. Download geckodriver.exe for your version of firefox into the same directory.
3. Open an Ipython console and import scraper_run.py (or specifically the run_scraper function within). Run run_scraper(start_date, end_date) where start_date and end_date are strings of the format "dd/mm/yyyy" that specify the dates that you want data between. Start_date should be chronologically earlier than end_date. **Warning: If you scrape the entire season it will take well over an hour**
4. The script will then grab the relevant data and store it in a local SQL database named NBA_data.db. This repository has the database up to date as of the last commit incase you do not want to wait for the scraper to run.
5. backend.py contains some simple functions for retrieving data from the database. E.g. In a Jupyter notebook, use data = backend.retrieve_all_results() to get all of the team score data and data = backend.retrieve_all_boxscores() to get the player specific data.

Note: Sometimes Selenium will hang. If this happens then exit the script and simply run again with the same dates. The script will not insert duplicate data.
