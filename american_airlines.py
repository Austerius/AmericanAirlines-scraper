"""
Contains AmericanAirlines class, where help methods and logic for scraping data
from American Airlines web site are implemented. (all for educational purposes only!)

Check '__init__()' docstring for required parameters. To start scraping - just create instance of AmericanAirlines
and use 'run()' method. Example:
    scraper = AmericanAirlines('mia', 'sfo', '02/12/2018', '02/15/2018')
    scraper.run()
**Note**: this class does little about input data validation, so use 'aa_manager.py' (or your own script) to
perform data validation.
"""
import time
import os
import json

from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.common.keys import Keys

from bs4 import BeautifulSoup


class AmericanAirlines:

    def __init__(self, departure_airport, destination_airport, departure_date, return_date=None,
                 sleeptime=3, trip_type="round trip",
                 airline="AA", price="lowest", passengers=1,
                 passengers_type=None, daytime="all day", file_path="", file_format="json"):
        """

        :param departure_airport: code of airport from which you ant to depart (3 characters string)
        :param destination_airport: destination airport code (3 characters string)
        :param departure_date: date of departure - string with this format 'mm/dd/yyyy' (example: 02/10/2018)
        :param return_date: date of return - string 'mm/dd/yyyy' (example: 02/17/2018). Only needed,
                            when trip_type="round trip"
        :param sleeptime: wait time to download starting page
        :param trip_type: type of the trip
                                            - "round trip" - trip to chosen destination and back
                                            - "one way" - trip to chosen destination
        :param airline: service provider
                                        - AA - Americans Airlines
                                        - ALL - all providers
        :param price: search by price, default value - "lowest"(doesnt have other options for now)
        :param passengers: number of passengers(for now supporting only one passenger)
        :param passengers_type: dictionary of passengers grouped by age corresponding to passengers total number;
                                {1: "adult", 2: "child"} etc. (Not supported for now).
        :param daytime: return available flights only from chosen time interval(evening, morning). For now,
                        class support only one interval - 'all day'
        :param file_path: full path to directory, where you want to save flights information(default location -
                          - current directory)
        :param file_format: format in which data would be saved to a file. Chose from next option:
                                                                                                   -"json"

        """

        # making Firefox work in headless mode
        firefox_options = Options()
        firefox_options.add_argument('-headless')
        # setting Firefox to use tor proxies
        # profile = webdriver.FirefoxProfile()
        # profile.set_preference('network.proxy.type', 1)
        # profile.set_preference('network.proxy.socks', '127.0.0.1')
        # profile.set_preference('network.proxy.socks_port', 9150)

        self.sleeptime = sleeptime
        self.trip_type = trip_type
        self.airline = airline
        self.price = price
        self.passengers = passengers
        self.passengers_type = passengers_type
        self.daytime = daytime
        self.departure = departure_airport
        self.destination = destination_airport
        self.departure_date = departure_date
        self.return_date = return_date
        self.file_path = file_path
        self.file_format = file_format

        self.driver = webdriver.Firefox(firefox_options=firefox_options)
        # site has bot protection and easy detect 'default cromedriver'so we using firefox for now
        # self.driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, chrome_options=chrome_options)
        self.driver.get("https://www.aa.com/booking/find-flights")  # opening site's search window
        time.sleep(self.sleeptime)

    def __del__(self):
        self.driver.close()

    def press_accept_cookies(self):
        """ Method for pressing 'accept button'.
        When we open site for the first time - they'll ask to accept cookies polices in separate pop-up window.
        """
        try:
            self.driver.find_element_by_xpath('//div[@aria-describedby="cookieConsentDialog"]//button[@id="cookieConsentAccept"]').click()
            time.sleep(self.sleeptime)
        except NoSuchElementException as e:
            print(e.msg)

    def _validate_file_format(self):
        if self.file_format.lower() != "json":
            return False
        else:
            return True

    def _one_way_trip(self):
        if self.trip_type.lower() == ("one way" or "oneway"):
            return True
        else:
            return False

    def _round_trip(self):
        if self.trip_type.lower() == ("round trip" or "roundtrip"):
            return True
        else:
            return False

    def select_trip_type(self):
        """ Method for selecting trip type in search box.
            Can be "round trip" or "one way" trip
        """
        if self._round_trip():
            self.driver.find_element_by_xpath('//li[@aria-controls="roundtrip"]/a').click()
            time.sleep(0.5)
        if self._one_way_trip():
            self.driver.find_element_by_xpath('//li[@aria-controls="oneway"]/a').click()
            time.sleep(0.5)

    def select_airline(self):
        """ Method for selecting airline provider from search form.
            Can be "aa" - which represent American Airlines or "all" - which represent all airlines
        """
        if self.airline.lower() == "aa":
            self.driver.find_element_by_xpath('//select[@id="airline"]/option[@value="AA"]').click()
            time.sleep(0.5)
        if self.airline.lower() == "all":
            self.driver.find_element_by_xpath('//select[@id="airline"]/option[@value="ALL"]').click()
            time.sleep(0.5)

    def select_time_of_day(self, form):
        """ Method for selecting time interval("all day" for now) in which available flights will be returned"""
        form.find_element_by_xpath('.//option[@value="120001"]').click()

    @staticmethod
    def _clear_for_input(input_field, n):
        """ Method for clearing input field from default data
            "input_field" - selenium object located with webdriver.find method
            'n' - number of characters to be deleted
        """
        for i in range(0, n):
            input_field.send_keys(Keys.BACKSPACE)

    def fill_from_form(self):
        """ Here we filling form 'from' with appropriate airport code"""
        airport = self.driver.find_element_by_xpath('//input[@id="segments0.origin"]')
        # clearing form from default text
        self._clear_for_input(airport, 4)
        airport.send_keys(self.departure)

    def fill_destination_form(self):
        """ Here we filling destination form ith appropriate airport code"""
        airport = self.driver.find_element_by_xpath('//input[@id="segments0.destination"]')
        airport.send_keys(self.destination)

    def fill_date_form(self, selector, date):
        """ Here we filling departure date form with appropriate date"""
        self._clear_for_input(selector, 15)
        selector.send_keys(date)

    def click_search(self):
        """Pressing search form "search" button"""
        self.driver.find_element_by_xpath('//button[@id="flightSearchSubmitBtn"]').click()
        self._wait_to_load()

    def check_for_input_error(self):
        """ Here we checking if error box appeared and if so - terminated execution"""
        self.driver.refresh()
        try:
            self.driver.find_element_by_xpath('//div[@class="message-error margin-bottom"]')
            raise Exception("Search field was filled wrong")
        except NoSuchElementException:
            pass

        try:
            self.driver.find_element_by_xpath('//head/meta[@name="ROBOTS"]')
            # text = self.driver.find_element_by_xpath('//body//div[@class="outerContainer"]/p[1]').text
            # if text.strip() == "We're working on our site":
            raise Exception("Bot was detected!")
        except NoSuchElementException:
            pass

    def _wait_to_load(self):
        """ private method for waiting until 'loading' indicator gone"""
        time.sleep(0.5)
        # initializing timer for 10 sec (means: don't ait for page to load if its tale more than 10 sec)
        timer = time.time() + 10
        while True:
            try:
                # this is loading indicator
                self.driver.find_element_by_xpath('//div[@class="aa-busy-module"]')
                if time.time() > timer:
                    break
                time.sleep(0.5)
            except NoSuchElementException:
                break
        time.sleep(0.5)

    def fully_load_results(self):
        """ Here we trying to load results, hidden by 'show more' button/link """
        # initial wait to load a result page
        time.sleep(self.sleeptime)
        while True:
            try:
                self.driver.find_element_by_xpath('//a[@class="showmorelink"]').click()
                time.sleep(0.2)
            except (NoSuchElementException, ElementNotInteractableException):
                break

    def click_on_round_trip(self):
        self.driver.find_element_by_xpath('//button[@data-triptype="roundTrip"]').click()
        self._wait_to_load()

    def parse_page(self):
        """Here we scraping flights information from 'search results' page"""
        flights_list = []
        bs = BeautifulSoup(self.driver.page_source, "html.parser")
        # getting all flight available
        flights_block = bs.select("li.flight-search-results.js-moreflights")
        for flight in flights_block:
            # getting departure and arrival time
            departure_time = flight['data-departuretime']
            arrival_time = flight['data-arrivaltime']
            # getting information about amount of stops
            try:
                stops = flight.select_one("div.span3 div.flight-duration-stops a.text-underline").get_text()
                stops = stops.strip()
                temp = stops.split("\n")
                stops = temp[0]
            except AttributeError:
                stops = "Nonstop"

            # getting flight number and airplane model
            flight_numbers_models = []
            flight_numbers = flight.select("span.flight-numbers")
            plane_model = flight.select("span.wrapText")
            for number, name in zip(flight_numbers, plane_model):
                temp = {"number": (number.get_text()).strip(),
                        "airplane": (name.get_text()).strip(),
                        }
                flight_numbers_models.append(temp)

            # getting lowest price
            lowest_price = flight['data-tripprice']
            # for the case, when we need to book ticket directly at airport
            if lowest_price == "9999999999":
                lowest_price = "N/A"
            # dictionary with information about single flight
            flight_info = {"depart": departure_time,
                           "arrive": arrival_time,
                           "stops": stops,
                           "price": lowest_price,
                           "details": flight_numbers_models
                           }
            flights_list.append(flight_info)
            # # print debugging info
            # print("Depart at: {}     Arrive at: {}".format(departure_time, arrival_time))
            # print("Stops: {}".format(stops))
            # print("Lowest price: ${}".format(lowest_price))
            # print("Flight details:")
            # for plane in flight_numbers_models:
            #     print(plane)
            # print("-"*80)
        return flights_list

    @staticmethod
    def _generate_file_name(departure, destination, date, file_format):
        """ Private method for generating unique file names
            :param departure: - airport code from where we departure
            :param destination: - code of destination airport
            :param date: - date of departure
            :param file_format: - format of the file we will save or data to
        """
        month, day, year = date.split("/")
        time_string = time.strftime("%H%M%S")
        return departure + "_" + destination + year + "-" + month + "-" + day + "-" + time_string + "." + file_format

    def save_to_json(self, filename, list_of_dict):
        """ Method to save scraped data to .json file
            :param filename: unique file name generated by ::method::**_generate_file_name**
            :param list_of_dict: scraped data, returned by ::method::**parse_page**
        """
        name = os.path.join(self.file_path, filename)
        with open(name, 'w') as file:
            json.dump(list_of_dict, file, indent=2)

    # def _get_my_ip(self):
    #     self.driver.get('https://checkmyip.com/')
    #     my_ip = self.driver.find_element_by_xpath('//tr[1]/td[2]').text
    #     print("My current ip was: {}".format(my_ip))

    def run(self):
        """Here we executing scraping logic"""
        if not self._validate_file_format():
            raise ValueError("Unsupported file format for saving data!")
        self.press_accept_cookies()
        self.select_trip_type()
        self.select_airline()
        # setting time interval and departure/arrival dates
        if self._round_trip():
            # checking if we have return date filled:
            if self.return_date is None:
                raise ValueError("Return date must be filled!")

            # here we selecting 'time interval' form
            form1 = self.driver.find_element_by_xpath('//select[@id="segments0.travelTime"]')
            self.select_time_of_day(form1)
            depart_form = self.driver.find_element_by_xpath('//input[@id="segments0.travelDate"]')
            self.fill_date_form(depart_form, self.departure_date)
            time.sleep(0.5)
            form2 = self.driver.find_element_by_xpath('//select[@id="segments1.travelTime"]')
            return_form = self.driver.find_element_by_xpath('//input[@id="segments1.travelDate"]')
            self.fill_date_form(return_form, self.return_date)
            self.select_time_of_day(form2)
            time.sleep(0.5)

        elif self._one_way_trip():
            # selecting 'time interval' form
            form = self.driver.find_element_by_xpath('//select[@id="segments0.travelTime"]')
            self.select_time_of_day(form)
            depart_form = self.driver.find_element_by_xpath('//input[@id="segments0.travelDate"]')
            self.fill_date_form(depart_form, self.departure_date)
            time.sleep(0.5)
        self.fill_from_form()
        self.fill_destination_form()

        # all search fields filled, and we beginning the search:
        self.click_search()
        self.check_for_input_error()
        self.fully_load_results()

        # scraping data from search results:
        if self._one_way_trip():
            list_results = self.parse_page()
            file_name = self._generate_file_name(self.departure, self.destination, self.departure_date, self.file_format)
            self.save_to_json(file_name, list_results)
        # for round trip we need to scrap 2nd search page with returning flights
        if self._round_trip():
            self.click_on_round_trip()
            self.fully_load_results()
            list_results2 = self.parse_page()
            file_name = self._generate_file_name(self.departure, self.destination, self.departure_date, self.file_format)
            self.save_to_json(file_name, list_results2)
            time.sleep(0.5)

        # self._get_my_ip()


if __name__ == "__main__":
    browser = AmericanAirlines('mia', 'sfo', '02/12/2018', '02/15/2018')
    browser.run()
