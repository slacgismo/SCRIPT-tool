from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from past.utils import old_div
from builtins import range
from builtins import object
import file_in
import file_out
import constants
import helpers
import billcalculator_class
import loadprofile_class
import simple_TandD
import time
import constants
from collections import Counter
import pandas as pd
import numpy as np

class ModelInstance(object):

    def __init__(self, case_name):

        start = time.time()
        print('Loading Inputs')

        # Load external inputs for model run
        self.inputs = file_in.MODEL_INPUTS(case_name)


        ### CALCULATE TIMESTEP INPUTS ###

        self.inputs.vehicle_lifetime
        self.model_years = list(range(self.inputs.start_year, self.inputs.end_year + self.inputs.vehicle_lifetime))
        self.inputs.timesteps, self.inputs.weekday_weekend_count = self.inputs.process_timesteps(self.model_years)

        ### CALCULATE TAX CREDITS ###

        self.tax_credit_pv = {year: old_div(self.inputs.tax_credit,(1 + constants.inflation) \
           **(year - self.inputs.start_year)) for year in self.model_years}
        self.bev_tax_credit = {year: old_div(self.inputs.BEV_tax_credit, (1 + constants.inflation) \
                                                             ** (year - self.inputs.start_year)) for year in
                              self.model_years}

        self.phev_tax_credit = {year: old_div(self.inputs.PHEV_tax_credit, (1 + constants.inflation) \
                                                             ** (year - self.inputs.start_year)) for year in
                              self.model_years}

        ### CREATE MODEL ATTRIBUTES ###

        # Create rates
        list_of_rate_names = []
        for sub_dict in list(self.inputs.loadprofile_to_rate.values()):
            for key in list(sub_dict.keys()):
                if key not in list_of_rate_names:
                    list_of_rate_names.append(key)

        # Read in rate escalators file:
        rate_escalators = self.inputs.read_rate_escalators()

        self.rates = {name: self.inputs.create_rate(
            name, self.model_years, rate_escalators[name]) for name in list_of_rate_names}

        # Determine what portion of workplace load falls under each rate
        self.proportions_by_loadprofile_and_rate = self.get_loadprofile_and_rate_proportions()


        # Vehicle processing
        self.vehicles = self.inputs.create_vehicles(self.inputs.vehicles_file)

        self.vehicles.create_adoption_data(self.inputs.first_adoption_year,
                                           self.inputs.end_year, self.inputs.vehicle_lifetime)

        self.vehicles.get_capital_cost(self.model_years)

        self.vehicles.get_tax_credit(self.model_years,
                                     self.inputs.last_taxcredit_year,
                                     self.bev_tax_credit, self.phev_tax_credit,
                                     self.inputs.credit_to_replacements)

        self.vehicles.get_oandm_savings(self.model_years, self.inputs.bev_annual_oandm_savings,
                                        self.inputs.phev_annual_oandm_savings, self.inputs.inflation_rate)

        self.vehicles.get_gasoline_savings(self.model_years, self.inputs.metrictons_CO2_per_gallon,
                                           self.inputs.NOX_per_gallon, self.inputs.PM_10_per_gallon,
                                           self.inputs.SO2_per_gallon, self.inputs.VOC_per_gallon)

        self.vehicles.get_gasoline_consumption(self.model_years,
                                           self.inputs.gallons_per_ice,
                                           self.inputs.gallons_per_ice_year, self.inputs.metrictons_CO2_per_gallon,
                                               self.inputs.end_year, self.vehicles.new_vmt, self.vehicles.phev_vmt,
                                               self.vehicles.bev_vmt)

        # Partition laod profiles by rate and charger
        self.load_profiles_by_rate_and_charger = {}
        for loadprofile_name in self.inputs.loadprofile_names:
            for rate_name in list(self.inputs.loadprofile_to_rate[loadprofile_name].keys()):

                proportion_under_rate = self.inputs.loadprofile_to_rate[loadprofile_name][rate_name]

                loadprofile = self.inputs.process_loadprofile(loadprofile_name, scalar=proportion_under_rate)
                loadprofile.get_day_shapes(self.inputs.timesteps, self.model_years)
                loadprofile.expand_loadprofiles(
                    list(range(min(self.vehicles.adoption_years),self.inputs.end_year + self.vehicles.vehicle_lifetime)),
                    self.vehicles)
                loadprofile_charger = self.inputs.loadprofile_to_charger[loadprofile_name]
                self.load_profiles_by_rate_and_charger[(loadprofile_name, rate_name, loadprofile_charger)] = loadprofile

        # Hourly Marginal Cost Processing
        self.aggregate_load = {}
        hours = list(range(8760))
        # Inputs for Building Load
        self.public_building_load = self.inputs.process_building_load('public_building_load')
        self.workplace_building_load = self.inputs.process_building_load('workplace_building_load')
        self.dcfc_building_load = self.inputs.process_building_load('dcfc_building_load')

        for year in self.model_years:
            self.aggregate_load[year] = {}

        for loadprofile in self.load_profiles_by_rate_and_charger.values():

            for year in self.model_years:
                for hour in hours:
                    try:
                        self.aggregate_load[year][hour] += loadprofile.annual_load[year][hour] * 1000
                    except:
                        self.aggregate_load[year][hour] = loadprofile.annual_load[year][hour] * 1000

        self.energy_mc = self.inputs.process_energy_marginal_costs('energy_mc')
        # self.ghg_mc = self.inputs.process_energy_marginal_costs('ghg_mc')
        self.generation_mc = self.inputs.process_capacity_marginal_costs('generation_mc')
        self.distribution_mc = self.inputs.process_energy_marginal_costs('distribution_mc')
        self.transmission_mc = self.inputs.process_energy_marginal_costs('transmission_mc')
        self.CO2_emissions = self.inputs.process_emissions('CO2_emissions')
        self.NOX_emissions = self.inputs.process_emissions('NOX_emissions')
        self.PM10_emissions = self.inputs.process_emissions('PM10_emissions')
        self.SO2_emissions = self.inputs.process_emissions('SO2_emissions')
        self.VOC_emissions = self.inputs.process_emissions('VOC_emissions')

        # Aggregate load profiles by charger type
        self.workplace_loadprofile = None
        self.res_loadprofile = None
        self.publicl2_loadprofile = None
        self.dcfc_loadprofile = None
        self.aggregate_loads_by_charger()

        aggregate_load = {}
        self.peak_demand_5to9_pm = {}
        # typenames = ['avg_weekday', 'avg_weekend', 'peak_shape']
        typenames = ['avg_weekday']
        for year in self.model_years:
            aggregate_load[year] = {}
            self.peak_demand_5to9_pm[year] = 0
            for hour in range(24):
                aggregate_load[year][hour] = {}
                for type in typenames:
                    aggregate_load[year][hour][type] = 0

        self.annual_energy_supply_cost_dict, self.distribution_dict, self.transmission_dict, self.energy_dict, self.ghg_dict,\
        self.capacity_dict, self.CO2_emissions_dict, \
        self.NOX_emissions_dict, self.PM10_emissions_dict, self.SO2_emissions_dict, \
        self.VOC_emissions_dict = ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})

        for year in self.model_years:

            self.annual_energy_supply_cost_dict[year] = 0
            self.distribution_dict[year] = 0
            self.CO2_emissions_dict[year] = 0
            self.NOX_emissions_dict[year] = 0
            self.PM10_emissions_dict[year] = 0
            self.SO2_emissions_dict[year] = 0
            self.VOC_emissions_dict[year] = 0


        for loadprofile in \
            [self.workplace_loadprofile, self.res_loadprofile, self.publicl2_loadprofile, self.dcfc_loadprofile]:
            data = [['Type', 'Hour'] + self.model_years]
            aggregate_data = [['Type', 'Hour'] + self.model_years]
            # for typename, dictionary in [('avg_weekday', loadprofile.avg_weekday),
            #                              ('avg_weekend', loadprofile.avg_weekend),
            #                              ('peak_shape', loadprofile.peak_shape)]:
            for typename, dictionary in [('avg_weekday', loadprofile.avg_weekday)]:
                for hour in range(24):
                    newrow = [typename, hour] + [dictionary[year][hour] for year in self.model_years]
                    data.append(newrow)
                for year in self.model_years:
                    for hour in range(24):
                        aggregate_load[year][hour][typename] += dictionary[year][hour]
                        if 16 < hour < 21:
                            self.peak_demand_5to9_pm[year] = max(self.peak_demand_5to9_pm[year], dictionary[year][hour])

            file_out.export_loadprofiles(self, data, loadprofile.name)
        for typename in typenames:
            for hour in range(24):
                aggregate_row = [typename, hour] + [aggregate_load[year][hour][typename] for year in self.model_years]
                aggregate_data.append(aggregate_row)

        file_out.export_loadprofiles(self, aggregate_data, 'aggregate')

        # Create annual energy supply cost dict if Marginal Costs Exist
        annual_energy_supply_cost_dict, distribution_dict, transmission_dict, energy_dict, ghg_dict, capacity_dict, CO2_emissions_dict,\
        NOX_emissions_dict, PM10_emissions_dict, SO2_emissions_dict,\
        VOC_emissions_dict = loadprofile_class.generate_annual_stream_from_load(
            self.aggregate_load, self.energy_mc, self.generation_mc, self.distribution_mc, self.transmission_mc,
            self.CO2_emissions, self.NOX_emissions, self.PM10_emissions, self.SO2_emissions,
            self.VOC_emissions, self.vehicles.sales, self.inputs.dcfc_EVSE_ratio,
            self.inputs.DCFC_cluster_size_per_upgrade, self.inputs.DCFC_distribution_upgrade_cost, self.model_years)

        self.annual_energy_supply_cost_dict = dict(Counter(self.annual_energy_supply_cost_dict) +
                                                   Counter(annual_energy_supply_cost_dict))

        self.energy_dict = dict(Counter(self.energy_dict) +
                                      Counter(energy_dict))

        self.ghg_dict = dict(Counter(self.ghg_dict) +
                                      Counter(ghg_dict))

        self.capacity_dict = dict(Counter(self.capacity_dict) +
                                      Counter(capacity_dict))

        self.distribution_dict = dict(Counter(self.distribution_dict) +
                                                   Counter(distribution_dict))
        self.transmission_dict = dict(Counter(self.transmission_dict) +
                                      Counter(transmission_dict))

        self.t_and_d_dict = dict(Counter(self.transmission_dict) +
                                      Counter(self.distribution_dict))
        self.CO2_emissions_dict = dict(Counter(self.CO2_emissions_dict) +
                                                   Counter(CO2_emissions_dict))
        self.NOX_emissions_dict = dict(Counter(self.NOX_emissions_dict) +
                                                   Counter(NOX_emissions_dict))
        self.PM10_emissions_dict = dict(Counter(self.PM10_emissions_dict) +
                                                   Counter(PM10_emissions_dict))
        self.SO2_emissions_dict = dict(Counter(self.SO2_emissions_dict) +
                                                   Counter(SO2_emissions_dict))
        self.VOC_emissions_dict = dict(Counter(self.VOC_emissions_dict) +
                                                   Counter(VOC_emissions_dict))

        # Chargers
        self.chargers = self.inputs.create_chargers(self.inputs.charger_name)

        # Use Pro Lite Method to get EVSE Adoption

        if self.inputs.pro_lite_EVSE_method:
            years = list(range(min(self.vehicles.adoption_years), self.inputs.end_year + self.vehicles.vehicle_lifetime))
            self.chargers.get_populations_from_pro_lite(self.inputs.work_EVSE_ratio, self.inputs.public_l2_EVSE_ratio,
                                                        self.inputs.dcfc_EVSE_ratio, years, self.vehicles)


            self.chargers.get_pro_lite_workplace_l2_sales(start_year=min(self.vehicles.adoption_years),
                                                 end_year=self.inputs.end_year,
                                                 vehicle_lifetime=self.inputs.vehicle_lifetime,
                                                 vehicle_sales=self.vehicles.sales,
                                                 work_EVSE_ratio=self.inputs.work_EVSE_ratio)

            self.chargers.get_pro_lite_public_l2_sales(start_year=min(self.vehicles.adoption_years),
                                              end_year=self.inputs.end_year,
                                              vehicle_lifetime=self.inputs.vehicle_lifetime,
                                              vehicle_sales=self.vehicles.sales,
                                              public_EVSE_ratio=self.inputs.public_l2_EVSE_ratio)
            self.chargers.get_pro_lite_dcfc_sales(start_year=min(self.vehicles.adoption_years),
                                         end_year=self.inputs.end_year,
                                         vehicle_lifetime=self.inputs.vehicle_lifetime,
                                         vehicle_sales=self.vehicles.sales,
                                         DCFC_EVSE_ratio=self.inputs.dcfc_EVSE_ratio)

            self.chargers.get_base_cost_with_replacement(self.model_years,  self.inputs.homel2_makeready,
                                                         self.inputs.homel2_evse_cost, self.inputs.homel2_reduction,
                                                         self.inputs.workl2_makeready, self.inputs.workl2_evse_cost,
                                                         self.inputs.workl2_reduction, self.inputs.publicl2_makeready, self.inputs.publicl2_evse_cost,
                                                         self.inputs.publicl2_reduction, self.inputs.dcfc_makeready, self.inputs.dcfc_evse_cost, self.inputs.DCFC_cluster_size_per_upgrade,
                                                         self.inputs.dcfc_reduction, self.inputs.inflation_rate)

        else:
            # Load-based charger split methodology

            self.chargers.static_workplace_chargers = self.inputs.static_workplace_chargers

            self.chargers.get_res_sales(vehicles=self.vehicles,
                                        start_year=min(self.vehicles.adoption_years),
                                        end_year=self.inputs.end_year + self.vehicles.vehicle_lifetime - 1)

            self.chargers.get_workplace(workplace_loadprofile=self.workplace_loadprofile,
                                        start_year=min(self.vehicles.adoption_years),
                                        adoption_final_year = self.inputs.end_year,
                                        end_year=self.inputs.end_year + self.vehicles.vehicle_lifetime - 1,
                                        include_static=self.inputs.include_static_workplace,
                                        cap_per_plug = self.inputs.workl2_cap_per_plug,
                                        workl2_portsperEVSE = self.inputs.workl2_portsperEVSE)

            self.chargers.get_workplace_l2_sales(start_year=min(self.vehicles.adoption_years),
                                                 end_year=self.inputs.end_year,
                                                 vehicle_lifetime=self.inputs.vehicle_lifetime)

            self.chargers.get_public(start_year=min(self.vehicles.adoption_years),
                                     end_year=self.inputs.end_year + self.vehicles.vehicle_lifetime - 1,
                                     vehicle_lifetime=self.inputs.vehicle_lifetime,
                                     publicl2_portsperEVSE=self.inputs.publicl2_portsperEVSE)

            self.chargers.get_public_l2(start_year=min(self.vehicles.adoption_years),
                                        end_year=self.inputs.end_year + self.vehicles.vehicle_lifetime - 1,
                                        include_static=self.inputs.include_static_workplace)

            self.chargers.get_public_l2_sales(start_year=min(self.vehicles.adoption_years),
                                              end_year=self.inputs.end_year,
                                              vehicle_lifetime=self.inputs.vehicle_lifetime)

            self.chargers.get_base_cost(self.model_years,
                                        self.inputs.homel2_startprice,
                                        self.inputs.homel2_reduction,
                                        self.inputs.workl2_startprice,
                                        self.inputs.workl2_reduction,
                                        self.inputs.publicl2_startprice,
                                        self.inputs.publicl2_reduction,
                                        self.inputs.dcfc_startprice,
                                        self.inputs.dcfc_reduction)

        # Determine charger population breakdown by load profile
        self.division_of_chargers = self.divide_chargers()

        # Building Load Methodology
        hours = list(range(8760))

        self.total_work_load = {}
        self.total_public_load = {}
        self.dcfc_meter_load = {}

        for year in self.model_years:
            self.total_work_load[year] = {}
            self.total_public_load[year] = {}
            self.dcfc_meter_load[year] = {}
            for hour in hours:
                try:
                    self.total_work_load[year][hour] += self.workplace_loadprofile.annual_load[year][hour] * \
                                                        (old_div(self.inputs.workl2_chrgrspermeter,
                                                         self.chargers.workplace_evses[year]))

                    self.total_public_load[year][hour] += self.publicl2_loadprofile.annual_load[year][hour] * \
                                                        (old_div(self.inputs.publicl2_chrgrspermeter,
                                                         self.chargers.public_l2_evses[year]))
                    self.dcfc_meter_load[year][hour] += self.dcfc_loadprofile.annual_load[year][hour] * \
                                                        (old_div(self.inputs.dcfc_chrgrspermeter,
                                                         self.chargers.dcfc_evses[year]))
                except:
                    try:
                        self.total_work_load[year][hour] = self.workplace_building_load[year][hour] + \
                                                           (self.workplace_loadprofile.annual_load[year][hour] * \
                                                            (old_div(self.inputs.workl2_chrgrspermeter,
                                                             self.chargers.workplace_evses[year])))
                    except ZeroDivisionError:
                        self.total_work_load[year][hour] = 0
                    try:
                        self.total_public_load[year][hour] = self.public_building_load[year][hour] + \
                                                           (self.publicl2_loadprofile.annual_load[year][hour] * \
                                                            (old_div(self.inputs.publicl2_chrgrspermeter,
                                                             self.chargers.public_l2_evses[year])))
                    except ZeroDivisionError:
                        self.total_public_load[year][hour] = 0

                    try:
                        self.dcfc_meter_load[year][hour] = self.dcfc_building_load[year][hour] + \
                                                           (self.dcfc_loadprofile.annual_load[year][hour] * \
                                                            (old_div(self.inputs.dcfc_chrgrspermeter,
                                                             self.chargers.dcfc_evses[year])))
                    except ZeroDivisionError:
                        self.dcfc_meter_load[year][hour] = 0

        self.workplace_peak_hour = {}
        self.dcfc_peak_hour = {}
        self.publicl2_peak_hour = {}
        for year in self.model_years:
            self.workplace_peak_hour[year] = self.calculate_demand_peak_hour(self.total_work_load, year)
            self.dcfc_peak_hour[year] = self.calculate_demand_peak_hour(self.dcfc_meter_load, year)
            self.publicl2_peak_hour[year] = self.calculate_demand_peak_hour(self.total_public_load, year)

        # Bill calculation
        self.total_revenue = {}
        self.volumetric_revenue = {}
        self.demand_revenue = {}
        self.res_revenue = {}
        self.work_revenue = {}
        self.publicl2_revenue = {}
        self.dcfc_revenue = {}

        for loadprofile_name, rate_name, charger_name in list(self.division_of_chargers.keys()):
            loadprofile = self.load_profiles_by_rate_and_charger[(loadprofile_name, rate_name, charger_name)]
            rate = self.rates[rate_name]
            charger_proportions = self.division_of_chargers[(loadprofile_name, rate_name, charger_name)]
            chargers_per_meter = self.inputs.chargers_per_meter[charger_name]

            bill_calculator = billcalculator_class.BillCalculator(loadprofile=loadprofile,
                                                                  rate=rate,
                                                                  charger_name=charger_name,
                                                                  charger_proportions=charger_proportions,
                                                                  chargers=self.chargers,
                                                                  chargers_per_meter=chargers_per_meter)

            # is_residential = True if charger_name == 'Residential L2' else False
            bill_calculator.calculate_bill(self.model_years, self.inputs.weekday_weekend_count,
                                           self.workplace_peak_hour, self.dcfc_peak_hour,
                                           self.publicl2_peak_hour, charger_name)

            for year in sorted(bill_calculator.annual_bill.keys()):
                # if year in list(self.total_revenue.keys()):
                #     self.total_revenue[year] += bill_calculator.annual_bill[year]
                # else:
                #     self.total_revenue[year] = bill_calculator.annual_bill[year]

                if year in list(self.volumetric_revenue.keys()):
                    self.volumetric_revenue[year] += bill_calculator.weekday_energy_bill[year] + bill_calculator.weekend_energy_bill[year]
                else:
                    self.volumetric_revenue[year] = bill_calculator.weekday_energy_bill[year] + bill_calculator.weekend_energy_bill[year]

                # if year in list(self.demand_revenue.keys()):
                #     self.demand_revenue[year] += bill_calculator.total_monthly_max_bill[year] + \
                #                                  bill_calculator.total_onpeak_max_bill[year] + \
                #                                  bill_calculator.total_partpeak_max_bill1[year] + \
                #                                  bill_calculator.total_partpeak_max_bill2[year]
                #
                #
                # else:
                #     self.demand_revenue[year] = bill_calculator.total_monthly_max_bill[year] + \
                #                                  bill_calculator.total_onpeak_max_bill[year] + \
                #                                  bill_calculator.total_partpeak_max_bill1[year] + \
                #                                  bill_calculator.total_partpeak_max_bill2[year]

                if year in list(self.demand_revenue.keys()):
                    self.demand_revenue[year] += bill_calculator.total_monthly_max_bill[year]

                else:
                    self.demand_revenue[year] = bill_calculator.total_monthly_max_bill[year]

                if (charger_name == 'Residential L2') or (charger_name == 'Residential L1'):
                    if year in list(self.res_revenue.keys()):
                        self.res_revenue[year] += bill_calculator.annual_bill[year]
                    else:
                        self.res_revenue[year] = bill_calculator.annual_bill[year]

                if charger_name == 'Workplace L2':
                    if year in list(self.work_revenue.keys()):
                        self.work_revenue[year] += bill_calculator.annual_bill[year]
                    else:
                        self.work_revenue[year] = bill_calculator.annual_bill[year]

                if charger_name == 'Public L2':
                    if year in list(self.publicl2_revenue.keys()):
                        self.publicl2_revenue[year] += bill_calculator.annual_bill[year]
                    else:
                        self.publicl2_revenue[year] = bill_calculator.annual_bill[year]

                if charger_name == 'DCFC':
                    if year in list(self.dcfc_revenue.keys()):
                        self.dcfc_revenue[year] += bill_calculator.annual_bill[year]
                    else:
                        self.dcfc_revenue[year] = bill_calculator.annual_bill[year]


        for year in sorted(bill_calculator.annual_bill.keys()):
            if year in list(self.total_revenue.keys()):
                self.total_revenue[year] += self.dcfc_revenue[year] + self.publicl2_revenue[year] + \
                                            self.work_revenue[year] + self.res_revenue[year]
            else:
                self.total_revenue[year] = self.dcfc_revenue[year] + self.publicl2_revenue[year] + \
                                           self.work_revenue[year] + self.res_revenue[year]

        # T and D
        if self.inputs.allEVload_onTandD:
            tandd_years = list(range(self.inputs.start_year, self.inputs.end_year + self.vehicles.vehicle_lifetime))
        else:
            tandd_years = \
                list(range(min(self.vehicles.adoption_years), self.inputs.end_year + self.vehicles.vehicle_lifetime))

        # self.TandD_instance = simple_TandD.SimpleTandD(tandd_years,
        #                                                self.inputs.cost_per_incremental_kw,
        #                                                self.load_profiles_by_rate_and_charger)


        file_out.export_results(self)
        end = time.time()
        elapsed = end - start
        print('Model ran in %s seconds (%s minutes)' % (elapsed, elapsed/60))
        print('Model has finished running, please exit out of the command window to view results')


    def divide_chargers(self):

        loadprofiles_by_charger = {'Residential L2': [],
                                   'Residential L1': [],
                                   'Public L2': [],
                                   'DCFC': [],
                                   'Workplace L2': []}
        peaksum_by_charger = {'Residential L2': {},
                              'Residential L1': {},
                                   'Public L2': {},
                                   'DCFC': {},
                                   'Workplace L2': {}}

        # First find the peak of each load profile for a given charger type and sum them by charger type
        peaks_by_loadprofile_rate_charger = {}
        for (loadprofile_name, rate_name, loadprofile_charger) in list(self.load_profiles_by_rate_and_charger.keys()):

            charger_tuple = (loadprofile_name, rate_name, loadprofile_charger)

            loadprofiles_by_charger[loadprofile_charger].append(charger_tuple)
            peaks_by_loadprofile_rate_charger[charger_tuple] = {}

            loadprofile = self.load_profiles_by_rate_and_charger[(loadprofile_name, rate_name, loadprofile_charger)]

            for year in self.model_years:
                peak = max(loadprofile.peak_shape[year].values())
                peaks_by_loadprofile_rate_charger[charger_tuple][year] = peak

                try:
                    peaksum_by_charger[loadprofile_charger][year] += peak
                except KeyError:
                    peaksum_by_charger[loadprofile_charger][year] = peak

        # Then divide by the total to get the percentage of non-coincident peaks in each charger tuple
        peakproportions_by_loadprofile_rate_charger = {}
        for (loadprofile_name, rate_name, loadprofile_charger) in list(self.load_profiles_by_rate_and_charger.keys()):

            charger_tuple = (loadprofile_name, rate_name, loadprofile_charger)
            peakproportions_by_loadprofile_rate_charger[charger_tuple] = {}

            for year in self.model_years:
                tuple_peak = peaks_by_loadprofile_rate_charger[charger_tuple][year]
                total_peak = peaksum_by_charger[loadprofile_charger][year]

                if total_peak == 0:
                    proportion = 1.0 / len(loadprofiles_by_charger[loadprofile_charger])
                else:
                    proportion = old_div(tuple_peak, total_peak)

                peakproportions_by_loadprofile_rate_charger[charger_tuple][year] = proportion

        return peakproportions_by_loadprofile_rate_charger


    def aggregate_loads_by_charger(self):

        self.workplace_loadprofile = loadprofile_class.LoadProfile(name='AllWorkplace')
        self.res_loadprofile = loadprofile_class.LoadProfile(name='AllResidential')
        self.publicl2_loadprofile = loadprofile_class.LoadProfile(name='AllPublicL2')
        self.dcfc_loadprofile = loadprofile_class.LoadProfile(name='AllDCFC')

        for (loadprofile_name, rate_name, loadprofile_charger) in list(self.load_profiles_by_rate_and_charger.keys()):

            loadprofile_to_add = self.load_profiles_by_rate_and_charger[(loadprofile_name,
                                                                         rate_name,
                                                                         loadprofile_charger)]

            if loadprofile_charger == 'Workplace L2':
                self.workplace_loadprofile = \
                    loadprofile_class.add_loadprofiles('AllWorkplace',
                                                       self.workplace_loadprofile,
                                                       loadprofile_to_add,
                                                       self.inputs.timesteps,
                                                       self.model_years,
                                                       self.vehicles)


            elif (loadprofile_charger == 'Residential L2') or (loadprofile_charger == 'Residential L1'):
                self.res_loadprofile = \
                    loadprofile_class.add_loadprofiles('AllResidential',
                                                       self.res_loadprofile,
                                                       loadprofile_to_add,
                                                       self.inputs.timesteps,
                                                       self.model_years,
                                                       self.vehicles)

            elif loadprofile_charger == 'Public L2':
                self.publicl2_loadprofile = \
                    loadprofile_class.add_loadprofiles('AllPublicL2',
                                                       self.publicl2_loadprofile,
                                                       loadprofile_to_add,
                                                       self.inputs.timesteps,
                                                       self.model_years,
                                                       self.vehicles)

            else:
                self.dcfc_loadprofile = \
                    loadprofile_class.add_loadprofiles('AllDCFC',
                                                       self.dcfc_loadprofile,
                                                       loadprofile_to_add,
                                                       self.inputs.timesteps,
                                                       self.model_years,
                                                       self.vehicles)



    def get_loadprofile_and_rate_proportions(self):

        workplace_loadprofile_names = \
            [key for key in self.inputs.loadprofile_to_charger
             if self.inputs.loadprofile_to_charger[key] == 'Workplace L2']

        res_loadprofile_names = \
            [key for key in self.inputs.loadprofile_to_charger
             if self.inputs.loadprofile_to_charger[key] == 'Residential L2' or 'Residential L1']

        rate_proportions = {'Workplace': {},
                            'Residential': {}}


        workplace_total = 0.0

        for loadprofile_name in workplace_loadprofile_names:

            for rate_name in list(self.inputs.loadprofile_to_rate[loadprofile_name].keys()):

                workplace_total += self.inputs.loadprofile_to_rate[loadprofile_name][rate_name]

                try:
                    rate_proportions['Workplace'][(loadprofile_name, rate_name)] \
                        += self.inputs.loadprofile_to_rate[loadprofile_name][rate_name]
                except KeyError:
                    rate_proportions['Workplace'][(loadprofile_name, rate_name)] \
                        = self.inputs.loadprofile_to_rate[loadprofile_name][rate_name]

        residential_total = 0.0
        for loadprofile_name in res_loadprofile_names:
            for rate_name in list(self.inputs.loadprofile_to_rate[loadprofile_name].keys()):

                residential_total += self.inputs.loadprofile_to_rate[loadprofile_name][rate_name]

                try:
                    rate_proportions['Residential'][(loadprofile_name, rate_name)] \
                        += self.inputs.loadprofile_to_rate[loadprofile_name][rate_name]
                except KeyError:
                    rate_proportions['Residential'][(loadprofile_name, rate_name)] \
                        = self.inputs.loadprofile_to_rate[loadprofile_name][rate_name]


        for loadprofile_name in self.inputs.loadprofile_names:
            for rate_name in list(self.rates.keys()):

                if (loadprofile_name, rate_name) in list(rate_proportions['Workplace'].keys()):
                    rate_proportions['Workplace'][(loadprofile_name, rate_name)] \
                        = old_div(rate_proportions['Workplace'][(loadprofile_name, rate_name)], workplace_total)

                if (loadprofile_name, rate_name) in list(rate_proportions['Residential'].keys()):
                    rate_proportions['Residential'][(loadprofile_name, rate_name)] \
                        = old_div(rate_proportions['Residential'][(loadprofile_name, rate_name)], residential_total)

        return rate_proportions


    def calculate_demand_peak_hour(self, building_location, year):
        """
        For SRP Project, calculate hour where (building load + ev load) reaches a peak
        :param building_location:
        :param year:
        :return:
        """
        peak_timestep = helpers.get_max_index(building_location[year])

        month = self.inputs.timesteps[peak_timestep][year]['month']
        dayofmonth = self.inputs.timesteps[peak_timestep][year]['dayofmonth']

        peak_timesteps = sorted([i for i in list(self.inputs.timesteps.keys()) if self.inputs.timesteps[i][year]['month'] == month
                                 and self.inputs.timesteps[i][year]['dayofmonth'] == dayofmonth])
        max_load = {}
        peak_isweekday = {}
        max_load[year] = {i: building_location[year][peak_timesteps[i]] for i in range(24)}
        peak_isweekday[year] = self.inputs.timesteps[peak_timesteps[0]][year]['is_weekday']

        peak_shape_kw = {i: max_load[year][i] * 1000 for i in range(24)}

        return helpers.get_max_index(peak_shape_kw)