from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from past.utils import old_div
from builtins import range
from builtins import object
import helpers
import constants
import copy

class LoadProfile(object):

    def __init__(self, name):

        self.name = name
        self.annual_load = {}
        self.avg_weekday = {}
        self.avg_weekend = {}
        self.peak_shape = {}
        self.peak_isweekday = {}
        self.flexload_added = False


    def is_empty(self):

        if self.annual_load == {}:
            if self.avg_weekday == {}:
                if self.avg_weekend == {}:
                    if self.peak_shape == {}:
                        if self.peak_isweekday == {}:
                            return True


    def missing_annual_load(self):

        nonzero_avg = False
        for year in list(self.avg_weekday.keys()):
            for hour in list(self.avg_weekday[year].keys()):
                if self.avg_weekday[year][hour] != 0 \
                        or self.avg_weekend[year][hour] != 0 \
                        or self.peak_shape[year][hour] != 0:
                    nonzero_avg = True

        if self.annual_load == {} and nonzero_avg:
            return True
        else:
            return False



    def process_data(self, data, scalar=1.0):
        """
        Given data from a load profile file, process_data() organizes the load profile into a annual_load dictionary
        with year as the outer key and index as the inner key. The load profile is the value.

        scalar can be used to scale the load profile down to model partitioned load profiles.
        """
        first_row = True
        years = []
        count = 0

        for row in data.iterrows():
            row = row[1].str.split(",").tolist()

            if first_row:
                for element in row[0][1:]:
                    year_str = element.replace('MW_', '')
                    year = int(year_str)
                    years.append(year)
                self.annual_load = {year: {} for year in years}
                first_row = False

            else:
                index = int(row[0][0])

                for i in range(len(row[0])-1):
                    year = years[i]
                    value = float(row[0][i+1])
                    self.annual_load[year][index] = value * scalar


    def get_day_shapes(self, timesteps, model_years):

        self.get_avg_days(timesteps, model_years)
        self.get_peak_day(timesteps, model_years)


    def get_avg_days(self, timesteps, model_years):
        """
        Calculates the average weekday and weekend load shape, for each year, and saves them in avg_weekday and
        avg_weekend dictionaries, respectively, indexed by year.
        """

        for year in model_years:

            try:
                weekday_count = {i: 0 for i in range(24)}
                weekday_sum = {i: 0 for i in range(24)}

                weekend_count = {i: 0 for i in range(24)}
                weekend_sum = {i: 0 for i in range(24)}

                for timestep in list(timesteps.keys()):
                    is_weekday = timesteps[timestep][year]['is_weekday']
                    hour_of_day = timesteps[timestep][year]['hourofday']
                    load = self.annual_load[year][timestep]

                    if is_weekday:
                        weekday_count[hour_of_day] += 1
                        weekday_sum[hour_of_day] += load
                    else:
                        weekend_count[hour_of_day] += 1
                        weekend_sum[hour_of_day] += load

                self.avg_weekday[year] = {i: old_div(weekday_sum[i], weekday_count[i]) for i in range(24)}
                self.avg_weekend[year] = {i: old_div(weekend_sum[i], weekend_count[i]) for i in range(24)}

            except KeyError:
                self.avg_weekday[year] = {i: 0 for i in range(24)}
                self.avg_weekend[year] = {i: 0 for i in range(24)}

    def get_peak_day(self, timesteps, model_years):

        for year in model_years:

            try:
                peak_timestep = helpers.get_max_index(self.annual_load[year])
                month = timesteps[peak_timestep][year]['month']
                dayofmonth = timesteps[peak_timestep][year]['dayofmonth']
                peak_timesteps = sorted([i for i in list(timesteps.keys()) if timesteps[i][year]['month'] == month
                    and timesteps[i][year]['dayofmonth'] == dayofmonth])
                self.peak_shape[year] = {i: self.annual_load[year][peak_timesteps[i]] for i in range(24)}
                self.peak_isweekday[year] = timesteps[peak_timesteps[0]][year]['is_weekday']

            except KeyError:
                self.peak_shape[year] = {i: 0 for i in range(24)}
                self.peak_isweekday[year] = timesteps[peak_timesteps[0]][year]['is_weekday']


    def expand_loadprofiles(self, model_years, vehicles):
        """
        Given the annual_load attribute, model_years and a vehicle population over time, expand_loadprofiles() will
        expand the annual_load attribute into the missing model years by scaling based on either the first or last
        year in annual_load.
        """

        first_loadprofile_year = min(self.annual_load.keys())
        last_loadprofile_year = max(self.annual_load.keys())

        for year in model_years:

            if year not in list(self.annual_load.keys()):
                pop_in_year = vehicles.population[year]

                if year < first_loadprofile_year:
                    template_year = first_loadprofile_year
                else:
                    template_year = last_loadprofile_year

                pop_in_loadprofile = vehicles.population[template_year]
                try:
                    scalar = old_div(pop_in_year,pop_in_loadprofile)
                except:
                    scalar = 0

                scaled_avg_weekday = {i: self.avg_weekday[template_year][i]*scalar for i in range(24)}
                scaled_avg_weekend = {i: self.avg_weekend[template_year][i]*scalar for i in range(24)}
                scaled_peak = {i: self.peak_shape[template_year][i]*scalar for i in range(24)}

                self.avg_weekday[year] = scaled_avg_weekday
                self.avg_weekend[year] = scaled_avg_weekend
                self.peak_shape[year] = scaled_peak
                self.peak_isweekday[year] = self.peak_isweekday[template_year]


