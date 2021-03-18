from __future__ import unicode_literals

from builtins import str
from builtins import range
from builtins import object
import constants

class Rate(object):

    def __init__(self, data, model_years, rate_escalator):

        self.name = str()
        self.description = str()
        self.data_author = str()
        self.fixed_monthly_charges = float()
        self.meter_day_charge = float()
        self.rate_escalators = rate_escalator.to_dict()
        self.energy_charges = {}
        self.demand_charges = {}
        self.demand_charge_periods = {(category, month): [] for month in range(1,13)
                                      for category in list(constants.demandcharge_components.values())
                                      if category != 'monthly_max'}

        self.data_to_rate(data, model_years)


    def data_to_rate(self, data, model_years):
        """
        Fills out attributes of rate by loading data for rate_data_year and then calling escalate_rate()
        """
        i = 0
        base_energy = {}
        base_demand = {}

        for row in data:

            # Text elements of rate
            if i in range(1,4):
                name = row[0]
                value = row[1]
                setattr(self, name, value)

            # Fixed charges of rate
            elif i in range(4, 6):
                name = row[0]
                value = float(row[1])
                setattr(self, name, value)

            # Energy charges of rate
            elif i in range(42, 282):

                daytype = row[1]
                hour = int(row[2])
                for j in range(0,12):
                    month = j+1
                    value = 0. if row[j+3] == '' else float(row[j+3])
                    try:
                        base_energy[(month, hour, daytype)] += value
                    except:
                        base_energy[(month, hour, daytype)] = value

            # Demand charges of rate
            elif i in range(285, 525):
                component = int(row[0])
                category = constants.demandcharge_components[component]
                daytype = row[1]
                hour = int(row[2])
                for j in range(0,12):
                    month = j+1
                    value = 0. if row[j+3] == '' else float(row[j+3])
                    base_demand[(category, month, hour, daytype)] = value

                    if daytype == 'workday':
                        is_weekday = True
                    else:
                        is_weekday = False

                    if value != 0 and category != 'monthly_max':
                        if (hour, daytype) not in self.demand_charge_periods[(category, month)]:
                            self.demand_charge_periods[(category, month)].append((hour, is_weekday))

            i += 1

        self.expand_escalators(model_years)
        self.escalate_rate(model_years, base_energy, base_demand)


    def expand_escalators(self, model_years):

        min_escalator_year = min(self.rate_escalators.keys())
        max_escalator_year = max(self.rate_escalators.keys())

        for year in model_years:
            if year < min_escalator_year:
                self.rate_escalators[year] = self.rate_escalators[min_escalator_year]
            elif year > max_escalator_year:
                self.rate_escalators[year] = self.rate_escalators[max_escalator_year]

    def escalate_rate(self, model_years, base_energy, base_demand):

        energy_charges = {}
        demand_charges = {}

        for year in model_years:
            energy_charges[year] = {}
            demand_charges[year] = {}
            escalation_factor = self.rate_escalators[year]

            for key in list(base_energy.keys()):
                value = base_energy[key]
                escalated_value = value * escalation_factor
                energy_charges[year][key] = escalated_value

            for key in list(base_demand.keys()):
                value = base_demand[key]
                escalated_value = value * escalation_factor
                demand_charges[year][key] = escalated_value

        self.demand_charges = demand_charges
        self.energy_charges = energy_charges