from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from past.utils import old_div
from builtins import range
from builtins import object
import helpers

class Chargers(object):

    def __init__(self, charger_data, public_dcfc_proportion):

        self.public_dcfc_proportion = public_dcfc_proportion

        self.port_population = {}
        self.static_workplace_chargers = {}
        self.static_workplace_proportion = {}

        self.res_evses = {}
        self.dcfc_evses = {}
        self.l2_evses = {}
        self.workplace_evses = {}
        self.public_l2_evses = {}

        self.res_evse_sales = {}
        self.l2_sales = {}
        self.public_l2_sales = {}
        self.workplace_evse_sales = {}
        self.dcfc_sales = {}

        self.res_evse_new_sales = {}
        self.public_l2_new_sales = {}
        self.workplace_evse_new_sales = {}
        self.dcfc_new_sales = {}

        self.res_evse_replacements = {}
        self.public_l2_replacements = {}
        self.workplace_evse_replacements = {}
        self.dcfc_replacements = {}

        self.res_cost = {}
        self.l2_cost = {}
        self.public_l2_cost = {}
        self.workplace_l2_cost = {}
        self.dcfc_cost = {}

        self.get_port_population(charger_data)


    def get_port_population(self, charger_data):

        first_row = True

        for row in charger_data.iterrows():
            row = row[1].str.split(",").tolist()
            year = int(row[0][0])
            ports = float(row[0][1])
            self.port_population[year] = ports


    def get_res_sales(self, vehicles, start_year, end_year):

        for year in range(start_year, end_year+1):
            if year in vehicles.adoption_years:
                self.res_evses[year] = vehicles.population[year]
                self.res_evse_sales[year] = vehicles.sales[year]
            else:
                self.res_evses[year] = vehicles.population[year]
                self.res_evse_sales[year] = 0

        # Get new sales and replacements

        for year in range(start_year, end_year + 1):

            if year == start_year:
                new_sales = self.res_evses[year]
            else:
                new_sales = self.res_evses[year] - self.res_evses[year - 1]

            try:
                replacements = self.res_evse_sales[year - vehicles.vehicle_lifetime]
            except KeyError:
                replacements = 0.0
            self.res_evse_new_sales[year] = new_sales
            self.res_evse_replacements[year] = replacements


    def get_public(self, start_year, end_year, vehicle_lifetime, publicl2_portsperEVSE):

        for year in range(start_year, end_year+1):
            if year == start_year:
                self.dcfc_evses[year] = self.port_population[year] * self.public_dcfc_proportion
                dcfc_new_sales = self.dcfc_evses[year]
                dcfc_replacements = 0.

                self.l2_evses[year] = old_div(self.port_population[year] \
                                      * (1.0 - self.public_dcfc_proportion), publicl2_portsperEVSE)
                l2_new_sales = self.l2_evses[year]
                l2_replacements = 0.

            elif year <= max(self.port_population.keys()):
                self.dcfc_evses[year] = self.port_population[year] * self.public_dcfc_proportion
                dcfc_new_sales = self.dcfc_evses[year] - self.dcfc_evses[year-1]
                try:
                    dcfc_replacements = self.dcfc_sales[year - vehicle_lifetime]
                except KeyError:
                    dcfc_replacements = 0.0

                self.l2_evses[year] = old_div(self.port_population[year] \
                                      * (1.0 - self.public_dcfc_proportion), publicl2_portsperEVSE)

                l2_new_sales = self.l2_evses[year] - self.l2_evses[year - 1]
                try:
                    l2_replacements = self.l2_sales[year - vehicle_lifetime]
                except KeyError:
                    l2_replacements = 0.0

            else:
                dcfc_new_sales = 0.
                dcfc_replacements = 0.
                try:
                    self.dcfc_evses[year] = self.dcfc_evses[year-1] \
                                            - self.dcfc_sales[year - vehicle_lifetime]
                except KeyError:
                    self.dcfc_evses[year] = self.dcfc_evses[year-1]

                l2_new_sales = 0.
                l2_replacements = 0.
                try:
                    self.l2_evses[year] = self.l2_evses[year-1] \
                                                 - self.l2_sales[year - vehicle_lifetime]
                except KeyError:
                    self.l2_evses[year] = self.l2_evses[year-1]

            self.dcfc_sales[year] = dcfc_new_sales + dcfc_replacements
            self.l2_sales[year] = l2_new_sales + l2_replacements


    def get_workplace(self, workplace_loadprofile, start_year,adoption_final_year, end_year, include_static,
                      cap_per_plug, workl2_portsperEVSE ):
        """
        Calculates workplace_evse_sales for adoption years.
        """

        for year in range(start_year, end_year+1):
            try:
                max_kw = max(workplace_loadprofile.peak_shape[year].values())*1000
                chargers_needed = old_div(max_kw,(cap_per_plug * workl2_portsperEVSE))
                # Make sure that workplace evses can't go down compared to previous year
                if year > adoption_final_year:
                    self.workplace_evses[year] = self.workplace_evses[adoption_final_year]
                else:
                    self.workplace_evses[year] = chargers_needed

                if include_static:

                    self.workplace_evses[year] += self.static_workplace_chargers[year]

            except KeyError:
                self.workplace_evses[year] = 0

    def get_public_l2(self, start_year, end_year, include_static):
        for year in range(start_year, end_year+1):
            if include_static:
                try:
                    self.static_workplace_proportion[year] = old_div(self.static_workplace_chargers[year], self.l2_evses[year])
                    self.public_l2_evses[year] = self.l2_evses[year] * (1 - self.static_workplace_proportion[year])
                except:
                    self.public_l2_evses[year] = 0.0  # TODO: static workplace should extend over all model years
            else:
                self.public_l2_evses[year] = self.l2_evses[year] - self.workplace_evses[year]

    def get_public_l2_sales(self, start_year, end_year, vehicle_lifetime):

        for year in range(start_year, end_year+1):

            if year == start_year:
                new_sales = self.public_l2_evses[year]
            else:
                new_sales = self.public_l2_evses[year] - self.public_l2_evses[year-1]

            try:
                replacements = self.public_l2_sales[year - vehicle_lifetime]
            except KeyError:
                replacements = 0.0

            self.public_l2_sales[year] = new_sales + replacements
            self.public_l2_new_sales[year] = new_sales
            self.public_l2_replacements[year] = replacements

    def get_dcfc_sales(self, start_year, end_year, vehicle_lifetime):

        for year in range(start_year, end_year+1):

            if year == start_year:
                new_sales = self.dcfc_evses[year]
            else:
                new_sales = self.dcfc_evses[year] - self.dcfc_evses[year-1]

            try:
                replacements = self.dcfc_sales[year - vehicle_lifetime]
            except KeyError:
                replacements = 0.0

            self.dcfc_sales[year] = new_sales + replacements
            self.dcfc_new_sales[year] = new_sales
            self.dcfc_replacements[year] = replacements

    def get_pro_lite_public_l2_sales(self, start_year, end_year, vehicle_lifetime, vehicle_sales, public_EVSE_ratio):

        for year in range(start_year, end_year+1):

            if year == start_year:
                try:
                    new_sales = vehicle_sales[year] / public_EVSE_ratio
                except ZeroDivisionError:
                    new_sales = 0

            else:
                new_sales = self.public_l2_evses[year] - self.public_l2_evses[year-1]

            try:
                replacements = self.public_l2_sales[year - vehicle_lifetime]
            except KeyError:
                replacements = 0.0

            self.public_l2_sales[year] = new_sales + replacements
            self.public_l2_new_sales[year] = new_sales
            self.public_l2_replacements[year] = replacements

    def get_pro_lite_dcfc_sales(self, start_year, end_year, vehicle_lifetime, vehicle_sales, DCFC_EVSE_ratio):

        for year in range(start_year, end_year+1):

            if year == start_year:
                try:
                    new_sales = vehicle_sales[year] / DCFC_EVSE_ratio
                except ZeroDivisionError:
                    new_sales = 0
            else:
                new_sales = self.dcfc_evses[year] - self.dcfc_evses[year-1]

            try:
                replacements = self.dcfc_sales[year - vehicle_lifetime]
            except KeyError:
                replacements = 0.0

            self.dcfc_sales[year] = new_sales + replacements
            self.dcfc_new_sales[year] = new_sales
            self.dcfc_replacements[year] = replacements


    def print_populations(self, years):

        for year in years:
            print(year, \
                self.res_evses[year] if year in list(self.res_evses.keys()) else '-', \
                self.public_l2_evses[year] if year in list(self.public_l2_evses.keys()) else '-', \
                self.workplace_evses[year] if year in list(self.workplace_evses.keys()) else '-', \
                self.dcfc_evses[year] if year in list(self.dcfc_evses.keys()) else '-')

    def get_populations_from_pro_lite(self, work_ratio, public_ratio, dcfc_ratio,
                                      model_years, vehicles):

        for year in model_years:
            if year in vehicles.adoption_years:
                self.res_evses[year] = vehicles.population[year]
                self.res_evse_sales[year] = vehicles.sales[year]
            else:
                self.res_evses[year] = vehicles.population[year]
                self.res_evse_sales[year] = 0

        for year in model_years:
            try:
                self.public_l2_evses[year] = old_div(vehicles.population[year], public_ratio)
            except ZeroDivisionError:
                self.public_l2_evses[year] = 0
            try:
                self.workplace_evses[year] = old_div(vehicles.population[year], work_ratio)
            except ZeroDivisionError:
                self.workplace_evses[year] = 0
            try:
                self.dcfc_evses[year] = old_div(vehicles.population[year], dcfc_ratio)
            except ZeroDivisionError:
                self.dcfc_evses[year] = 0

        # Get new sales and replacements

        for year in model_years:

            if year == min(model_years):
                new_sales = self.res_evses[year]
            else:
                new_sales = self.res_evses[year] - self.res_evses[year - 1]

            try:
                replacements = self.res_evse_sales[year - vehicles.vehicle_lifetime]
            except KeyError:
                replacements = 0.0
            self.res_evse_new_sales[year] = new_sales
            self.res_evse_replacements[year] = replacements

    def get_workplace_l2_sales(self, start_year, end_year, vehicle_lifetime):

        for year in range(start_year, end_year+1):

            if year == start_year:
                new_sales = self.workplace_evses[year]
            else:
                new_sales = self.workplace_evses[year] - self.workplace_evses[year-1]

            try:
                replacements = self.workplace_evse_sales[year - vehicle_lifetime]
            except KeyError:
                replacements = 0.0

            self.workplace_evse_sales[year] = new_sales + replacements
            self.workplace_evse_new_sales[year] = new_sales
            self.workplace_evse_replacements[year] = replacements

    def get_pro_lite_workplace_l2_sales(self, start_year, end_year, vehicle_lifetime, vehicle_sales, work_EVSE_ratio):

        for year in range(start_year, end_year+1):

            if year == start_year:
                try:
                    new_sales = vehicle_sales[year] / work_EVSE_ratio
                except ZeroDivisionError:
                    new_sales = 0
            else:
                new_sales = self.workplace_evses[year] - self.workplace_evses[year-1]

            try:
                replacements = self.workplace_evse_sales[year - vehicle_lifetime]
            except KeyError:
                replacements = 0.0

            self.workplace_evse_sales[year] = new_sales + replacements
            self.workplace_evse_new_sales[year] = new_sales
            self.workplace_evse_replacements[year] = replacements

    def get_base_cost(self,
                        model_years,
                        homel2_startprice,
                        homel2_reduction,
                        workl2_startprice,
                        workl2_reduction,
                        publicl2_startprice,
                        publicl2_reduction,
                        dcfc_startprice,
                        dcfc_reduction):

        start_year = min(model_years)

        for year in model_years:

            try:
                homel2_sales = self.res_evse_sales[year]

                homel2_price = homel2_startprice * (1-homel2_reduction) ** (year - start_year)
                homel2_cost = homel2_sales * homel2_price
                self.res_cost[year] = homel2_cost

                workl2_sales = self.workplace_evse_sales[year]
                workl2_price = workl2_startprice * (1-workl2_reduction) ** (year - start_year)
                workl2_cost = workl2_sales * workl2_price
                self.workplace_l2_cost[year] = workl2_cost

                publicl2_sales = self.public_l2_sales[year]
                publicl2_price = publicl2_startprice * (1-publicl2_reduction) ** (year - start_year)
                publicl2_cost = publicl2_sales * publicl2_price
                self.public_l2_cost[year] = publicl2_cost

                dcfc_sales = self.dcfc_sales[year]
                dcfc_price = dcfc_startprice * (1-dcfc_reduction) ** (year - start_year)
                dcfc_cost = dcfc_sales * dcfc_price
                self.dcfc_cost[year] = dcfc_cost

            except KeyError:
                self.res_cost[year] = 0.
                self.workplace_l2_cost[year] = 0.
                self.public_l2_cost[year] = 0.
                self.dcfc_cost[year] = 0

    def get_base_cost_with_replacement(self, model_years, homel2_makeready, homel2_evse_cost,
                                       homel2_reduction, workl2_makeready, workl2_evse_cost,
                                       workl2_reduction, publicl2_makeready, publicl2_evse_cost,
                                       publicl2_reduction, dcfc_makeready, dcfc_evse_cost, dcfc_cluster_size,
                                       dcfc_reduction, inflation_rate):

        start_year = min(model_years)
        for year in model_years:

            try:

                homel2_evse_price = homel2_evse_cost * (1-homel2_reduction + inflation_rate) ** (year - start_year)
                homel2_cost = self.res_evse_new_sales[year] * (homel2_makeready + homel2_evse_price) + \
                              self.res_evse_replacements[year] * homel2_evse_price

                self.res_cost[year] = homel2_cost

                workl2_evse_price = workl2_evse_cost * (1-workl2_reduction + inflation_rate) ** (year - start_year)
                workl2_cost = self.workplace_evse_new_sales[year] * (workl2_makeready + workl2_evse_price) + \
                              self.workplace_evse_replacements[year] * workl2_evse_price

                self.workplace_l2_cost[year] = workl2_cost

                publicl2_evse_price = publicl2_evse_cost * (1-publicl2_reduction + inflation_rate) ** (year - start_year)
                publicl2_cost = self.public_l2_new_sales[year] * (publicl2_makeready + publicl2_evse_price) + \
                              self.public_l2_replacements[year] * publicl2_evse_price

                self.public_l2_cost[year] = publicl2_cost

                dcfc_evse_price = dcfc_evse_cost * (1 - dcfc_reduction + inflation_rate) ** (year - start_year)
                dcfc_cost = self.dcfc_new_sales[year] * (old_div(dcfc_makeready,dcfc_cluster_size)+ dcfc_evse_price) + \
                                self.dcfc_replacements[year] * dcfc_evse_price
                self.dcfc_cost[year] = dcfc_cost

            except KeyError:
                self.res_cost[year] = 0.
                self.workplace_l2_cost[year] = 0.
                self.public_l2_cost[year] = 0.
                self.dcfc_cost[year] = 0

    def print_sales(self, year_range):

        for year in year_range:
            print(year, \
                self.dcfc_sales[year] if year in list(self.dcfc_sales.keys()) else '-')


    def print_base_cost(self, year_range):

        for year in year_range:
            print(year, \
                helpers.format_as_dollars(self.dcfc_cost[year]) if year in list(self.dcfc_cost.keys()) else '-', \
                helpers.format_as_dollars(self.public_l2_cost[year]) if year in list(self.public_l2_cost.keys()) else '-', \
                helpers.format_as_dollars(self.workplace_l2_cost[year]) if year in list(self.workplace_l2_cost.keys()) \
                    else '-', \
                helpers.format_as_dollars(self.res_cost[year]) if year in list(self.res_cost.keys()) else '-')


    def print_charger_data(self, year_range, charger_string):

        string_to_attr = {
            'res': ['res_evses', 'res_evse_sales', 'res_cost'],
            'workplace': ['workplace_evses', 'workplace_evse_sales', 'workplace_l2_cost'],
            'dcfc': ['dcfc_evses', 'dcfc_sales', 'dcfc_cost'],
            'publicl2': ['public_l2_evses', 'public_l2_sales', 'public_l2_cost'],
            'l2': ['l2_evses', 'l2_sales', 'l2_cost']
        }

        attrs = string_to_attr[charger_string]
        tabular_data = []

        for year in year_range:
            tabular_data.append([year,
                                 helpers.comma_format(getattr(self,attrs[0])[year]),
                                 helpers.comma_format(getattr(self, attrs[1])[year]) if year in list(getattr(self, attrs[1]).keys()) else '-',
                                 helpers.format_as_dollars(getattr(self, attrs[2])[year]) if year in list(getattr(self, attrs[2]).keys()) else '-'])

        import tabulate
        print(charger_string)
        print(tabulate.tabulate(tabular_data, headers=['year', 'pop', 'sales', 'cost']))
