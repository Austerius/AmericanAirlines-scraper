"""
Script for running American Airlines scraper directly from command line.
**Requirements**:
- Selenium
- Geckodriver
- Firefox web browser

Default name for file with search queries -
'search_tasks.json'(default location - script directory).
'search_tasks.json'(and similar files) must have following format:
            [
            {"departure": "departure_string(airport_code or state or city)",
             "destination": "destination_string(airport_code or state or city)",
             "date": "departure_date(mm/dd/yyyy)",
             "return_date": "return_date_string"},
            {"another search task and so on"}, {}, {}, ...
            ]

So, what kind of search you can perform and what you will get as a result?
For example, you can find all flights from Los Angeles to San Francisco that depart on 03/21/2018 just typing next:
    aa_manager.py args LAX SFO 03/21/2018
(Take note of date format: mm/dd/yyyy).Entire search results will be placed in newly generated .json file(default
location of the file - script execution folder) with auto generated name like this one: 'LAX_SFO2018-03-21-220649.json'
(First 3 letters - departure airport code, second 3 letters - destination airport code, then follows a date of the
flight and timestump, which represent file's creation time: -HHMMSS).
 Ok, lets look inside:
  {
    "depart": "03-21-2018 21:20:00",
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
Values keys speaks for themselves, didn't they? Well, only "price" key need a bit of explanation: this key shows
lowest price for selected flight. Also, if you see "N/A" - that's probably mean you need to buy ticket directly
at airport or searched class("basic economy", "main cabin" etc) not available for most of the flights.
WELL, WOW. But one more example: let's say - you wanna know list of all flight from all Alabama state airports
to San Francisco? Not a problem - just type a state name instead of specific airport code.(Better to use
parallel execution for this type of task):
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

"""
import json
import re
import datetime
import argparse
from multiprocessing import Pool

from american_airlines import AmericanAirlines

AIRPORTS_CODES = "airports.json"  # this file contain all available for search airports codes
NUM_PROCESSES = 4  # default number of processes for parallel execution
SEARCH_TASKS = "search_tasks.json"  # default name for .json file with search queries


def get_airports_codes(airports_file):
    """Loading airports codes, city and state names form .json file(default: AIRPORTS_CODES)"""
    with open(airports_file, 'r') as file:
        text = file.read()
        # yeh, 'airports.json' doesnt have proper format, so we just making some transformations
        new_text = re.sub(r'}{', '},{', text)
        new_text = re.sub(r"^{", '[{', new_text)
        new_text = re.sub(r'}$', '}]', new_text)
        return json.loads(new_text)


def get_search_tasks(tasks_file):
    """ Loading search queries from .json file(default - 'search_tasks.json')"""
    with open(tasks_file, 'r') as file:
        return json.load(file)


def validate_airport_name(airports_list, airport_name):
    """ Here we compering entered airport name to names from AIRPORTS_CODES.
        Three types of names are permitted: airport code, city name(where airport located), state name.
    """
    if not isinstance(airport_name, str):
        raise TypeError("Airport name is not a String!")
    for airport in airports_list:
        if airport['code'].lower() == airport_name.lower():
            return 'code'
        if (airport['city']).lower() == airport_name.lower():
            return 'city'
        if (airport['state']).lower() == airport_name.lower():
            return 'state'
    return 'none'  # no matches found


def validate_date_string(date_string):
    """Date string must have following format: dd/dd/dddd (where d - single digit from 0 to 9)"""
    return re.fullmatch(r'^\d{2}/\d{2}/\d{4}$', date_string)


def transform_string_to_date(date_string):
    """Transforming date string to datetime.date format. Check data with 'validate_date_string' first"""
    month, day, year = date_string.split("/")
    return datetime.date(year=int(year), month=int(month), day=int(day))


