from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from past.utils import old_div
from builtins import str
from builtins import range
from builtins import object
import os
import csv
import rate_class
import vehicles_class
import loadprofile_class
import chargers_class
import constants
import datetime
import sys
import helpers
import pandas as pd
import numpy as np
from s3fs.core import S3FileSystem
from pathlib import Path

class MODEL_INPUTS(object):
    """
    Python object where the inputs to a model run are stored. All inputs read from files are read in this script.
    """

    def __init__(self, case_name):

        ### DIRECTORIES ###
        self.PYTHON_DIR = str()
        self.MODEL_DIR = str()
        self.DATA_DIR = str()
        self.CONFIG_DIR = str()
        self.RATES_DIR = str()
        self.LOADPROFILE_DIR = str()
        self.TESTFILE_DIR = str()
        self.RESULTS_DIR = str()
        self.T_AND_D_OUT_DIR = str()


        ### Inputs read from config file ###
        # Year inputs
        self.start_year = int()
        self.first_adoption_year = int()
        self.end_year = int()
        self.gallons_per_ice_year = int()
        self.timesteps = {}


        # Financial inputs
        self.inflation_rate = float()
        self.discount_rate = float()
        self.tax_credit = float()
        self.BEV_tax_credit = float()
        self.PHEV_tax_credit = float()
        self.credit_to_replacements = True

        # Vehicle inputs
        self.vehicle_lifetime = int()
        self.last_taxcredit_year = int()
        self.annual_oandm_savings = float()
        self.bev_annual_oandm_savings = float()
        self.phev_annual_oandm_savings = float()
        self.gallons_per_ice = float()
        self.metrictons_CO2_per_gallon = float()
        self.carbon_cost = float()
        self.NOX_per_gallon = float()
        self.SO2_per_gallon = float()
        self.PM_10_per_gallon = float()
        self.VOC_per_gallon = float()

        # Managed charging and load profile inputs
        self.include_static_workplace = bool()
        self.static_workplace_chargers = {}

        # Vehicles inputs
        self.vehicles_file = 'vehicle_adoption'

        # Load profile inputs
        self.loadprofile_names = list()
        self.loadprofile_to_rate = dict()
        self.loadprofile_to_charger = dict()

        # Charger inputs
        self.charger_name = 'ports_adoption'
        self.public_dcfc_proportion = float()
        self.publicl2_portsperEVSE = float()

        self.homel2_startprice = float()
        self.homel2_reduction = float()
        self.homel2_chrgrspermeter = float()

        self.workl2_startprice = float()
        self.workl2_reduction = float()
        self.workl2_chrgrspermeter = float()
        self.workl2_cap_per_plug = float()
        self.workl2_portsperEVSE = float()

        self.publicl2_startprice = float()
        self.publicl2_reduction = float()
        self.publicl2_chrgrspermeter = float()

        self.dcfc_startprice = float()
        self.dcfc_reduction = float()
        self.dcfc_chrgrspermeter = float()

        self.pro_lite_EVSE_method = bool()
        self.work_EVSE_ratio = float()
        self.public_l2_EVSE_ratio = float()
        self.dcfc_EVSE_ratio = float()

        self.dcfc_makeready = float()
        self.dcfc_evse_cost = float()
        self.publicl2_makeready = float()
        self.publicl2_evse_cost = float()
        self.workl2_makeready = float()
        self.workl2_evse_cost = float()
        self.homel2_makeready = float()
        self.homel2_evse_cost = float()

        # T&D Inputs
        self.tandd_method = str()
        self.cost_per_incremental_kw = float()
        self.DCFC_cluster_size_per_upgrade = float()
        self.DCFC_distribution_upgrade_cost = float()

        # Simple only: If False, only incremental load from startyear-1 to startyear is used
        self.allEVload_onTandD = bool()

        ### CREATED INPUTS ###
        self.get_directories(case_name)
        self.read_config('config')
        self.read_loadprofile_allocation('loadprofile_allocation')
        self.get_charger_assignments('charger_assignments')

        self.chargers_per_meter = {'Residential L2': self.homel2_chrgrspermeter,
                                   'Residential L1': self.homel2_chrgrspermeter,
                                   'Public L2': self.publicl2_chrgrspermeter,
                                   'DCFC': self.dcfc_chrgrspermeter,
                                   'Workplace L2': self.workl2_chrgrspermeter}

        self.simple_TandD = True if self.tandd_method == "Simple" else False

        return


    def read_config(self, config_name):
        """
        Reads in the config CSV, which stores many of the inputs used by the model.
        :param config_name: The name of the config file to be read in.
        :return: Each attribute in the config CSV is added as an attribute to the MODEL_INPUTS instance.
        """
        config_dir = self.CONFIG_DIR + r'/{0}.csv'.format(config_name)
        config_data = pd.read_csv(config_dir, sep="\n", header=None, skiprows=1)

        for row in config_data.iterrows():
            row = row[1].str.split(",").tolist()
            attribute = row[0][0]
            attribute_type = type(getattr(self, attribute))

            if attribute_type is float:
                value = float(row[0][1])
            elif attribute_type is int:
                value = int(row[0][1])
            elif attribute_type is str:
                value = row[0][1]
            elif attribute_type is bool:
                if row[0][1].upper() == "TRUE":
                    value = True
                elif row[0][1].upper() == "FALSE":
                    value = False
                else:
                    print('problematic attribute: %s' % attribute)
                    print('attribute type: %s' % attribute_type)
                    print('value: %s' % row[0][1])
            else:
                print(attribute, attribute_type)
                print('%s attribute type not assigned.' % attribute)
                print('value: %s' % row[0][1])
                exit()

            setattr(self, attribute, value)
            # print '\tset as %s' % type(value)

    def read_loadprofile_allocation(self, allocation_name):
        """
        Reads in information regarding how load profiles are to be allocated across rates, and guarantees that those
        allocations sum to 1.
        :param allocation_name: The name of the allocation file to be read in.
        :return: MODEL_INPUTS.loadprofile_to_rate and MODEL_INPUTS.loadprofile_names are defined in this function.
        """

        allocation_dir = self.DATA_DIR + "/Load Profile Assignment" + r'/{0}.csv'.format(allocation_name)

        allocation_data = pd.read_csv(allocation_dir, header=None, index_col=False)
        first_row = True

        for row in allocation_data.iterrows():
            row = row[1].str.split(",").tolist()
            if first_row:
                rate_names = row[1:]
                first_row = False

            else:
                loadprofile_name = row[0][0]

                for j in range(len(rate_names)):
                    rate_name = rate_names[j][0]
                    value = float(row[j+1][0])


                    if value != 0:
                        try:
                            self.loadprofile_to_rate[loadprofile_name][rate_name] = value
                        except KeyError:
                            self.loadprofile_to_rate[loadprofile_name] = {rate_name: value}

        # Make sure allocation sums to 1
        for loadprofile_name in list(self.loadprofile_to_rate.keys()):
            total = sum(self.loadprofile_to_rate[loadprofile_name].values())
            num_rates = len(list(self.loadprofile_to_rate[loadprofile_name].keys()))
            for rate_name in list(self.loadprofile_to_rate[loadprofile_name].keys()):
                if total == 0:
                    self.loadprofile_to_rate[loadprofile_name][rate_name] = 1.0 / num_rates
                else:
                    self.loadprofile_to_rate[loadprofile_name][rate_name] = \
                        old_div(self.loadprofile_to_rate[loadprofile_name][rate_name], total)

        self.loadprofile_names = list(self.loadprofile_to_rate.keys())

    def get_charger_assignments(self, filename):

        chargerassignment_dir = self.DATA_DIR + "/Load Profile Assignment" + r'/{0}.csv'.format(filename)
        chargerassignment_data = pd.read_csv(chargerassignment_dir, sep="\n" , header=None, skiprows=1)

        for row in chargerassignment_data.iterrows():
            row = row[1].str.split(",").tolist()
            
            loadprofile_name = row[0][0]
            charger_name = row[0][1]
            self.loadprofile_to_charger[loadprofile_name] = charger_name

    def get_directories(self, case_name):
        """
        Build all of the directories required for a model run.
        """
        self.PYTHON_DIR = str(Path(__file__).parent.parent.resolve())
        self.MODEL_DIR = 's3://script.control.tool'
        self.CASE_DIR = self.MODEL_DIR + r'/cases/' + case_name
        self.DATA_DIR = self.CASE_DIR + r'/data'
        self.CONFIG_DIR = self.DATA_DIR + r'/configs'
        self.RATES_DIR = self.PYTHON_DIR + r'/rates'
        self.LOADPROFILE_DIR = self.PYTHON_DIR + r'/EV_Loads/load_profiles'
        self.TESTFILE_DIR = self.CASE_DIR + r'/test_files'
        self.LOCAL_CASE_DIR = self.PYTHON_DIR + r'/cases/' + case_name
        self.RESULTS_DIR = self.LOCAL_CASE_DIR + r'/results'

        # Create case and case results directories if don't already exist
        for directory in constants.directory_list:
            helpers.make_dir_if_not_exist(getattr(self, directory))

    def create_rate(self, rate_name, model_years, rate_escalator):
        """
        Creates a rate object from the rate_name data file.
        """
        rate_dir = self.RATES_DIR + r'/{0}.csv'.format(rate_name)
        with open(rate_dir) as rate_file:
            rate_data = csv.reader(rate_file)
            rate = rate_class.Rate(rate_data, model_years, rate_escalator)

        return rate

    def read_rate_escalators(self):
        """
        Creates a rate object from the rate_name data file.
        """
        rate_escalator_df = pd.read_csv(self.RATES_DIR + r'/Rate Escalators.csv').set_index("Year")

        return rate_escalator_df

    def create_vehicles(self, annual_filename):
        """
        Creates a Vehicles instance from vehicles_class.py.
            -Calls Vehicles.process_annual_data and Vehicles.process_gasprices.
        :param annual_filename:
        :return:
        """

        vehicles = vehicles_class.Vehicles()

        annual_dir = self.DATA_DIR + '/Annual Values' + r'/{0}.csv'.format(annual_filename)
        annual_data = pd.read_csv(annual_dir, sep="\n", header=None, skiprows=1)
        vehicles.process_annual_data(annual_data)

        gasprice_dir = self.DATA_DIR +  "/Annual Values" + r'/gas_prices.csv'
        gasprice_data = pd.read_csv(gasprice_dir, sep="\n", header=None, skiprows=1)
        vehicles.process_gasprices(gasprice_data)

        return vehicles


    def process_loadprofile(self, loadprofile_name, scalar=1.0):
        """
        Creates a LoadProfile instance based from loadprofile_class.py, based on loadprofile_name.
            -Calls LoadProfile.process_data
        :param scalar: Load profile can be scaled by scalar when process_data() is called.
        :return:
        """
        load_profile = loadprofile_class.LoadProfile(loadprofile_name)
        loadprofile_dir = self.LOADPROFILE_DIR + r'/{0}.csv'.format(loadprofile_name)
        loadprofile_data = pd.read_csv(loadprofile_dir, sep="\n", header=None)
        load_profile.process_data(loadprofile_data, scalar=scalar)

        return load_profile

    def process_energy_marginal_costs(self, energy_mc_name):
        """
        Creates a dictionary of form [year][hour] of energycosts

        :param mc_name: Name of marginal cost file
        :return:
        """

        energy_mc_dir = self.DATA_DIR + "/Marginal Costs" + r'/{0}.csv'.format(energy_mc_name)
        energy_mc_data = pd.read_csv(energy_mc_dir, sep="\n", header=None)
        years = []
        # process open file
        first_row = True


        for row in energy_mc_data.iterrows():
            row = row[1].str.split(",").tolist()

            if first_row:
                for element in row[0][1:]:
                    year = int(element)
                    years.append(year)
                first_row = False
                energy_mc = {year: {} for year in years}

            else:
                index = int(row[0][0])

                for i in range(len(row[0]) - 1):
                    year = years[i]
                    value = float(row[0][i + 1])
                    energy_mc[year][index] = value

        return energy_mc


    def process_emissions(self, emissions_name):
        """
        Creates a dictionary of form [year][hour] of emissions

        :param mc_name: Name of marginal cost file
        :return:
        """

        emissions_dir = self.DATA_DIR + "/Emissions" + r'/{0}.csv'.format(emissions_name)
        emissions_data = pd.read_csv(emissions_dir, sep="\n", header=None)
        # process open file
        first_row = True
        years = []

        for row in emissions_data.iterrows():
            row = row[1].str.split(",").tolist()

            if first_row:
                for element in row[0][1:]:
                    year = int(element)
                    years.append(year)
                first_row = False
                emissions = {year: {} for year in years}

            else:
                index = int(row[0][0])

                for i in range(len(row[0]) - 1):
                    year = years[i]
                    value = float(row[0][i + 1])
                    emissions[year][index] = value

        return emissions

    def process_capacity_marginal_costs(self, capacity_mc_name):
        """
        Creates a dictionary of form [year][hour] of capiticity costs

        :param mc_name: Name of marginal cost file
        :return:
        """

        capacity_mc_dir = self.DATA_DIR + "/Marginal Costs" + r'/{0}.csv'.format(capacity_mc_name)
        capacity_mc_data = pd.read_csv(capacity_mc_dir, sep="\n", header=None)
        # process open file
        first_row = True
        years = []

        for row in capacity_mc_data.iterrows():
            row = row[1].str.split(",").tolist()

            if first_row:
                for element in row[0][1:]:
                    year = int(element)
                    years.append(year)
                first_row = False
                capacity_mc = {year: {} for year in years}

            else:
                index = int(row[0][0])

                for i in range(len(row[0]) - 1):
                    year = years[i]
                    value = float(row[0][i + 1])
                    capacity_mc[year][index] = value

        return capacity_mc


    def process_building_load(self, building_load_name):
        """
        Creates a dictionary of form [year][hour] of building loads

        :param mc_name: Name of marginal cost file
        :return:
        """

        building_load = self.DATA_DIR + '/Building Loads' + r'/{0}.csv'.format(building_load_name)
        building_load_data = pd.read_csv(building_load, sep='\n', header=None)
        # process open file
        first_row = True
        years = []

        for row in building_load_data.iterrows():
            row = row[1].str.split(",").tolist()

            if first_row:
                for element in row[0][1:]:
                    year = int(element)
                    years.append(year)
                first_row = False
                building_load_dict = {year: {} for year in years}

            else:
                index = int(row[0][0])
                for i in range(len(row[0]) - 1):
                    year = years[i]
                    value = float(row[0][i + 1])
                    building_load_dict[year][index] = value

        return building_load_dict

    def process_timesteps(self, model_years):
        """
        Creates a timesteps dictionary for every year in model_years.
            -Timesteps is indexed by each hour of the year from 0 to 8759
            -timesteps[hour] is indexed by each year in model_years
            -Every timesteps[hour][year] value is a subdictionary with:
                -month (1-12)
                -dayofmonth (1-31)
                -hourofday (0-23)
                -is_weekday (bool)
        Timsteps also creates a weekday_weekend_count dictionary for scaling monthly values to annual values
            -weekday_weekend_count is indexed by year, month and 'weekdays'/'weekends'
        :param model_years:
        :return:
        """

        timesteps_dir = self.DATA_DIR + r'/timesteps.csv'
        timesteps = {i: {} for i in range(8760)}
        weekday_weekend_count = {year: {month: {'weekdays': 0, 'weekends': 0}
                                    for month in range(1,13)}
                                 for year in model_years}

        timesteps_data = pd.read_csv(timesteps_dir, sep="\n", header=None, skiprows=1)

        for row in timesteps_data.iterrows():
            row = row[1].str.split(",").tolist()
            index = int(row[0][0])

            for year in model_years:
                month = int(row[0][1])
                dayofmonth = int(row[0][2])
                hourofday = int(row[0][3])


                calendar_date = datetime.date(year, month, dayofmonth)
                day_of_week = calendar_date.isoweekday()
                is_weekday = day_of_week <= 5

                timesteps[index][year] = {'month': month,
                                            'dayofmonth': dayofmonth,
                                            'hourofday': hourofday,
                                            'is_weekday': is_weekday}

                if is_weekday:
                    weekday_weekend_count[year][month]['weekdays'] += 1
                else:
                    weekday_weekend_count[year][month]['weekends'] += 1

        for year in model_years:
            for month in range(1,13):
                for daytype in ['weekdays', 'weekends']:
                    weekday_weekend_count[year][month][daytype] = weekday_weekend_count[year][month][daytype] / 24.

        return timesteps, weekday_weekend_count


    def create_chargers(self, chargerfile_name):
        """
        Creates a Chargers instance from charger_class.py based on chargerfile_name.
        """

        charger_dir = self.DATA_DIR + "/Annual Values" + r'/{0}.csv'.format(chargerfile_name)

        charger_data = pd.read_csv(charger_dir, sep="\n", header=None, skiprows=1)
        chargers = chargers_class.Chargers(charger_data=charger_data,
                                            public_dcfc_proportion=self.public_dcfc_proportion)

        return chargers


    def read_static_workplace(self):
        """
        TODO
        """
        workplace_dir = self.DATA_DIR + r'/static_workplace_chargers.csv'
        workplace_data = pd.read_csv(workplace_file, sep="\n", header=None)
        first_row = True

        for row in workplace_data.iterrows():
            row = row[1].str.split(",").tolist()
            if first_row:
                self.include_static_workplace = True if row[0][1] in ['True', 'TRUE'] else False
                first_row = False

            else:
                row = row.split("\n")
                year = int(row[0][0])
                value = float(row[0][1])
                self.static_workplace_chargers[year] = value