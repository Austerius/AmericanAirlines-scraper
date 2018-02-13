""" Functional tests for American Airlines scraper
    run from command line(you must be in project directory):
    ```python -m unittest discover```
"""

import unittest
import datetime

import aa_manager


class TestManager(unittest.TestCase):

    def test_validate_date_string(self):
        """ Testing 'validate_date_string' function from 'aa_manager.py' """
        # proper date_string format
        date_string1 = '34/34/2345'
        # improper date_string format:
        date_string2 = '34\\12\\2345'
        date_string3 = '2454'
        date_string4 = '02/12/201'
        date_string5 = 'mm/12/2018'
        self.assertTrue(aa_manager.validate_date_string(date_string1))
        self.assertFalse(aa_manager.validate_date_string(date_string2))
        self.assertFalse(aa_manager.validate_date_string(date_string3))
        self.assertFalse(aa_manager.validate_date_string(date_string4))
        self.assertFalse(aa_manager.validate_date_string(date_string5))

    def test_transform_string_to_date(self):
        """ Testing 'transform_string_to_date' function from 'aa_manager.py' """
        date1 = datetime.date(year=2018, month=2, day=11)
        date_string1 = '02/11/2018'
        self.assertEqual(date1, aa_manager.transform_string_to_date(date_string1))

    def test_check_dates(self):
        """ Testing 'check_dates' function from 'aa_maneger.py' """
        task_dict1 = {"departure": "BHM",
                      "destination": "MOB",
                      "date": "kkjkj",
                      "return_date": "03/09/2118",
                      }
        # improper "date" format
        with self.assertRaises(ValueError):
            aa_manager.check_dates(task_dict1)

        task_dict2 = {"departure": "BHM",
                      "destination": "MOB",
                      "date": "03/10/2118",
                      "return_date": "03/09/2118",
                      }
        # return date > departure date
        with self.assertRaises(ValueError):
            aa_manager.check_dates(task_dict2)

        task_dict3 = {"departure": "BHM",
                      "destination": "MOB",
                      "date": "03/10/1118",
                      "return_date": "03/09/2118",
                      }
        # departure date < current date
        with self.assertRaises(ValueError):
            aa_manager.check_dates(task_dict3)

        task_dict4 = {"departure": "BHM",
                      "destination": "MOB",
                      "date": "03/10/2118",
                      "return_date": "dfgfhgh",
                      }
        # improper "return_date" format:
        with self.assertRaises(ValueError):
            aa_manager.check_dates(task_dict4)

    def test_airports_codes_from_city(self):
        """ Skip this test, if you using different airports list"""
        airports = aa_manager.get_airports_codes('airports.json')
        airport_name1 = 'Alabama'
        airports_list1 = ['BHM', 'DHN', 'MSL', 'HSV', 'MOB', 'MGM']
        self.assertEqual(airports_list1, aa_manager.airports_codes_from_city(airport_name1, airports, 'state'))

        airport_name2 = 'bhm'
        airports_list2 = ['BHM']
        self.assertEqual(airports_list2, aa_manager.airports_codes_from_city(airport_name2, airports, 'code'))

        airport_name3 = 'fhhjkhjkgh'
        airports_list3 = []
        self.assertEqual(airports_list3, aa_manager.airports_codes_from_city(airport_name3, airports, 'code'))

    def test_validate_airport_name(self):
        """ Skip this test, if you using different airports list"""
        airports = aa_manager.get_airports_codes('airports.json')
        airport_name1 = "alabama"
        type1 = 'state'
        self.assertEqual(type1, aa_manager.validate_airport_name(airports, airport_name1))

        airport_name2 = "Florence"
        type2 = 'city'
        self.assertEqual(type2, aa_manager.validate_airport_name(airports, airport_name2))

        airport_name3 = 'bhm'
        type3 = 'code'
        self.assertEqual(type3, aa_manager.validate_airport_name(airports, airport_name3))

        airport_name4 = 'No Name here'
        type4 = 'none'
        self.assertEqual(type4, aa_manager.validate_airport_name(airports, airport_name4))

    def test_check_and_quantize_tasks(self):
        """ You need airports.json for this test to work"""
        airports = aa_manager.get_airports_codes('airports.json')
        task_dict1 = [{"departure": "BHM",
                       "destination": "MOB",
                       "date": "03/10/2118",
                       "return_date": "03/11/2118",
                       },
                      {"departure": "bhm",
                       "destination": 'mob',
                       'date': "03/17/2118"}]
        task_list1 = [["BHM", "MOB", '03/10/2118', '03/11/2118', 'round trip'],
                      ["BHM", "MOB", "03/17/2118", None, 'one way']]
        self.assertEqual(task_list1, aa_manager.check_and_quantize_tasks(task_dict1, airports))

        # skipping 2nd dictionary because of error in "departure" field
        task_dict2 = [{"departure": "BHM",
                       "destination": "MOB",
                       "date": "03/10/2118",
                       "return_date": "03/11/2118",
                       },
                      {"departure": "bhmgfhgfh",
                       "destination": 'mob',
                       'date': "03/17/2118"}]
        task_list2 = [["BHM", "MOB", '03/10/2118', '03/11/2118', 'round trip']]
        self.assertEqual(task_list2, aa_manager.check_and_quantize_tasks(task_dict2, airports))

        # no "return_date" = 'one way' trip
        task_dict3 = [{"departure": "BHM",
                       "destination": "MOB",
                       "date": "03/10/2118",
                       }]
        task_list3 = [["BHM", "MOB", "03/10/2118", None, 'one way']]
        self.assertEqual(task_list3, aa_manager.check_and_quantize_tasks(task_dict3, airports))

        # both dicts have some error in data/key, so we didn't acquired search commands from them
        task_dict4 = [{"departureT": "BHM",
                       "destination": "MOB",
                       "date": "03/10/2118",
                       "return_date": "03/11/2118",
                       },
                      {"departure": "bhm",
                       "destination": 'mob',
                       'date': "fgfgfg/17/2118"}]
        with self.assertRaises(ValueError):
            aa_manager.check_and_quantize_tasks(task_dict4, airports)

        # getting series of tasks from one dictionary
        task_dict5 = [{"departure": "Alabama",
                       "destination": "SFO",
                       "date": "03/10/2118"}]
        task_list5 = [["BHM", "SFO", "03/10/2118", None, 'one way'],
                      ["DHN", "SFO", "03/10/2118", None, 'one way'],
                      ["MSL", "SFO", "03/10/2118", None, 'one way'],
                      ["HSV", "SFO", "03/10/2118", None, 'one way'],
                      ["MOB", "SFO", "03/10/2118", None, 'one way'],
                      ["MGM", "SFO", "03/10/2118", None, 'one way']]
        self.assertEqual(task_list5, aa_manager.check_and_quantize_tasks(task_dict5, airports))