def check_dates(task_dictionary):
    """ Validating departure and return dates. Note that :param task_dictionary: must have proper form
        Main usage - inside 'check_and_quantize_tasks' function.
    """
    current_date = datetime.date.today()
    departure_date_string = task_dictionary['date']  # existing of this field checked in 'check_and_quantize_tasks'
    # checking string date to be formatted like mm/dd/yyyy
    if not validate_date_string(departure_date_string):
        raise ValueError("Departure date string has inappropriate format!")
    # if date_string has something like this: 34/34/2018 - ValueError will be raised 
    departure_date = transform_string_to_date(departure_date_string)
    # checking for departure date not from the past
    if current_date > departure_date:
        raise ValueError("Departure date must be today or in the future(no past dates allowed)")
    try:
        return_date_string = task_dictionary['return_date']
        if not validate_date_string(return_date_string):
            raise ValueError("Return date string has inappropriate format!")
        return_date = transform_string_to_date(return_date_string)
        if departure_date > return_date:
            raise ValueError("Return date must be at same day or after departure date!")
    except KeyError:
        pass  # if no return_date - than it's 'one way' trip


def airports_codes_from_city(name, airports_list, airport_type):
    """
        Here we finding all airports(their codes) in city or state.
        :param name: name of airport we gonna check
        :param airports_list: list of all airports
        :param airport_type: type of :param name: - 'code', 'city', 'state'
        :return: list of airports codes
    """
    temp = []
    for airport in airports_list:
        if name.lower() == airport[airport_type].lower():
            temp.append(airport['code'])
    return temp


def check_and_quantize_tasks(tasks_dictionaries, airports_list):
    """
        Here we perform 'quantization' of search queries to the form which can be
        executed inside 'execute_single_crawler' function. Each task will be a list, that contains:
        departure airport code, destination airport code, departure date, return date('None' for 'one way' trip),
        trip type('one way' or 'round trip').
        :param tasks_dictionaries: list of dictionaries (Our search queries).
        :param airports_list: return result from 'get_airports_codes' function
        :return: list of lists.
    """
    tasks_list = []  # returns list of lists
    for dictionary in tasks_dictionaries:
        return_date = None
        # validating 'departure' key
        try:
            departure_airport = dictionary['departure']
            airport_type = validate_airport_name(airports_list, departure_airport)
            if airport_type == "none":
                print("Invalid airport name")
                continue
            departure_codes = airports_codes_from_city(departure_airport, airports_list, airport_type)
        except (KeyError, ValueError) as e:
            print(e.__str__())
            continue  # skip this query dictionary if there is invalid data
        # validating destination key
        try:
            destination_airport = dictionary['destination']
            airport_type = validate_airport_name(airports_list, destination_airport)
            if airport_type == "none":
                print("Invalid airport name")
                continue
            destination_codes = airports_codes_from_city(destination_airport, airports_list, airport_type)
        except (KeyError, ValueError) as e:
            print(e.__str__())
            continue
        # validating 'date'
        try:
            departure_date = dictionary['date']
            check_dates(dictionary)  # here we also checking 'return_date' if present
        except (KeyError, ValueError) as e:
            print(e.__str__())
            continue
        # validating "return_date" (we don't always need a return date)
        try:
            return_date = dictionary['return_date']
        except KeyError:
            pass
        # forming tasks  (list of lists)
        for dep_airport in departure_codes:  # from each airport in departure list
            for dest_airport in destination_codes:  # to every single airport in destination list
                if return_date is None:
                    trip_type = "one way"
                else:
                    trip_type = 'round trip'
                # that is actually our 'quantized' task
                temp = [dep_airport, dest_airport, departure_date, return_date, trip_type]
                tasks_list.append(temp)
    # if we cant identify even a single task - something wrong with input data
    if not tasks_list:
        raise ValueError('No tusks for execution found. Check input format!')
    return tasks_list


def execute_single_crawler(list_of_arguments):
    """This function create and execute single instance of AmericanAirlines() class"""
    crawler = AmericanAirlines(departure_airport=list_of_arguments[0], destination_airport=list_of_arguments[1],
                               departure_date=list_of_arguments[2], return_date=list_of_arguments[3],
                               trip_type=list_of_arguments[4])
    crawler.run()


