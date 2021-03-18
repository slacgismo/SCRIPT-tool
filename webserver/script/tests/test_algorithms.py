from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from script.models.enums import DayType, POI, AggregationLevel
from script.models.data import County
from script.models.config import LoadControllerConfig, LoadForecastConfig, LoadProfileConfig, GasConsumptionConfig, NetPresentValueConfig, CostBenefitConfig, EmissionConfig
from script.models.algorithms import LoadController, LoadForecast, LoadProfile, GasConsumption, CostBenefit, NetPresentValue, Emission, LoadForecastConfig
from script.tests.utils import create_load_controller_config, create_load_forecast_config, create_load_profile_config, create_cost_benefit_config, create_emission_config, create_gas_consumption_config, create_net_present_value_config
from script.tests.utils import create_county, create_load_controller, create_load_forecast, create_load_profile, create_gas_consumption, create_cost_benefit, create_net_present_value, create_emission

from script.tests.test_data import CountyTests
from script.tests.test_config import LoadControllerConfigTests, LoadForecastConfigTests, LoadProfileConfigTests, GasConsumptionConfigTests, NetPresentValueConfigTests, CostBenefitConfigTests, EmissionConfigTests

import json
import copy

class LoadControllerTests(APITestCase):

    uncontrolled_load = [
        {
            'time': '05:30',
            'load': '134'
        },
        {
            'time': '05:45',
            'load': '323'
        },
        {
            'time': '06:00',
            'load': '413'
        }
    ]
    controlled_load = [
        {
            'time': '05:30',
            'load': '130'
        },
        {
            'time': '05:45',
            'load': '320'
        },
        {
            'time': '06:00',
            'load': '410'
        }
    ]

    def test_create_load_controller(self):
        """Ensure we can create a new load controller object."""
        _ = create_county(CountyTests.county_name,
                            CountyTests.total_session,
                            CountyTests.total_energy,
                            CountyTests.peak_energy)
        _ = create_load_controller_config(CountyTests.county_name,
                                            LoadControllerConfigTests.rate_energy_peak,
                                            LoadControllerConfigTests.rate_energy_partpeak,
                                            LoadControllerConfigTests.rate_energy_offpeak,
                                            LoadControllerConfigTests.rate_demand_peak,
                                            LoadControllerConfigTests.rate_demand_partpeak,
                                            LoadControllerConfigTests.rate_demand_overall)
        config = LoadControllerConfig.objects.get()
        response = create_load_controller(config,
                                            json.dumps(self.uncontrolled_load),
                                            json.dumps(self.controlled_load))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LoadController.objects.count(), 1)
        obj = LoadController.objects.get()
        self.assertEqual(obj.config.county.name, CountyTests.county_name)
        self.assertEqual(json.loads(obj.uncontrolled_load), self.uncontrolled_load)
        self.assertEqual(json.loads(obj.controlled_load), self.controlled_load)

    def test_create_conflict(self):
        """Ensure we cannot create two load controllers with the same config."""
        _ = create_county(CountyTests.county_name,
                            CountyTests.total_session,
                            CountyTests.total_energy,
                            CountyTests.peak_energy)
        _ = create_load_controller_config(CountyTests.county_name,
                                            LoadControllerConfigTests.rate_energy_peak,
                                            LoadControllerConfigTests.rate_energy_partpeak,
                                            LoadControllerConfigTests.rate_energy_offpeak,
                                            LoadControllerConfigTests.rate_demand_peak,
                                            LoadControllerConfigTests.rate_demand_partpeak,
                                            LoadControllerConfigTests.rate_demand_overall)
        config = LoadControllerConfig.objects.get()
        response = create_load_controller(config,
                                            json.dumps(self.uncontrolled_load),
                                            json.dumps(self.controlled_load))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = create_load_controller(config,
                                            json.dumps(self.uncontrolled_load),
                                            json.dumps(self.controlled_load))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_config(self):
        """Ensure we can filter load controllers by fields: config."""
        _ = create_county(CountyTests.county_name,
                            CountyTests.total_session,
                            CountyTests.total_energy,
                            CountyTests.peak_energy)
        _ = create_county('Palo Alto',
                            CountyTests.total_session,
                            CountyTests.total_energy,
                            CountyTests.peak_energy)
        _ = create_load_controller_config(CountyTests.county_name,
                                            LoadControllerConfigTests.rate_energy_peak,
                                            LoadControllerConfigTests.rate_energy_partpeak,
                                            LoadControllerConfigTests.rate_energy_offpeak,
                                            LoadControllerConfigTests.rate_demand_peak,
                                            LoadControllerConfigTests.rate_demand_partpeak,
                                            LoadControllerConfigTests.rate_demand_overall)
        _ = create_load_controller_config('Palo Alto',
                                            LoadControllerConfigTests.rate_energy_peak,
                                            LoadControllerConfigTests.rate_energy_partpeak,
                                            LoadControllerConfigTests.rate_energy_offpeak,
                                            LoadControllerConfigTests.rate_demand_peak,
                                            LoadControllerConfigTests.rate_demand_partpeak,
                                            LoadControllerConfigTests.rate_demand_overall)
        county1 = County.objects.get(pk=CountyTests.county_name)
        config1 = LoadControllerConfig.objects.filter(county=county1)[0]
        response = create_load_controller(config1,
                                            json.dumps(self.uncontrolled_load),
                                            json.dumps(self.controlled_load))
        county2 = County.objects.get(pk='Palo Alto')
        config2 = LoadControllerConfig.objects.filter(county=county2)[0]
        new_controlled_load = copy.deepcopy(self.controlled_load)
        new_controlled_load[0]['load'] = '110'
        response = create_load_controller(config2,
                                            json.dumps(self.uncontrolled_load),
                                            json.dumps(new_controlled_load))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        url = reverse('algorithm/load_controller-list')
        data = {
            'config': config1.id
        }
        response = self.client.get(url, data)
        obj = json.loads(response.content)[0]
        config = LoadControllerConfig.objects.get(id=obj['config'])
        self.assertEqual(config.county.name, CountyTests.county_name)
        self.assertEqual(json.loads(obj['controlled_load']), self.controlled_load)