def add_loadprofiles(name, loadprofile1, loadprofile2, timesteps, model_years, vehicles):

    if loadprofile1.is_empty():
        loadprofile2.name = name
        return copy.deepcopy(loadprofile2)

    elif loadprofile2.is_empty():
        loadprofile1.name = name
        return copy.deepcopy(loadprofile1)

    else:
        new_loadprofile = LoadProfile(name)

        # Combine annual load
        if list(loadprofile1.annual_load.keys()) != list(loadprofile2.annual_load.keys()):
            raise KeyError('Load profiles do not extend over identical years.')
        else:
            for year in list(loadprofile1.annual_load.keys()):
                new_loadprofile.annual_load[year] = {}

                if list(loadprofile1.annual_load[year].keys()) != list(loadprofile2.annual_load[year].keys()):
                    raise KeyError('Load profiles do not extend over identical hours.')
                else:
                    for index in list(loadprofile1.annual_load[year].keys()):
                        new_loadprofile.annual_load[year][index] = \
                            loadprofile1.annual_load[year][index] + loadprofile2.annual_load[year][index]

        # Get day shapes
        new_loadprofile.get_day_shapes(timesteps, model_years)
        new_loadprofile.expand_loadprofiles(model_years, vehicles)

        return new_loadprofile

def generate_annual_stream_from_load(load_profile, energy_marginal_cost, capacity_marginal_cost,
                                     distribution_marginal_cost, transmission_marginial_cost, CO2_emissions, NOX_emissions,
                                     PM10_emissions, SOX_emissions, VOC_emissions, vehicle_sales, dcfc_ratio, dcfc_cluster_size,
                                     dcfc_distribution_upgrade_cost, model_years):

    total_mc = {}
    energy_supply_cost = {}
    energy_cost = {}
    ghg_cost = {}
    capacity_cost = {}
    distribution_cost = {}
    transmission_cost = {}
    CO2_emissions_dict = {}
    NOX_emissions_dict = {}
    PM10_emissions_dict = {}
    SOX_emissions_dict = {}
    VOC_emissions_dict = {}
    dcfc_upgrade_cost_per_cluster = old_div(dcfc_distribution_upgrade_cost, dcfc_cluster_size)

    for year in model_years:
        total_mc[year] = {}
        energy_supply_cost[year] = 0
        energy_cost[year] = 0
        ghg_cost[year] = 0
        capacity_cost[year] = 0
        distribution_cost[year] = 0
        transmission_cost[year] = 0
        CO2_emissions_dict[year] = 0
        NOX_emissions_dict[year] = 0
        PM10_emissions_dict[year] = 0
        SOX_emissions_dict[year] = 0
        VOC_emissions_dict[year] = 0
        distribution_cost[year] += old_div(vehicle_sales[year] * dcfc_upgrade_cost_per_cluster, dcfc_ratio)

        for hour in range(8760):
            total_mc[year][hour] = energy_marginal_cost[year][hour] + capacity_marginal_cost[year][hour]
            energy_supply_cost[year] += total_mc[year][hour] * load_profile[year][hour]
            energy_cost[year] += load_profile[year][hour] * energy_marginal_cost[year][hour]
            # ghg_cost[year] += load_profile[year][hour] * ghg_marginal_cost[year][hour]
            capacity_cost[year] += load_profile[year][hour] * capacity_marginal_cost[year][hour]
            distribution_cost[year] += load_profile[year][hour] * distribution_marginal_cost[year][hour]

            transmission_cost[year] += load_profile[year][hour] * transmission_marginial_cost[year][hour]
            CO2_emissions_dict[year] += load_profile[year][hour] * CO2_emissions[year][hour]
            NOX_emissions_dict[year] += load_profile[year][hour] * NOX_emissions[year][hour]
            PM10_emissions_dict[year] += load_profile[year][hour] * PM10_emissions[year][hour]
            SOX_emissions_dict[year] += load_profile[year][hour] * SOX_emissions[year][hour]
            VOC_emissions_dict[year] += load_profile[year][hour] * VOC_emissions[year][hour]

    return energy_supply_cost, distribution_cost, transmission_cost, energy_cost, ghg_cost,  capacity_cost,\
           CO2_emissions_dict, NOX_emissions_dict, PM10_emissions_dict,\
           SOX_emissions_dict, VOC_emissions_dict
