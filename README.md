# AmericanAirlines-scraper
Scraping US flights information from AmericanAirlines web site(www.aa.com) using Selenium and BeautifulSoup.</br> 
Take note: project was created for educational purposes to demonstrate usage of Selenium driver, BeautifulSoup, multiprocessing, argparse.</br>
You can run this scraper from command line using "<i>aa_manager.py</i>"(check below) or you can use class 'AmericanAirlines()' from 
"<i>american_airlines.py</i>" directly. </br>
**Requirements**:
- Selenium 
- Geckodriver
- Firefox web browser
- bs4 (BeautifulSoup)
<h3>aa_manager.py</h3>
Script for running American Airlines scraper directly from command line.

Default name for file with search queries -
'<i>search_tasks.json</i>'(default location - script directory).
'<i>search_tasks.json</i>'(and similar files) must have following format:

            [
            {"departure": "departure_string(airport_code or state or city)",
             "destination": "destination_string(airport_code or state or city)",
             "date": "departure_date(mm/dd/yyyy)",
             "return_date": "return_date_string"},
            {"another search task and so on"}, {}, {}, ...
            ]

So, **what kind of search** you can perform and what you will get as a result?

For example, you can find all flights from Los Angeles to San Francisco that depart on 03/21/2018 just typing next:

    aa_manager.py args LAX SFO 03/21/2018
    
(Take note of date format: mm/dd/yyyy).Entire search results will be placed in newly generated .json file(default
location of the file - script execution folder) with auto generated name like this one: 'LAX_SFO2018-03-21-220649.json'
(First 3 letters - departure airport code, second 3 letters - destination airport code, then follows a date of the
flight and timestump, which represent file's creation time: -HHMMSS).

 Ok, lets look inside:
 
  ``` 
    {"depart": "03-21-2018 21:20:00",
    "arrive": "03-21-2018 22:54:00",
    "stops": "Nonstop",
    "price": "46.00",
    "details": [
      {
        "number": "AA  6039",
        "airplane": "E75-Embraer RJ-175"
      }
    ]
  }
 ``` 
Values keys speaks for themselves, didn't they? Well, only "price" key need a bit of explanation: this key shows
lowest price for selected flight. Also, if you see "N/A" - that's probably mean you need to buy ticket directly
at airport or searched class("basic economy", "main cabin" etc) not available for most of the flights.

WELL, WOW. But one more example:</br> 
let's say - you wanna know list of all flight from all Alabama state airports
to San Francisco? </br>
Not a problem - just type a state name instead of specific airport code.(Better to use
**parallel** execution for this type of task):

    aa_manager.py -sp args Alabama SFO 03/21/2018
    
And several .json files (one for each Alabama airport) will be saved into execution folder.

Here is some **help information**:

    usage: aa_manager.py [-h] [-sp | -ss] {run,args} ...
    positional arguments:
      {run,args}
        run            Execute search tasks from a file (default method - serial)
        args           Enter search parameters from command line and run
                       search(default execution method - serial)

    optional arguments:
      -h, --help       show this help message and exit
      -sp, --parallel  Perform parallel search
      -ss, --serial    Perform search, using serial execution(tusks executed 'one-
                       by-one'). It's a default method.

**run**:

    usage: aa_manager.py run [-h] [-f FILE_NAME]
    -f FILE_NAME, --file FILE_NAME
                        File name (and full path, if needed) to the file with
                        search tasks

**args**:

    usage: aa_manager.py args [-h] departure_airport destination_airport departure_date [return_date]
    positional arguments:
      departure_airport    Departure airport's code(or departure city/state - in
                           this case list of all airports in the city/state will
                           be formed)
      destination_airport  Destination airport's code(or destination city/state - in
                           this case list of all airports in the city/state will be
                           formed)
      departure_date       Departure date
      return_date          Return date(optional). Enter this parameter only for
                           round trips
                           
<h3>american_airlines</h3> 
Contains AmericanAirlines class, where help methods and logic for scraping data
from American Airlines web site are implemented. (all for educational purposes only!)

Check '__init__()' docstring for required parameters. To start scraping - just create instance of AmericanAirlines
and use 'run()' method. Example:

    scraper = AmericanAirlines('mia', 'sfo', '02/12/2018', '02/15/2018')
    scraper.run()
    
**Note**: this class does little about input data validation, so use '<i>aa_manager.py</i>' (or your own script) to
perform data validation.

<h3>airports_codes.py</h3>
This script should scrape "State", "City", "Airport Name" and "Airport Code" (USA Airports only) from
    Americans Airlines web site(www.aa.com).

Usage example:

        data = AirportsCodes(3, filename='myfile.json', show=True)
        data.run()
      
<h3>airports.json</h3>       
List of all codes of US airports(used for data validation inside '<i>aa_manager.py</i>') generated by '<i>airports_codes.py</i>'
<h3>search_tasks.json</h3>
Example of file with search queries for '<i>aa_manager.py</i>'
<h3>test_functional.py</h3>
Functional tests for American Airlines scraper. </br>
To run from command line(you must be in project directory):

    python -m unittest discover