class LoadForecastTests(APITestCase):

    residential_l1_load = [
        {
            'time': '05:30',
            'load': '130'
        },
        {
            'time': '05:45',
            'load': '320'
        },
        {
            'time': '06:00',
            'load': '410'
        }
    ]
    residential_l2_load = [
        {
            'time': '05:30',
            'load': '130'
        },
        {
            'time': '05:45',
            'load': '3230'
        },
        {
            'time': '06:00',
            'load': '410'
        }
    ]
    residential_mud_load = [
        {
            'time': '05:30',
            'load': '1303'
        },
        {
            'time': '05:45',
            'load': '320'
        },
        {
            'time': '06:00',
            'load': '410'
        }
    ]
    work_load = [
        {
            'time': '05:30',
            'load': '130'
        },
        {
            'time': '05:45',
            'load': '3220'
        },
        {
            'time': '06:00',
            'load': '410'
        }
    ]
    fast_load = [
        {
            'time': '05:30',
            'load': '130'
        },
        {
            'time': '05:45',
            'load': '3120'
        },
        {
            'time': '06:00',
            'load': '410'
        }
    ]
    public_l2_load = [
        {
            'time': '05:30',
            'load': '1330'
        },
        {
            'time': '05:45',
            'load': '3210'
        },
        {
            'time': '06:00',
            'load': '4110'
        }
    ]
    total_load = [
        {
            'time': '05:30',
            'load': '1130'
        },
        {
            'time': '05:45',
            'load': '320'
        },
        {
            'time': '06:00',
            'load': '4120'
        }
    ]

    def test_create_load_forecast(self):
        """Ensure we can create a new EV load forecast object."""
        _ = create_county(CountyTests.county_name,
                            CountyTests.total_session,
                            CountyTests.total_energy,
                            CountyTests.peak_energy)
        _ = create_load_forecast_config(LoadForecastConfigTests.config_name,
                                        LoadForecastConfigTests.aggregation_level,
                                        LoadForecastConfigTests.num_evs,
                                        LoadForecastConfigTests.choice,
                                        LoadForecastConfigTests.fast_percent,
                                        LoadForecastConfigTests.work_percent,
                                        LoadForecastConfigTests.res_percent,
                                        LoadForecastConfigTests.l1_percent,
                                        LoadForecastConfigTests.public_l2_percent)
        config = LoadForecastConfig.objects.get()
        response = create_load_forecast(config,
                                        json.dumps(self.residential_l1_load),
                                        json.dumps(self.residential_l2_load),
                                        json.dumps(self.residential_mud_load),
                                        json.dumps(self.work_load),
                                        json.dumps(self.fast_load),
                                        json.dumps(self.public_l2_load),
                                        json.dumps(self.total_load))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LoadForecast.objects.count(), 1)
        obj = LoadForecast.objects.get()
        self.assertEqual(obj.config.config_name, LoadForecastConfigTests.config_name)
        self.assertEqual(obj.config.aggregation_level, LoadForecastConfigTests.aggregation_level.name)
        self.assertEqual(json.loads(obj.residential_l1_load), self.residential_l1_load)
        self.assertEqual(json.loads(obj.total_load), self.total_load)


