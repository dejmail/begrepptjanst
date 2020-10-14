from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select, WebDriverWait

import unittest
import random
from random import randint
from datetime import datetime, timedelta
import string
from lorem_text import lorem

from pdb import set_trace

def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

def return_random_date_between_dates():
    
    start_date = datetime.strptime('2000-01-01', '%Y-%m-%d')
    end_date = datetime.now()
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    random_date = start_date + timedelta(days=random_number_of_days)
    print(random_date)
    return random_date.year, random_date.month, random_date.day

class NewSearch(unittest.TestCase):
    def setUp(self):
        
        chrome_options = Options()
        chrome_options.add_argument("--disable-extensions")
        self.browser = webdriver.Chrome(executable_path="C:/Users/liath1/coding/chromedriver/chromedriver.exe",
                                        chrome_options=chrome_options)
        self.browser.implicitly_wait(2)
        # open the base page
        self.browser.get('http://localhost:8000')

    def tearDown(self):
        self.browser.quit()
    
    def test_open_base_page_and_perform_search(self):
        

        # Make sure the browser title is correct
        self.assertIn('VGR Informatik - OLLI Begreppstjänst', self.browser.title)
        # Find the search input
        inputbox = self.browser.find_element_by_id('user-input')
        inputbox.send_keys('patient')
        inputbox.send_keys(Keys.ENTER)
        
        search_results_table = self.browser.find_element_by_id('definition_table')
        rows = search_Results__table.find_elements_by_tag_name('tr')

        cols_header = rows[0].find_elements_by_tag_name("td")
        assert rows[0].text == 'Term English Term Definition Synonym', 'Row headers have changed'

        cols_table_body = rows[1].find_elements_by_tag_name("td")
        assert cols_table_body[0].text == 'patient', '"patient" should be in the first column on the first row'
        
    def test_open_beställ_begrepp(self):
        
        # open the base page
        #self.browser.get('http://localhost:8000')

        # Find the search input, enter a random string
        inputbox = self.browser.find_element_by_id('user-input')
        inputbox.send_keys(get_random_string(8)+ '-' + datetime.now().strftime("%Y-%m-%d") + '-test')
        inputbox.send_keys(Keys.ENTER)

        self.browser.find_element_by_xpath('//button[text()="Efterfråga begrepp"]').click()

        # find the context field, and enter some random text
        context_field = self.browser.find_elements_by_id('id_kontext')
        context_field[0].send_keys(lorem.paragraph())

        # find workstream field and select a random choice from the dropdown
        workstream = Select(self.browser.find_element_by_id('id_workstream'))
        workstream.select_by_index(randint(0, len(workstream.options) -1))

        # select a random date for when the task should be completed by
        year, month, day = return_random_date_between_dates()
        self.browser.find_element_by_xpath('//*[@id="id_önskad_datum"]').click()
        self.browser.find_element_by_xpath('//*[@id="id_önskad_datum"]').send_keys(year)
        self.browser.find_element_by_xpath('//*[@id="id_önskad_datum"]').send_keys(Keys.TAB)
        self.browser.find_element_by_xpath('//*[@id="id_önskad_datum"]').send_keys(month)
        self.browser.find_element_by_xpath('//*[@id="id_önskad_datum"]').send_keys(day)

        # submit a name        
        name_field = self.browser.find_elements_by_id('id_namn')
        test_name = get_random_string(8)+'_testname'
        name_field[0].send_keys(test_name)
        
        # submit an email addrress
        epost_field = self.browser.find_elements_by_id('id_epost')
        epost_field[0].send_keys(get_random_string(8)+'@hairyhat.se')

        set_trace()
        # submit either skype or telephone number
        contact_details = (randint(10), get_random_string(7))
        contact_field = self.browser.find_elements_by_id('id_telefon')
        contact_field[0].send_keys(random.choice(contact_details))

        # attach a file
        attach_file = browser.find_element_by_xpath('//*[@id="id_file_field"]').click()

        set_trace()
if __name__ == '__main__':
    unittest.main(warnings='ignore')
    set_trace()
    