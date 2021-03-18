from __future__ import division
from __future__ import unicode_literals

from past.utils import old_div
from builtins import range
import csv
import helpers

def export_results(model_instance):

    # Utility Revenue
    annual_bills = [model_instance.total_revenue[year] for year in model_instance.model_years]
    annual_energy_bills = [model_instance.volumetric_revenue[year] for year in model_instance.model_years]
    annual_demand_bills = [model_instance.demand_revenue[year] for year in model_instance.model_years]

    npv_bills = helpers.npv(annual_bills, model_instance.inputs.discount_rate)[0]
    npv_volumetric = helpers.npv(annual_energy_bills, model_instance.inputs.discount_rate)[0]
    npv_demand = helpers.npv(annual_demand_bills, model_instance.inputs.discount_rate)[0]

    annual_resbills = [model_instance.res_revenue[year] for year in model_instance.model_years]
    npv_resbills = helpers.npv(annual_resbills, model_instance.inputs.discount_rate)[0]

    annual_workbills = [model_instance.work_revenue[year] for year in model_instance.model_years]
    npv_workbills = helpers.npv(annual_workbills, model_instance.inputs.discount_rate)[0]

    annual_publicl2bills = [model_instance.publicl2_revenue[year] for year in model_instance.model_years]
    npv_publicl2bills = helpers.npv(annual_publicl2bills, model_instance.inputs.discount_rate)[0]

    annual_dcfcbills = [model_instance.dcfc_revenue[year] for year in model_instance.model_years]
    npv_dcfcbills = helpers.npv(annual_dcfcbills, model_instance.inputs.discount_rate)[0]


    # Vehicle costs
    annual_vehcosts = [model_instance.vehicles.capital_cost[year] for year in model_instance.model_years]
    npv_vehcosts = helpers.npv(annual_vehcosts, model_instance.inputs.discount_rate)[0]


    # Charger costs
    annual_chgcosts = [model_instance.chargers.res_cost[year]
                           + model_instance.chargers.workplace_l2_cost[year]
                           + model_instance.chargers.public_l2_cost[year]
                           + model_instance.chargers.dcfc_cost[year] for year in model_instance.model_years]
    npv_chgcosts = helpers.npv(annual_chgcosts, model_instance.inputs.discount_rate)[0]

    annual_reschgcosts = [model_instance.chargers.res_cost[year] for year in model_instance.model_years]
    npv_reschgcosts = helpers.npv(annual_reschgcosts, model_instance.inputs.discount_rate)[0]

    annual_workl2chgcosts = [model_instance.chargers.workplace_l2_cost[year] for year in model_instance.model_years]
    npv_workl2chgcosts = helpers.npv(annual_workl2chgcosts, model_instance.inputs.discount_rate)[0]

    annual_publicl2chgcosts = [model_instance.chargers.public_l2_cost[year] for year in model_instance.model_years]
    npv_publicl2chgcosts = helpers.npv(annual_publicl2chgcosts, model_instance.inputs.discount_rate)[0]

    annual_dcfcchgcosts = [model_instance.chargers.dcfc_cost[year] for year in model_instance.model_years]
    npv_dcfcchgcosts = helpers.npv(annual_dcfcchgcosts, model_instance.inputs.discount_rate)[0]


    # Gasoline savings
    annual_gassavings = [model_instance.vehicles.gasoline_savings[year] for year in model_instance.model_years]
    annual_gallons_avoided = [model_instance.vehicles.gallons_avoided[year] for year in model_instance.model_years]
    npv_gassavings = helpers.npv(annual_gassavings, model_instance.inputs.discount_rate)[0]

    # Gasoline consumption
    annual_gas_consumption = [model_instance.vehicles.gasoline_consumption[year] for year in
                              model_instance.vehicles.gas_consumption_range]

    annual_gas_consumption_mmbtu = [model_instance.vehicles.gasoline_consumption_mmbtu[year] for year in
                                    model_instance.vehicles.gas_consumption_range]

    annual_gas_consumption_co2 = [model_instance.vehicles.gasoline_consumption_co2[year] for year in
                                    model_instance.vehicles.gas_consumption_range]

    phev_annual_gas_consumption = [model_instance.vehicles.phev_gasoline_consumption[year] for year in
                              model_instance.vehicles.gas_consumption_range]

    phev_annual_gas_consumption_mmbtu = [model_instance.vehicles.phev_gasoline_consumption_mmbtu[year] for year in
                                    model_instance.vehicles.gas_consumption_range]

    phev_annual_gas_consumption_co2 = [model_instance.vehicles.phev_gasoline_consumption_co2[year] for year in
                                    model_instance.vehicles.gas_consumption_range]

    bev_annual_gas_consumption = [model_instance.vehicles.bev_gasoline_consumption[year] for year in
                              model_instance.vehicles.gas_consumption_range]

    bev_annual_gas_consumption_mmbtu = [model_instance.vehicles.bev_gasoline_consumption_mmbtu[year] for year in
                                    model_instance.vehicles.gas_consumption_range]

    bev_annual_gas_consumption_co2 = [model_instance.vehicles.bev_gasoline_consumption_co2[year] for year in
                                    model_instance.vehicles.gas_consumption_range]

    ev_share = [model_instance.vehicles.ev_share[year] for year in
                                    model_instance.vehicles.gas_consumption_range]

    npv_gas_consumption = helpers.npv(annual_gas_consumption, model_instance.inputs.discount_rate)[0]

    # Avoided O&M
    annual_oandm = [model_instance.vehicles.oandm_savings[year] for year in model_instance.model_years]
    npv_oandm = helpers.npv(annual_oandm, model_instance.inputs.discount_rate)[0]


    # Tax credt
    annual_taxcredit = [model_instance.vehicles.tax_credit[year] for year in model_instance.model_years]
    npv_taxcredit = helpers.npv(annual_taxcredit, model_instance.inputs.discount_rate)[0]

    # Vehicle sales
    annual_sales = [model_instance.vehicles.sales[year] for year in model_instance.model_years]
    npv_sales = helpers.npv(annual_sales, model_instance.inputs.discount_rate)[0]

    # Cumulative vehicle population
    cumulative_ev_population = [model_instance.vehicles.population[year] for year in model_instance.model_years]
    cumulative_ldv_population = [model_instance.vehicles.total_population[year] for year in model_instance.model_years]
    ev_sales_proportion = [old_div(model_instance.vehicles.sales[year],model_instance.vehicles.total_population[year])
                           for year in range(model_instance.inputs.start_year, model_instance.inputs.end_year)]
    # Peak Demand 5 - 9 PM

    peak_demand_5to9_pm = [model_instance.peak_demand_5to9_pm[year] for year in model_instance.model_years]

    annual_tandd = []
    for year in model_instance.model_years:
        try:
            annual_tandd.append(model_instance.t_and_d_dict[year])
        except KeyError:
            annual_tandd.append(0)
    npv_tandd = helpers.npv(annual_tandd, model_instance.inputs.discount_rate)[0]

    annual_distribution = []
    for year in model_instance.model_years:
        try:
            annual_distribution.append(model_instance.distribution_dict[year])
        except KeyError:
            annual_tandd.append(0)
    npv_distribution = helpers.npv(annual_distribution, model_instance.inputs.discount_rate)[0]

    annual_transmission = []
    for year in model_instance.model_years:
        try:
            annual_transmission.append(model_instance.transmission_dict[year])
        except KeyError:
            annual_transmission.append(0)
    npv_transmission = helpers.npv(annual_transmission, model_instance.inputs.discount_rate)[0]

    # Energy Supply cost
    annual_energy_supply_cost = []
    for year in model_instance.model_years:
        try:
            annual_energy_supply_cost.append(model_instance.annual_energy_supply_cost_dict[year])
        except KeyError:
            annual_energy_supply_cost.append(0)

    npv_energy_supply_cost = helpers.npv(annual_energy_supply_cost, model_instance.inputs.discount_rate)[0]

    annual_energy = []
    for year in model_instance.model_years:
        try:
            annual_energy.append(model_instance.energy_dict[year])
        except KeyError:
            annual_energy.append(0)
    npv_energy = helpers.npv(annual_energy, model_instance.inputs.discount_rate)[0]

    annual_ghg_cost = []
    for year in model_instance.model_years:
        try:
            annual_ghg_cost.append(model_instance.ghg_dict[year])
        except KeyError:
            annual_ghg_cost.append(0)
    npv_ghg_cost = helpers.npv(annual_ghg_cost, model_instance.inputs.discount_rate)[0]

    annual_capacity = []
    for year in model_instance.model_years:
        try:
            annual_capacity.append(model_instance.capacity_dict[year])
        except KeyError:
            annual_capacity.append(0)
    npv_capacity = helpers.npv(annual_capacity, model_instance.inputs.discount_rate)[0]

    # Emissions from EV
    CO2_emissions = []
    NOX_emissions = []
    PM10_emissions = []
    SO2_emissions = []
    VOC_emissions = []
    
    # Emissions Savings
    
    CO2_emissions_savings = []
    annual_carbon_emissions_savings_from_avoided_gasoline = []
    annual_carbon_emissions_from_ev = []

    for year in model_instance.model_years:
        try:
            CO2_emissions.append(model_instance.CO2_emissions_dict[year])
        except KeyError:
            CO2_emissions.append(0)
        try:
            NOX_emissions.append(model_instance.NOX_emissions_dict[year])
        except KeyError:
            NOX_emissions.append(0)
        try:
            PM10_emissions.append(model_instance.PM10_emissions_dict[year])
        except KeyError:
            PM10_emissions.append(0)
        try:
            SO2_emissions.append(model_instance.SO2_emissions_dict[year])
        except KeyError:
            SO2_emissions.append(0)
        try:
            VOC_emissions.append(model_instance.VOC_emissions_dict[year])
        except KeyError:
            VOC_emissions.append(0)
        try:
            CO2_emissions_savings.append(model_instance.vehicles.co2_savings[year])
        except:
            CO2_emissions_savings.append(0)

        try:
            annual_carbon_emissions_from_ev.append(model_instance.CO2_emissions_dict[year] *
                                                                  model_instance.inputs.carbon_cost)
        except:
            annual_carbon_emissions_from_ev.append(0)

        try:
            annual_carbon_emissions_savings_from_avoided_gasoline.append(model_instance.vehicles.co2_savings[year] *
                                                                  model_instance.inputs.carbon_cost)
        except:
            annual_carbon_emissions_savings_from_avoided_gasoline.append(0)

    annual_net_carbon_emissions_savings = [a - b for a, b in zip(
        annual_carbon_emissions_savings_from_avoided_gasoline, annual_carbon_emissions_from_ev)]

    npv_emissions_av_gasoline = helpers.npv(
        annual_carbon_emissions_savings_from_avoided_gasoline, model_instance.inputs.discount_rate)[0]

    npv_emissions_from_ev = helpers.npv(annual_carbon_emissions_from_ev, model_instance.inputs.discount_rate)[0]

    npv_net_emissions_savings = helpers.npv(annual_net_carbon_emissions_savings,
                                            model_instance.inputs.discount_rate)[0]

    npv_results_dir = model_instance.inputs.RESULTS_DIR + r'/npv_results.csv'
    with open(npv_results_dir, 'w', newline ='') as csvfile:
        writer = csv.writer(csvfile)

        # Header
        writer.writerow(['Year', 'NPV'])

        # Bill revenue
        writer.writerow(['Utility Bills', npv_bills])
        writer.writerow(['Utility Bills (volumetric)', npv_volumetric])
        writer.writerow(['Utility Bills (demand)', npv_demand])
        writer.writerow(['Utility Bills (res)', npv_resbills])
        writer.writerow(['Utility Bills (work)', npv_workbills])
        writer.writerow(['Utility Bills (pub L2)', npv_publicl2bills])
        writer.writerow(['Utility Bills (DCFC)', npv_dcfcbills])

        # Incremental capital cost
        writer.writerow(['Incremental upfront vehicle cost', npv_vehcosts])

        # Charger cost
        writer.writerow(['Charging infrastructure cost', npv_chgcosts])
        writer.writerow(['Charging infrastructure cost (res)', npv_reschgcosts])
        writer.writerow(['Charging infrastructure cost (work L2)', npv_workl2chgcosts])
        writer.writerow(['Charging infrastructure cost (public L2)', npv_publicl2chgcosts])
        writer.writerow(['Charging infrastructure cost (DCFC)', npv_dcfcchgcosts])

        # Avoided gasoline cost
        writer.writerow(['Avoided vehicle gasoline', npv_gassavings])

        # Avoided O&M cost
        writer.writerow(['Vehicle O&M Savings', npv_oandm])

        # Tax credit
        writer.writerow(['Federal EV Tax Credit', npv_taxcredit])

        # Energy Supply Cost

        writer.writerow(['Total Energy Supply Cost', npv_energy_supply_cost])
        writer.writerow(['Energy Cost', npv_energy])
        writer.writerow(['Generation Capacity Cost', npv_capacity])

        # GHG Costs
        # writer.writerow(['GHG Costs', npv_ghg_cost])

        # Vehicle Sales
        writer.writerow(['Vehicle Sales (NPV)', npv_sales])

        # Distribution cost
        writer.writerow(['Transmission and Distribution Cost', npv_tandd])
        writer.writerow(['Distribution Cost', npv_distribution])
        writer.writerow(['Transmission Cost', npv_transmission])

        # Emissions Savings
        writer.writerow(['Emissions Savings from Avoided Gasoline ($)', npv_emissions_av_gasoline])

        writer.writerow(['Emissions associated with EV adoption ($)', npv_emissions_from_ev])

        writer.writerow(['Net emissions savings ($)', npv_net_emissions_savings])

    annual_results_dir = model_instance.inputs.RESULTS_DIR + r'/annual_results.csv'
    with open(annual_results_dir, 'w', newline ='') as csvfile:
        writer = csv.writer(csvfile)

        # Header
        writer.writerow(['Year']
                        + model_instance.model_years)

        # Bill revenue
        writer.writerow(['Utility Bills']
                        + annual_bills)
        writer.writerow(['Utility Bills (res)']
                        + annual_resbills)
        writer.writerow(['Utility Bills (work)']
                        + annual_workbills)
        writer.writerow(['Utility Bills (pub L2)']
                            + annual_publicl2bills)
        writer.writerow(['Utility Bills (DCFC)']
                        + annual_dcfcbills)

        # Incremental capital cost
        writer.writerow(['Incremental upfront vehicle cost']
                        + annual_vehcosts)

        # Charger cost
        writer.writerow(['Charging infrastructure cost']
                        + annual_chgcosts)
        writer.writerow(['Charging infrastructure cost (res)']
                        + annual_reschgcosts)
        writer.writerow(['Charging infrastructure cost (work L2)']
                        + annual_workl2chgcosts)
        writer.writerow(['Charging infrastructure cost (public L2)']
                        + annual_publicl2chgcosts)
        writer.writerow(['Charging infrastructure cost (DCFC)']
                        + annual_dcfcchgcosts)

        # Avoided gasoline cost
        writer.writerow(['Avoided vehicle gasoline ($)']
                        + annual_gassavings)

        writer.writerow(['Avoided vehicle gasoline (gallons)']
                        + annual_gallons_avoided)

        writer.writerow(['Carbon Emissions Savings From Avoided Gasoline ($)'] +
                        annual_carbon_emissions_savings_from_avoided_gasoline)

        writer.writerow(['Carbon Emission Costs Associated with EV Adoption ($)'] + annual_carbon_emissions_from_ev)

        writer.writerow(['Net Carbon Emission Savings Associated with EV Adoption ($)']
                        + annual_net_carbon_emissions_savings)

        # Avoided O&M cost
        writer.writerow(['Vehicle O&M Savings']
                        + annual_oandm)

        # Tax credit
        writer.writerow(['Federal EV Tax Credit']
                        + annual_taxcredit)

        # Vehicle sales
        writer.writerow(['Vehicle sales']
                        + annual_sales)

        # Distribution cost
        writer.writerow(['Transmission and Distribution Cost']
                        + annual_tandd)
        writer.writerow(['Distribution Cost']
                        + annual_distribution)
        writer.writerow(['Transmission Cost']
                        + annual_transmission)

        # Populations

        writer.writerow(['Cumulative personal light-duty EV population'] + cumulative_ev_population)
        writer.writerow(['Cumulative personal light-duty LDV population'] + cumulative_ldv_population)
        writer.writerow(['EV sales as % of total personal light-duty vehicles'] + ev_sales_proportion)

        # Annual results
        writer.writerow(['Peak Demand 5-9 PM'] + peak_demand_5to9_pm)

        # Energy supply cost
        writer.writerow(['Energy Supply Cost'] + annual_energy_supply_cost)
        writer.writerow(['Energy Cost']
                        + annual_energy)
        writer.writerow(['GHG Cost']
                        + annual_ghg_cost)
        writer.writerow(['Capacity Cost']
                        + annual_capacity)

    annual_gas_dir = model_instance.inputs.RESULTS_DIR + r'/Emissions.csv'
    with open(annual_gas_dir, 'w', newline ='') as csvfile:
        writer = csv.writer(csvfile)

        # Header
        writer.writerow(['Year']
                        +  model_instance.model_years)

        # Emissions from EVs
        writer.writerow(['CO2 emissions from EVs (metric tons)']
                        + CO2_emissions)
        writer.writerow(['NOX emissions from EVs (metric tons)']
                        + NOX_emissions)

        writer.writerow(['PM 10 emissions from EVs (metric tons)']
                        + PM10_emissions)

        writer.writerow(['SO2 emissions from EVs (metric tons)']
                        + SO2_emissions)

        writer.writerow(['VOC emissions from EVs (metric tons)']
                        + VOC_emissions)


    annual_gas_dir = model_instance.inputs.RESULTS_DIR + r'/annual_gas_consumption.csv'
    with open(annual_gas_dir, 'w', newline ='') as csvfile:
        writer = csv.writer(csvfile)

        # Header
        writer.writerow(['Year']
                        + model_instance.vehicles.gas_consumption_range)

        # Gasoline Consumption
        writer.writerow(['Gasoline Consumption (gallons)']
                        + annual_gas_consumption)
        writer.writerow(['Gasoline Consumption (MMBTU)']
                        + annual_gas_consumption_mmbtu)

        writer.writerow(['Gasoline Emissions (metric tons CO2)']
                        + annual_gas_consumption_co2)

        writer.writerow(['PHEV Gasoline Consumption (gallons)']
                        + phev_annual_gas_consumption)
        writer.writerow(['PHEV Gasoline Consumption (MMBTU)']
                        + phev_annual_gas_consumption_mmbtu)

        writer.writerow(['PHEV Gasoline Emissions (metric tons CO2)']
                        + phev_annual_gas_consumption_co2)

        writer.writerow(['BEV Gasoline Consumption (gallons)']
                        + bev_annual_gas_consumption)
        writer.writerow(['BEV Gasoline Consumption (MMBTU)']
                        + bev_annual_gas_consumption_mmbtu)

        writer.writerow(['BEV Gasoline Emissions (metric tons CO2)']
                        + bev_annual_gas_consumption_co2)

        writer.writerow(['EV Share (%)'] + ev_share)

def export_loadprofiles(model_instance, data, name):
    loadprofile_dir = model_instance.inputs.RESULTS_DIR + r'/{0}_loadprofile.csv'.format(name)

    with open(loadprofile_dir, 'w', newline ='') as csvfile:
        writer = csv.writer(csvfile)

        for row in data:
            writer.writerow(row)
