from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from io import StringIO
import pandas as pd


class Scraper:

    columns = ['bib_number', 'name', 'finish_time' ,'hyper_link']

    @staticmethod
    def __setup_driver() -> webdriver:
        """
        Set up and return a Chrome WebDriver instance
        """

        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver


    def __init__(self):
        self.driver = self.__setup_driver()

    def __load_and_parse_page(self, url: str, test_section: str = 'section.section-main' ) -> BeautifulSoup:
        """ 
        Loads and parses the page of the url 
        """
        
        self.driver.get(url)
    
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, test_section))
        )
    
        return BeautifulSoup(self.driver.page_source, 'html.parser')


    def scrape_runner_data(self, url: str) -> pd.DataFrame:
        """
        Scrape data for all the runners from page format: 
        https://brighton.r.mikatiming.com/2025/?event=BRMA&page=1&pid=list
        """

        soup = self.__load_and_parse_page(url)

        runner_data = pd.DataFrame()

        for row in soup.select_one('ul.list-group.list-group-multicolumn').select('li.list-group-item.row')[1:]:

            try:
            
                bib_number = row.find("div",{"class":'list-field type-field'}).text.replace('Bib Number', '').strip()
                name = row.select_one('h4').select_one('a').text
                finish_time =  row.find("div",{"class":'right list-field type-time'}).text.replace('Finish', '').strip()
                hyperlink =  row.select_one('h4').select_one('a').get('href')

                runner_data = pd.concat([runner_data, pd.DataFrame(data=[[bib_number, name, finish_time, hyperlink]] , columns=columns)], ignore_index=True)
            except:
                print(f'Warning: scraper incompatible page for page: {url}')
                continue

        return runner_data
    

    def scrape_individual_data(self, url: str) -> pd.DataFrame:
        """ 
        Scrape data for an individual runner from page of format:
        https://brighton.r.mikatiming.com/2025/?content=detail&fpid=list&pid=list&idp=9TGEELFR267AA&lang=EN_CAP&event=BRMA&&search_event=BRMA
        """

        soup = self.__load_and_parse_page(url)

        #use a try block since not everyone turned up and has split times associated.
        try:
            #retrieve split times table
            table = soup.select_one('table.table.table-condensed.table-striped')
            result = pd.read_html(StringIO(str(table)))[0]

            #add charity name
            charity = soup.select_one('table.table.table-condensed').find("tr" , { "class" : "f-company"}).text.replace('Charity', '').strip()
            result['charity'] = charity

        except:
            return pd.DataFrame()

        return result