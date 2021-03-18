from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from past.utils import old_div
from builtins import range
from builtins import object
import helpers
import constants

class BillCalculator(object):

    def __init__(self, loadprofile, rate, charger_name, charger_proportions, chargers, chargers_per_meter):

        self.loadprofile = loadprofile
        self.rate = rate
        self.charger_name = charger_name
        self.charger_proportions = charger_proportions
        self.chargers = chargers
        self.chargers_per_meter = chargers_per_meter

        self.annual_bill = {}
        self.weekday_energy_bill = {}
        self.weekend_energy_bill = {}
        self.total_monthly_max_bill = {}
        self.total_onpeak_max_bill = {}
        self.total_partpeak_max_bill1 = {}
        self.total_partpeak_max_bill2 = {}
        self.fixed_monthly_bill = {}
        self.fixed_daily_bill = {}

    def calculate_bill(self, model_years, weekday_weekend_count,workplace_peak_hour, dcfc_peak_hour,
                                           publicl2_peak_hour, charger_name):

        charger_population_attr = constants.charger_name_to_population_attr[self.charger_name]
        charger_populations = getattr(self.chargers, charger_population_attr)

        for year in model_years:

            avg_weekday_kw = {i: self.loadprofile.avg_weekday[year][i] * 1000 for i in range(24)}
            avg_weekend_kw = {i: self.loadprofile.avg_weekend[year][i] * 1000 for i in range(24)}
            peak_shape_kw = {i: self.loadprofile.peak_shape[year][i] * 1000 for i in range(24)}

            # Weekday volumetric charge
            avg_weekday_charge = {month:
                                      {i: avg_weekday_kw[i] * self.rate.energy_charges[year][(month, i + 1, 'workday')]
                                       for i in range(24)}
                                  for month in range(1,13)}
            weekday_charges = \
                {month: sum(avg_weekday_charge[month].values()) * weekday_weekend_count[year][month]['weekdays']
                 for month in range(1,13)}

            weekday_energy_charge = sum(weekday_charges.values())

            # Weekend volumetric charge
            avg_weekend_charge = {month:
                                      {i: avg_weekend_kw[i] * self.rate.energy_charges[year][(month, i + 1, 'non-workday')]
                                       for i in range(24)}
                                  for month in range(1,13)}
            weekend_charges = \
                {month: sum(avg_weekend_charge[month].values()) * weekday_weekend_count[year][month]['weekends']
                 for month in range(1,13)}
            weekend_energy_charge = sum(weekend_charges.values())

            # Monthly max demand charge

            if charger_name == 'Residential L2' or 'Residential L1':
                peak = max(peak_shape_kw.values())
            elif charger_name == 'Public L2':
                peak = peak_shape_kw[publicl2_peak_hour[year]]
            elif charger_name == 'Workplace L2':
                peak = peak_shape_kw[workplace_peak_hour[year]]
            else:
                peak = peak_shape_kw[dcfc_peak_hour[year]]

            peak_isweekday = self.loadprofile.peak_isweekday[year]
            peak_i = helpers.get_max_index(peak_shape_kw) + 1

            if peak_isweekday:
                daytype = 'workday'
            else:
                daytype = 'non-workday'

            monthly_max_charges = \
                {month: self.rate.demand_charges[year][('monthly_max', month, peak_i, daytype)] * peak
                    for month in range(1, 13)}
            total_monthly_max_charge = sum(monthly_max_charges.values())

            # On-Peak demand charge
            monthly_onpeak_max = {month: 0 for month in range(1,13)}
            monthly_onpeak_hour = {month: 1 for month in range(1,13)}
            monthly_onpeak_daytype = {month: 'workday' for month in range(1,13)}
            monthly_onpeak_charges = {month: 0 for month in range(1,13)}

            for month in range(1,13):
                for i in list(peak_shape_kw.keys()):
                    load_kw = peak_shape_kw[i] * 1000.
                    if (i, peak_isweekday) in self.rate.demand_charge_periods[('peak_max', month)]:
                        if load_kw > monthly_onpeak_max[month]:
                            monthly_onpeak_max[month] = load_kw
                            monthly_onpeak_hour[month] = i + 1
                            monthly_onpeak_daytype[month] = 'workday' if peak_isweekday else 'non-workday'

            for month in range(1,13):
                peak_load = monthly_onpeak_max[month]
                peak_hour = monthly_onpeak_hour[month]
                peak_daytype = monthly_onpeak_daytype[month]

                monthly_onpeak_charges[month] = \
                    self.rate.demand_charges[year][('peak_max', month, peak_hour, peak_daytype)] * peak_load

            total_onpeak_max_charge = sum(monthly_onpeak_charges.values())


            # Partial Peak demand charge #1
            monthly_partpeak_max1 = {month: 0 for month in range(1,13)}
            monthly_partpeak_hour1 = {month: 1 for month in range(1,13)}
            monthly_partpeak_daytype1 = {month: 'workday' for month in range(1,13)}
            monthly_partpeak_charges1 = {month: 0 for month in range(1,13)}

            for month in range(1,13):
                for i in list(peak_shape_kw.keys()):
                    load_kw = peak_shape_kw[i] * 1000.
                    if (i, peak_isweekday) in self.rate.demand_charge_periods[('partpeak_max1', month)]:
                        if load_kw > monthly_partpeak_max1[month]:
                            monthly_partpeak_max1[month] = load_kw
                            monthly_partpeak_hour1[month] = i + 1
                            monthly_partpeak_daytype1[month] = 'workday' if peak_isweekday else 'non-workday'

            for month in range(1,13):
                peak_load = monthly_partpeak_max1[month]
                peak_hour = monthly_partpeak_hour1[month]
                peak_daytype = monthly_partpeak_daytype1[month]

                monthly_partpeak_charges1[month] = \
                    self.rate.demand_charges[year][('partpeak_max1', month, peak_hour, peak_daytype)] * peak_load

            total_partpeak_max_charge1 = sum(monthly_partpeak_charges1.values())


            # Partial Peak demand charge #2
            monthly_partpeak_max2 = {month: 0 for month in range(1, 13)}
            monthly_partpeak_hour2 = {month: 1 for month in range(1, 13)}
            monthly_partpeak_daytype2 = {month: 'workday' for month in range(1, 13)}
            monthly_partpeak_charges2 = {month: 0 for month in range(1, 13)}

            for month in range(1,13):
                for i in list(peak_shape_kw.keys()):
                    load_kw = peak_shape_kw[i] * 1000.
                    if (i, peak_isweekday) in self.rate.demand_charge_periods[('partpeak_max2', month)]:
                        if load_kw > monthly_partpeak_max2[month]:
                            monthly_partpeak_max2[month] = load_kw
                            monthly_partpeak_hour2[month] = i + 1
                            monthly_partpeak_daytype2[month] = 'workday' if peak_isweekday else 'non-workday'

            for month in range(1, 13):
                peak_load = monthly_partpeak_max2[month]
                peak_hour = monthly_partpeak_hour2[month]
                peak_daytype = monthly_partpeak_daytype2[month]

                monthly_partpeak_charges2[month] = \
                    self.rate.demand_charges[year][('peak_max', month, peak_hour, peak_daytype)] * peak_load

            total_partpeak_max_charge2 = sum(monthly_partpeak_charges2.values())

            # Fixed charges

            charger_population = charger_populations[year]
            charger_proportion = self.charger_proportions[year]

            num_chargers = charger_population * charger_proportion
            num_meters = old_div(num_chargers, self.chargers_per_meter)

            fixed_monthly_charges = self.rate.fixed_monthly_charges * self.rate.rate_escalators[year] * 12. * num_meters
            fixed_daily_charges = self.rate.meter_day_charge * self.rate.rate_escalators[year] * 365. * num_meters

            self.weekday_energy_bill[year] = weekday_energy_charge
            self.weekend_energy_bill[year] = weekend_energy_charge
            self.total_monthly_max_bill[year] = total_monthly_max_charge
            self.total_onpeak_max_bill[year] = total_onpeak_max_charge
            self.total_partpeak_max_bill1[year] = total_partpeak_max_charge1
            self.total_partpeak_max_bill2[year] = total_partpeak_max_charge2
            self.fixed_monthly_bill[year] = fixed_monthly_charges
            self.fixed_daily_bill[year] = fixed_daily_charges

            # Sum all bill components
            self.annual_bill[year] = weekday_energy_charge \
                                + weekend_energy_charge \
                                + total_monthly_max_charge \
                                + fixed_monthly_charges + fixed_daily_charges


