import json
import csv
import psycopg2
from django.conf import settings


class UploadToPostgres():
    def __init__(
        self,
        load_profile,
        county
    ):

        with open(settings.BASE_DIR + '/postgres_info.json') as json_file:
            postgres_info = json.load(json_file)

        self.db_host = postgres_info['DB_HOST']
        self.postgres_db = postgres_info['POSTGRES_DB']
        self.postgres_user = postgres_info['POSTGRES_USER']
        self.postgres_password = postgres_info['POSTGRES_PASSWORD']

        self.conn = psycopg2.connect(
            host=self.db_host,
            dbname=self.postgres_db,
            user=self.postgres_user,
            password=self.postgres_password,
            port='5432'
        )

        self.load_profile = load_profile
        self.county = county

        ################################################
        ### Uncontrolled Gas Consumption CSV Results ###
        ################################################

        # Store EV Share to save in uncontrolled cost benefit results
        self.uncontrolled_ev_share_results = []

        with open(settings.BASE_DIR[:-3] + 'script/CostBenefitAnalysis/cases/BaseCase_{0}_uncontrolled_load/results/annual_gas_consumption.csv'.format(county)) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if row[0] == 'EV Share (%)':
                    for item in row:
                        self.uncontrolled_ev_share_results.append(item)

        ##############################################
        ### Controlled Gas Consumption CSV Results ###
        ##############################################

        # Store EV Share to save in controlled cost benefit results
        self.controlled_ev_share_results = []

        with open(settings.BASE_DIR[:-3] + 'script/CostBenefitAnalysis/cases/BaseCase_{0}_e19controlled_load/results/annual_gas_consumption.csv'.format(county)) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if row[0] == 'EV Share (%)':
                    for item in row:
                        self.controlled_ev_share_results.append(item)

        ##########################################
        ### Uncontrolled Emissions CSV Results ###
        ##########################################

        # Store unconctrolled CO2 emissions to calculate Net Carbon Emission Savings in uncontrolled cost benefit
        self.uncontrolled_co2_emissions = []

        with open(settings.BASE_DIR[:-3] + 'script/CostBenefitAnalysis/cases/BaseCase_{0}_uncontrolled_load/results/Emissions.csv'.format(county)) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if row[0] == 'CO2 emissions from EVs (metric tons)':
                    for item in row[1:]:
                        self.uncontrolled_co2_emissions.append(item)

        ########################################
        ### Controlled Emissions CSV Results ###
        ########################################

        # Store controlled CO2 emissions to calculate Net Carbon Emission Savings in controlled cost benefit
        self.controlled_co2_emissions = []

        with open(settings.BASE_DIR[:-3] + 'script/CostBenefitAnalysis/cases/BaseCase_{0}_e19controlled_load/results/Emissions.csv'.format(county)) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if row[0] == 'CO2 emissions from EVs (metric tons)':
                    for item in row[1:]:
                        self.controlled_co2_emissions.append(item)

        #############################################
        ### Uncontrolled Cost Benefit CSV Results ###
        #############################################

        self.uncontrolled_cost_benefit_result_dict = {}
        self.uncontrolled_electricity_supply_cost_list = []
        self.uncontrolled_avoided_gasoline_gallons = []

        with open(settings.BASE_DIR[:-3] + 'script/CostBenefitAnalysis/cases/BaseCase_{0}_uncontrolled_load/results/annual_results.csv'.format(county)) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:

                # Calculate uncontrolled Electricity Supply Cost and store to uncontrolled cost benefit results
                # Electricity Supply Cost (per year) = Energy Supply Cost (per year) + Capacity Cost (per year) + Distribution Cost (per year) + Transmission Costs (per year) + GHG Cost (per year)
                if row[0] == 'Energy Supply Cost' or row[0] == 'Capacity Cost' or row[0] == 'Distribution Cost' or row[0] == 'Transmission Cost' or row[0] == 'GHG Cost':
                    for idx, item in enumerate(row[1:]):
                        if len(self.uncontrolled_electricity_supply_cost_list) > idx:
                            self.uncontrolled_electricity_supply_cost_list[idx] = self.uncontrolled_electricity_supply_cost_list[idx] + float(item)
                        else:
                            self.uncontrolled_electricity_supply_cost_list.append(float(item))
                    self.uncontrolled_cost_benefit_result_dict['Electricity Supply Cost ($)'] = [str(item) for item in self.uncontrolled_electricity_supply_cost_list]

                if row[0] == 'Utility Bills':
                    self.uncontrolled_cost_benefit_result_dict['Utility Bills ($)'] = []
                    for item in row[1:]:
                        self.uncontrolled_cost_benefit_result_dict['Utility Bills ($)'].append(item)

                if row[0] == 'Year' or row[0] == 'Cumulative personal light-duty EV population':
                    self.uncontrolled_cost_benefit_result_dict[row[0]] = []
                    for item in row[1:]:
                        self.uncontrolled_cost_benefit_result_dict[row[0]].append(item)

                if row[0] == 'Avoided vehicle gasoline (gallons)':
                    self.uncontrolled_cost_benefit_result_dict[row[0]] = []
                    for item in row[1:]:
                        self.uncontrolled_cost_benefit_result_dict[row[0]].append(item)
                        # Store uncontrolled avoided vehicle gasoline to calculate uncontrolled Net Carbon Emission Savings
                        self.uncontrolled_avoided_gasoline_gallons.append(item)

            self.uncontrolled_cost_benefit_result_dict[self.uncontrolled_ev_share_results[0]] = []
            for item in self.uncontrolled_ev_share_results[1:]:
                self.uncontrolled_cost_benefit_result_dict[self.uncontrolled_ev_share_results[0]].append(item)

            # Calculate uncontrolled Net Carbon Emission Savings
            # Net Carbon Emission Savings (per year) = Avoided Gasoline (gallons) (per year) * 0.008887 (metric tons CO2 / gallon) – CO2 Emissions (metric tons) (per year)
            self.uncontrolled_cost_benefit_result_dict['Net Carbon Emission Savings (metric tons CO2)'] = []
            for idx, item in enumerate(self.uncontrolled_avoided_gasoline_gallons):
                co2_savings = float(item) * 0.008887 - float(self.uncontrolled_co2_emissions[idx])
                self.uncontrolled_cost_benefit_result_dict['Net Carbon Emission Savings (metric tons CO2)'].append(str(co2_savings))

        ###########################################
        ### Controlled Cost Benefit CSV Results ###
        ###########################################

        self.controlled_cost_benefit_result_dict = {}
        self.controlled_electricity_supply_cost_list = []
        self.controlled_avoided_gasoline_gallons = []

        with open(settings.BASE_DIR[:-3] + 'script/CostBenefitAnalysis/cases/BaseCase_{0}_e19controlled_load/results/annual_results.csv'.format(county)) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:

                # Calculate controlled Electricity Supply Cost and store to controlled cost benefit results
                # Electricity Supply Cost (per year) = Energy Supply Cost (per year) + Capacity Cost (per year) + Distribution Cost (per year) + Transmission Costs (per year ) + GHG Cost (per year)
                if row[0] == 'Energy Supply Cost' or row[0] == 'Capacity Cost' or row[0] == 'Distribution Cost' or row[0] == 'Transmission Cost' or row[0] == 'GHG Cost':
                    for idx, item in enumerate(row[1:]):
                        if len(self.controlled_electricity_supply_cost_list) > idx:
                            self.controlled_electricity_supply_cost_list[idx] = self.controlled_electricity_supply_cost_list[idx] + float(item)
                        else:
                            self.controlled_electricity_supply_cost_list.append(float(item))
                    self.controlled_cost_benefit_result_dict['Electricity Supply Cost ($)'] = [str(item) for item in self.controlled_electricity_supply_cost_list]

                if row[0] == 'Utility Bills':
                    self.controlled_cost_benefit_result_dict['Utility Bills ($)'] = []
                    for item in row[1:]:
                        self.controlled_cost_benefit_result_dict['Utility Bills ($)'].append(item)

                if row[0] == 'Year' or row[0] == 'Cumulative personal light-duty EV population':
                    self.controlled_cost_benefit_result_dict[row[0]] = []
                    for item in row[1:]:
                        self.controlled_cost_benefit_result_dict[row[0]].append(item)

                if row[0] == 'Avoided vehicle gasoline (gallons)':
                    self.controlled_cost_benefit_result_dict[row[0]] = []
                    for item in row[1:]:
                        self.controlled_cost_benefit_result_dict[row[0]].append(item)
                        # Store controlled avoided vehicle gasoline to calculate controlled Net Carbon Emission Savings
                        self.controlled_avoided_gasoline_gallons.append(item)

            self.controlled_cost_benefit_result_dict[self.controlled_ev_share_results[0]] = []
            for item in self.controlled_ev_share_results[1:]:
                self.controlled_cost_benefit_result_dict[self.controlled_ev_share_results[0]].append(item)

            # Calculate controlled Net Carbon Emission Savings
            # Net Carbon Emission Savings (per year) = Avoided Gasoline (gallons) (per year) * 0.008887 (metric tons CO2 / gallon) – CO2 Emissions (metric tons) (per year)
            self.controlled_cost_benefit_result_dict['Net Carbon Emission Savings (metric tons CO2)'] = []
            for idx, item in enumerate(self.controlled_avoided_gasoline_gallons):
                co2_savings = float(item) * 0.008887 - float(self.controlled_co2_emissions[idx])
                self.controlled_cost_benefit_result_dict['Net Carbon Emission Savings (metric tons CO2)'].append(str(co2_savings))

        self.cba_cost_benefit_table_name = "script_algorithm_cba_cost_benefit"
        self.config_cba_cost_benefit_table_name = "script_config_cba_cost_benefit"

        self.run_cost_benefit()

        print("Cost Benefit Analysis Runner completed successfully.")

    def run_cost_benefit(self):

        self.cur = self.conn.cursor()

        # Loop through each year (11: ends at year 2030)
        for i in range(11):
            uncontrolled_tmp_res = {}
            controlled_tmp_res = {}

            for key in self.uncontrolled_cost_benefit_result_dict.keys():
                if key != 'Year':
                    uncontrolled_tmp_res[key] = self.uncontrolled_cost_benefit_result_dict[key][i]

            for key in self.controlled_cost_benefit_result_dict.keys():
                if key != 'Year':
                    controlled_tmp_res[key] = self.controlled_cost_benefit_result_dict[key][i]

            self.cur.execute("INSERT INTO " + self.config_cba_cost_benefit_table_name + " (lf_config, year) VALUES (%s, %s)",
                             (
                                 self.load_profile, str(
                                     self.uncontrolled_cost_benefit_result_dict['Year'][i])
                             )
                             )
            self.conn.commit()

            self.cur.execute(
                "SELECT id FROM " + self.config_cba_cost_benefit_table_name + " ORDER BY id DESC LIMIT 1")
            config_cost_benefit_id = self.cur.fetchone()[0]

            self.cur.execute("INSERT INTO " + self.cba_cost_benefit_table_name + " (config, uncontrolled_values, controlled_values) VALUES (%s, %s, %s)",
                             (
                                 str(config_cost_benefit_id), json.dumps(
                                     uncontrolled_tmp_res), json.dumps(controlled_tmp_res)
                             )
                             )

        # Make the changes to the database persistent
        self.conn.commit()

        # Close communication with the database
        self.cur.close()
        self.conn.close()