class LoadProfileTests(APITestCase):
    loads = [i * 2 % 24 + 1 for i in range(24)]

    def test_create_load_profile(self):
        """Ensure we can create a new load profile object."""
        _ = create_county(CountyTests.county_name,
                            CountyTests.total_session,
                            CountyTests.total_energy,
                            CountyTests.peak_energy)
        _ = create_load_forecast_config(LoadForecastConfigTests.config_name,
                                        LoadForecastConfigTests.aggregation_level,
                                        LoadForecastConfigTests.num_evs,
                                        LoadForecastConfigTests.choice,
                                        LoadForecastConfigTests.fast_percent,
                                        LoadForecastConfigTests.work_percent,
                                        LoadForecastConfigTests.res_percent,
                                        LoadForecastConfigTests.l1_percent,
                                        LoadForecastConfigTests.public_l2_percent)
        lf_config = LoadForecastConfig.objects.get()
        _ = create_load_profile_config(lf_config,
                                        LoadProfileConfigTests.poi,
                                        LoadProfileConfigTests.year,
                                        LoadProfileConfigTests.day_type)
        config = LoadProfileConfig.objects.get()
        response = create_load_profile(config, json.dumps(self.loads))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LoadProfile.objects.count(), 1)
        obj = LoadProfile.objects.get()
        self.assertEqual(obj.config.lf_config.config_name, LoadForecastConfigTests.config_name)
        self.assertEqual(obj.config.poi, LoadProfileConfigTests.poi.name)
        self.assertEqual(json.loads(obj.loads), self.loads)


class GasConsumptionTests(APITestCase):

    consumption = {
        'Gasoline_Consumption_gallons': 545619941.6,
        'Gasoline_Consumption_MMBTU': 65734108089476.5,
        'Gasoline_Emissions_CO2': 4637769.504,
        'PHEV_10_Gasoline_Consumption_gallons': 24929.58517,
        'PHEV_10_Gasoline_Consumption_MMBTU': 3003416703,
        'PHEV_10_Gasoline_Emissions_CO2': 211.9014739,
        'PHEV_20_Gasoline_Consumption_gallons': 69108.54055,
        'PHEV_20_Gasoline_Consumption_MMBTU': 8325920531,
        'PHEV_20_Gasoline_Emissions_CO2': 587.4225947,
        'PHEV_40_Gasoline_Consumption_gallons': 95172.95918,
        'PHEV_40_Gasoline_Consumption_MMBTU': 11466057430,
        'PHEV_40_Gasoline_Emissions_CO2': 808.970153,
        'BEV_100_Gasoline_Consumption_gallons': 67142.92642,
        'BEV_100_Gasoline_Consumption_MMBTU': 8089111204,
        'BEV_100_Gasoline_Emissions_CO2': 570.7148746,
        'EV_Share': 0.001533283
    }

    def test_create_gas_consumption(self):
        """Ensure we can create a new gas consumption object."""
        _ = create_county(CountyTests.county_name,
                            CountyTests.total_session,
                            CountyTests.total_energy,
                            CountyTests.peak_energy)
        _ = create_load_forecast_config(LoadForecastConfigTests.config_name,
                                        LoadForecastConfigTests.aggregation_level,
                                        LoadForecastConfigTests.num_evs,
                                        LoadForecastConfigTests.choice,
                                        LoadForecastConfigTests.fast_percent,
                                        LoadForecastConfigTests.work_percent,
                                        LoadForecastConfigTests.res_percent,
                                        LoadForecastConfigTests.l1_percent,
                                        LoadForecastConfigTests.public_l2_percent)
        lf_config = LoadForecastConfig.objects.get()
        _ = create_gas_consumption_config(lf_config, GasConsumptionConfigTests.year)
        config = GasConsumptionConfig.objects.get()
        response = create_gas_consumption(config, json.dumps(self.consumption))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GasConsumption.objects.count(), 1)
        obj = GasConsumption.objects.get()
        self.assertEqual(obj.config.year, GasConsumptionConfigTests.year)
        self.assertEqual(json.loads(obj.consumption), self.consumption)