def serial_execution(tasks_list):
    for task in tasks_list:
        execute_single_crawler(task)


def multiprocesses_execution(tasks_list):
    with Pool(processes=NUM_PROCESSES) as pool:
        pool.map(execute_single_crawler, tasks_list)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Getting flights information (depart, arrive, number of stops, "
                                                 "lowest price etc) from American Airlines web site search form "
                                                 "using user-provided(from file or command line) search parameters")

    # ok, parallel or serial types of execution should exclude each other
    group1 = parser.add_mutually_exclusive_group()
    # command for parallel execution
    group1.add_argument('-sp', '--parallel',
                        help="Perform parallel search",
                        const="parallel",
                        action='store_const',
                        dest='execution_method')
    # command for serial execution
    group1.add_argument('-ss', '--serial',
                        help="Perform search, using serial execution(tusks executed 'one-by-one'). "
                             "It's a default method.",
                        const="serial",
                        action='store_const',
                        dest='execution_method')
    # Serial execution will be default method, if parallel not mentioned explicitly
    parser.set_defaults(execution_method='serial')
    # creating 2 subparsers(run and args) with name 'subcommand' (parser.pars_args().subcommand - name of subparser)
    subparsers = parser.add_subparsers(dest="subcommand")
    # parser_a will get tasks list from a file
    parser_a = subparsers.add_parser('run', help="Execute search tasks from a file (default method - serial)")
    # command for loading tasks from file (default 'search_tasks.json')
    parser_a.add_argument('-f', '--file',
                          help="File name (and full path, if needed) to the file with search tasks.",
                          default=SEARCH_TASKS,
                          action='store',
                          dest='file_name')

    # parser_b will accept search parameters from command line
    parser_b = subparsers.add_parser('args',
                                     help="Enter search parameters from command line "
                                          "and run search(default execution method - serial)")
    # entering departure airport name
    parser_b.add_argument('departure_airport',
                          help="Departure airport's code(or departure city/state - in this case list "
                               "of all airports in the city/state will be formed)",
                          action='store',
                          )
    # entering destination airport name/code
    parser_b.add_argument('destination_airport',
                          help="Destination airport's code(or departure city/state - in this case list"
                               "of all airports in the city/state will be formed)",
                          action='store',
                          )
    # entering departure date
    parser_b.add_argument('departure_date',
                          help="Departure date",
                          action='store',
                          )
    # entering return date(optionally):
    parser_b.add_argument('return_date',
                          help="Return date(optional). Enter this parameter only for round trips",
                          nargs='?',
                          action='store',
                          )

    # getting our arguments
    args = parser.parse_args()
    list_of_airports = get_airports_codes(AIRPORTS_CODES)
    # ok, here is block for 'file execution' logic
    if args.subcommand == 'run':
        print("Starting {} execution of search commands from file: '{}'".format(args.execution_method, args.file_name))
        # Opening and loading file with search tasks
        potential_tasks = get_search_tasks(args.file_name)
        # Validating data and forming commands from search tasks:
        list_of_tasks = check_and_quantize_tasks(potential_tasks, list_of_airports)

    # this is block for "command line" search arguments logic
    elif args.subcommand == 'args':
        print("Staring {} execution of provided search command...".format(args.execution_method))
        # forming dictionary with potential search parameters
        search_dict = [{'departure': args.departure_airport,
                        'destination': args.destination_airport,
                        'date': args.departure_date}]
        if args.return_date is not None:
            search_dict[0]['return_date'] = args.return_date
        list_of_tasks = check_and_quantize_tasks(search_dict, list_of_airports)

    if args.execution_method == 'serial':
        serial_execution(list_of_tasks)
    elif args.execution_method == 'parallel':
        multiprocesses_execution(list_of_tasks)
    print("All jobs done!")
