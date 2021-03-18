'''
Author: Huai Jiang Robbie Shaw
Email: huai@ethree.com robbie@ethree.com
'''

from __future__ import division
import pandas as pd
import os
import numpy as np
from pathlib import Path 
from s3fs.core import S3FileSystem

def stock_rollover(adoption_start, adoption_end, vehicle_lifetime, population):
    
    new_sales = {}
    replacements = {}
    sales = {}

    new_sales[adoption_start] = population[adoption_start]

    for year in range(adoption_start, adoption_end + 1):
        if year == adoption_start:
            try:
                new_sales[year] = population[year] - population[year-1]
            except:
                new_sales[year] = 0
        else:
            new_sales[year] = population[year] - population[year-1]

    for year in range(adoption_end + 1, adoption_end + vehicle_lifetime):
        new_sales[year] = 0.

    first_replacement_year = adoption_start + vehicle_lifetime
    for year in range(adoption_start, first_replacement_year):
        replacements[year] = 0.

    for year in range(first_replacement_year, adoption_end + 1):
        replacements[year] = \
            new_sales[year - vehicle_lifetime] + replacements[year - vehicle_lifetime]

    for year in range(adoption_end + 1, adoption_end + vehicle_lifetime):
        replacements[year] = 0.

    for year in range(adoption_start, adoption_end + vehicle_lifetime):
        sales[year] = new_sales[year] + replacements[year]

    for year in range(adoption_end + 1, adoption_end + vehicle_lifetime):
        try:
            population[year] = population[year-1] - sales[year - vehicle_lifetime]
        except:
            population[year] = population[year - 1]

    return population


def hourly(array):
    return np.mean(np.reshape(array, (int(len(array) / 60), 60)), axis=1) #depending on the unit


def split_file(load_profile, county, controlled_types, scenarios={'Scenario 1': 'BaseCase'}, year='2025'):

    s3 = S3FileSystem(anon=False)
    bucket = 's3://script.control.tool'
    path = Path(__file__).parent.resolve()

    # Input Loads
    weekday_data_path = str(path)+'/inputs/weekdays/'
    weekend_data_path = str(path)+'/inputs/weekends/'

    weekday_load_list = list(weekday_data_path)
    weekend_load_list = list(weekend_data_path)


    # Driver Counts Path
    driver_counts_path = 'Driver Counts'

    # Adoption File - This file must correspond to the scenario selected.
    adoption_path = 'Adoption Files/vehicle_adoption base case.xlsx'

    combined_output = pd.DataFrame()

    output_dictionary = {}

    charger_types = ['Residential L1', 'Residential L2', 'Residential MUD', 'Work', 'Public L2', 'Fast', 'Total']
    for field_name in charger_types:
        output_dictionary[field_name] = pd.DataFrame()

    for scenario in scenarios.values():
        for controlled_type in controlled_types:

            if scenario in ['WorkPublic', 'FastPublic', 'Work', 'Equity']:

                weekday_file_name_exists = os.path.isfile(weekday_data_path + "{}_rescaled_{}_weekday_{}_county_{}_load_{}.csv".format(Scenario, year, county, controlled_type, load_profile))
                weekend_file_name_exists = os.path.isfile(weekend_data_path + "{}_rescaled_{}_weekend_{}_county_{}_load_{}.csv".format(Scenario, year, county, controlled_type, load_profile))

                if weekday_file_exists:
                    weekday_file_name = "{}_rescaled_{}_weekday_{}_county_{}_load_{}.csv".format(scenario, year, county, controlled_type, load_profile)
                    driver_counts_file_name = "{}_{}_weekday__driver_counts.csv".format(scenario, year)

                if weekend_file_name_exists:
                    weekend_file_name = "{}_rescaled_{}_weekend_{}_county_{}_load_{}.csv".format(scenario, year, county, controlled_type, load_profile)
                    driver_counts_file_name = "{}_{}_weekend__driver_counts.csv".format(scenario, year)

            else:

                weekday_file_name_exists = os.path.isfile(weekday_data_path + "{}_{}_weekday_{}_county_{}_load_{}.csv".format(scenario, year, county, controlled_type, load_profile))
                weekend_file_name_exists = os.path.isfile(weekend_data_path + "{}_{}_weekend_{}_county_{}_load_{}.csv".format(scenario, year, county, controlled_type, load_profile))
                        
                if weekday_file_name_exists:
                    weekday_file_name = "{}_{}_weekday_{}_county_{}_load_{}.csv".format(scenario, year, county, controlled_type, load_profile)
                    driver_counts_file_name = "{}_{}_weekday__driver_counts.csv".format(scenario, year)
                if weekend_file_name_exists:
                    weekend_file_name = "{}_{}_weekend_{}_county_{}_load_{}.csv".format(scenario, year, county, controlled_type, load_profile)
                    driver_counts_file_name = "{}_{}_weekend__driver_counts.csv".format(scenario, year)
      

            driver_count_df = pd.read_csv("{}/{}/{}".format(bucket, driver_counts_path, driver_counts_file_name))
            driver_count = float(driver_count_df.loc[driver_count_df['County'] == county]['Num Drivers'])

            adoption_spreadsheet_df = \
                pd.read_excel(f"{bucket}/{adoption_path}", sheet_name=county).set_index(['year'])[' BEV_population']
                        
            if weekday_file_name_exists:
                weekday_all = pd.read_csv(os.path.join(weekday_data_path,weekday_file_name))
                weekday_all = weekday_all.drop(list(weekday_all)[0],axis=1)
                col_names = list(weekday_all.columns)
            if weekend_file_name_exists:
                weekend_all = pd.read_csv(os.path.join(weekend_data_path,weekend_file_name))
                weekend_all = weekend_all.drop(list(weekend_all)[0],axis=1)
                col_names = list(weekend_all.columns)

            day_type = pd.read_csv(os.path.join(str(path),'day_type.csv'))

            for field_name in col_names:
                if weekday_file_name_exists:
                    weekday_array = np.array(weekday_all[field_name])
                    weekday_aggregated = hourly(weekday_array) # convert from 1-min to 1-hour
                if weekend_file_name_exists:
                    weekend_array = np.array(weekend_all[field_name])
                    weekend_aggregated = hourly(weekend_array)

                output = []

                for i in range(day_type.shape[0]):
                    if day_type['DayType'][i] == 1 and weekday_file_name_exists:
                        output.append(weekday_aggregated)
                    elif weekday_file_name_exists:
                        output.append(weekday_aggregated)
                    elif weekend_file_name_exists:
                        output.append(weekend_aggregated)

                annual_output = output * 52
                output = np.array(annual_output)
                output = np.append(output, output[0])
                output = np.reshape(output, 8760)
                output = pd.DataFrame(output, columns = {year})

                per_vehicle_results = output/driver_count

                for this_year in range(2019, 2031):
                    output_dictionary[field_name][this_year] = per_vehicle_results[year] * adoption_spreadsheet_df.loc[this_year]/1000
                            

                stock_rollover_output = stock_rollover(2019, 2030, 11, output_dictionary[field_name])

                stock_rollover_output.to_csv(os.path.join(
                    str(path.parent), "EV_Loads", "load_profiles",  "{}_{}_{}_{}_load.csv".format(
                        scenario, county, field_name, controlled_type)),index = True)
             
            if weekday_file_name_exists:
                os.remove(os.path.join(weekday_data_path,weekday_file_name))

            if weekend_file_name_exists:
                os.remove(os.path.join(weekend_data_path,weekend_file_name))