class CostBenefitTests(APITestCase):

    cost_benefit = {
        'Utility_Bills': 1643285.189,
        'Utility_Bills_res': 1574878.503,
        'Utility_Bills_work': 27523.12322,
        'Utility_Bills_pub_L2': 40883.56269,
        'Utility_Bills_DCFC': 0,
        'Incremental_upfront_vehicle_cost': 15713196.73,
        'Charging_infrastructure_cost':	4573543.239,
        'Charging_infrastructure_cost_res':	2920300,
        'Charging_infrastructure_cost_work_L2':	632882.3529,
        'Charging_infrastructure_cost_public_L2': 430360,
        'Charging_infrastructure_cost_DCFC': 590000.8865,
        'Avoided_vehicle_gasoline ($)':	4604521.161,
        'Avoided_vehicle_gasoline (gallons)': 2029634.905,
        'Vehicle_O&M_Savings': 307236,
        'Federal_EV_Tax_Credit': 10166700,
        'Vehicle_sales': 1537,
        'Transmission_and_Distribution_Cost': 127854.8147,
        'Distribution_Cost': 87146.31329,
        'Transmission_Cost': 40708.50144,
        'Cumulative_personal_light-duty_EV_population':	6878,
        'Cumulative_personal_light-duty_LDV_population': 1293819,
        'EV_sales_as_percentage_of_total_personal_light-duty_vehicles':	0.001187956,
        'Peak_Demand_5-9_PM': 6.913490911,
        'Energy_Supply_Cost': 687051.7026,
        'Energy_Cost': 531222.3664,
        'Capacity_Cost': 155829.3361
    }

    def test_create_cost_benefit(self):
        """Ensure we can create a new cost benefit object."""
        _ = create_county(CountyTests.county_name,
                            CountyTests.total_session,
                            CountyTests.total_energy,
                            CountyTests.peak_energy)
        _ = create_load_forecast_config(LoadForecastConfigTests.config_name,
                                        LoadForecastConfigTests.aggregation_level,
                                        LoadForecastConfigTests.num_evs,
                                        LoadForecastConfigTests.choice,
                                        LoadForecastConfigTests.fast_percent,
                                        LoadForecastConfigTests.work_percent,
                                        LoadForecastConfigTests.res_percent,
                                        LoadForecastConfigTests.l1_percent,
                                        LoadForecastConfigTests.public_l2_percent)
        lf_config = LoadForecastConfig.objects.get()
        _ = create_cost_benefit_config(lf_config, CostBenefitConfigTests.year)
        config = CostBenefitConfig.objects.get()
        response = create_cost_benefit(config, json.dumps(self.cost_benefit))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CostBenefit.objects.count(), 1)
        obj = CostBenefit.objects.get()
        self.assertEqual(obj.config.year, CostBenefitConfigTests.year)
        self.assertEqual(json.loads(obj.cost_benefit), self.cost_benefit)


