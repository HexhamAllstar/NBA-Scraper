from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
from string import ascii_lowercase

url = "http://uk.global.nba.com/playerindex/"

links = []
playerNames = []

"""code to go through each letter of the alphabet, collect each player name on that letter's page and then
store it in a list"""
options = Options()
options.add_argument("--headless")
driver = webdriver.Firefox(firefox_options=options, executable_path="geckodriver.exe")
driver.get(url)


for letter in ascii_lowercase:
    # code here to change the page based on the current letter

    soup = BeautifulSoup(driver.page_source, "html.parser")
    button = driver.find_element_by_xpath("//*[text()='" + letter + "']")
    button.click()


    elems = soup.find_all('a', "ng-hide")

    for elements in elems:
        links.append(elements.attrs['href'])

for link in links:
    tempName = link.split("/")[-1]
    playerNames.append(" ".join(tempName.split("_")))

print(playerNames[50:75], links[50:75])
driver.close()