class NetPresentValueTests(APITestCase):

    net_present_value = {
        'Utility_Bills': 250514400.4,
        'Utility_Bills_volumetric':	250059210.3,
        'Utility_Bills_demand':	455190.0426,
        'Utility_Bills_res': 240325818.2,
        'Utility_Bills_work': 4088140.725,
        'Utility_Bills_pub_L2':	6100441.406,
        'Utility_Bills_DCFC': 0,
        'Incremental_upfront_vehicle_cost':	91394525.43,
        'Charging_infrastructure_cost': 324375153.1,
        'Charging_infrastructure_cost_res':	207241475.2,
        'Charging_infrastructure_cost_work_L2':	44902567.99,
        'Charging_infrastructure_cost_public_L2': 30533746.23,
        'Charging_infrastructure_cost_DCFC': 41697363.66,
        'Avoided_vehicle_gasoline':	802838445.2,
        'Vehicle_O&M_Savings': 207528684.2,
        'Federal_EV_Tax_Credit': 121338516.8,
        'Energy_Supply_Cost': 80844635.85,
        'Energy_Cost': 80844635.85,
        'Generation_Capacity_Cost':	23490407.75,
        'Vehicle_Sales': 132772.6619,
        'Transmission_and_Distribution_Cost': 15056754.47,
        'Distribution_Cost': 8905317.194,
        'Transmission_Cost': 6151437.278
    }

    def test_create_net_present_value(self):
        """Ensure we can create a new net present value object."""
        _ = create_county(CountyTests.county_name,
                            CountyTests.total_session,
                            CountyTests.total_energy,
                            CountyTests.peak_energy)
        _ = create_load_forecast_config(LoadForecastConfigTests.config_name,
                                        LoadForecastConfigTests.aggregation_level,
                                        LoadForecastConfigTests.num_evs,
                                        LoadForecastConfigTests.choice,
                                        LoadForecastConfigTests.fast_percent,
                                        LoadForecastConfigTests.work_percent,
                                        LoadForecastConfigTests.res_percent,
                                        LoadForecastConfigTests.l1_percent,
                                        LoadForecastConfigTests.public_l2_percent)
        lf_config = LoadForecastConfig.objects.get()
        _ = create_net_present_value_config(lf_config, NetPresentValueConfigTests.year)
        config = NetPresentValueConfig.objects.get()
        response = create_net_present_value(config, json.dumps(self.net_present_value))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(NetPresentValue.objects.count(), 1)
        obj = NetPresentValue.objects.get()
        self.assertEqual(obj.config.year, NetPresentValueConfigTests.year)
        self.assertEqual(json.loads(obj.npv), self.net_present_value)


class EmissionTests(APITestCase):

    emissions = {
        'CO2_emissions': 11809.74895,
        'NOX_emissions': 8.537033476,
        'PM_10_emissions': 0.41418928,
        'SO2_emissions': 2.786595841,
        'VOC_emissions': 0.13171142
    }

    def test_create_emission(self):
        """Ensure we can create a new emission object."""
        _ = create_county(CountyTests.county_name,
                            CountyTests.total_session,
                            CountyTests.total_energy,
                            CountyTests.peak_energy)
        _ = create_load_forecast_config(LoadForecastConfigTests.config_name,
                                        LoadForecastConfigTests.aggregation_level,
                                        LoadForecastConfigTests.num_evs,
                                        LoadForecastConfigTests.choice,
                                        LoadForecastConfigTests.fast_percent,
                                        LoadForecastConfigTests.work_percent,
                                        LoadForecastConfigTests.res_percent,
                                        LoadForecastConfigTests.l1_percent,
                                        LoadForecastConfigTests.public_l2_percent)
        lf_config = LoadForecastConfig.objects.get()
        _ = create_emission_config(lf_config, EmissionConfigTests.year)
        config = EmissionConfig.objects.get()
        response = create_emission(config, json.dumps(self.emissions))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Emission.objects.count(), 1)
        obj = Emission.objects.get()
        self.assertEqual(obj.config.year, EmissionConfigTests.year)
        self.assertEqual(json.loads(obj.emissions), self.emissions)
