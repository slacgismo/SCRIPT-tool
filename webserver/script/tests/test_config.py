from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from script.models.enums import DayType, POI, AggregationLevel
from script.models.data import County
from script.models.config import LoadControllerConfig, LoadForecastConfig, LoadProfileConfig, GasConsumptionConfig, CostBenefitConfig, NetPresentValueConfig, EmissionConfig
from script.tests.utils import create_county, create_load_controller_config, create_load_forecast_config, create_load_profile_config, create_gas_consumption_config, create_cost_benefit_config, create_net_present_value_config, create_emission_config

from script.tests.test_data import CountyTests


class LoadControllerConfigTests(APITestCase):

    rate_energy_peak = 0.16997
    rate_energy_partpeak = 0.12236
    rate_energy_offpeak = 0.09082
    rate_demand_peak = 21.23
    rate_demand_partpeak = 5.85
    rate_demand_overall = 19.10

    def test_create_load_controller_config(self):
        """Ensure we can create a new config of load controller object."""
        _ = create_county(CountyTests.county_name,
                            CountyTests.total_session,
                            CountyTests.total_energy,
                            CountyTests.peak_energy)
        response = create_load_controller_config(CountyTests.county_name,
                                            self.rate_energy_peak,
                                            self.rate_energy_partpeak,
                                            self.rate_energy_offpeak,
                                            self.rate_demand_peak,
                                            self.rate_demand_partpeak,
                                            self.rate_demand_overall)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LoadControllerConfig.objects.count(), 1)
        obj = LoadControllerConfig.objects.get()
        self.assertEqual(obj.county.name, CountyTests.county_name)
        self.assertEqual(obj.rate_demand_partpeak, self.rate_demand_partpeak)


class LoadForecastConfigTests(APITestCase):

    config_name = 'lf-config-test'
    aggregation_level = AggregationLevel.COUNTY
    num_evs = 1000000
    choice = 'Santa Clara'
    fast_percent = 0.1
    work_percent = 0.2
    res_percent = 0.7
    l1_percent = 0.5
    public_l2_percent = 0.0

    def test_create_load_forecast_config(self):
        """Ensure we can create a new config of load forecast object."""
        _ = create_county(CountyTests.county_name,
                            CountyTests.total_session,
                            CountyTests.total_energy,
                            CountyTests.peak_energy)
        response = create_load_forecast_config(self.config_name,
                                                self.aggregation_level,
                                                self.num_evs,
                                                self.choice,
                                                self.fast_percent,
                                                self.work_percent,
                                                self.res_percent,
                                                self.l1_percent,
                                                self.public_l2_percent)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LoadForecastConfig.objects.count(), 1)
        obj = LoadForecastConfig.objects.get()
        self.assertEqual(obj.aggregation_level, self.aggregation_level.name)
        self.assertEqual(obj.choice, self.choice)
        self.assertEqual(obj.fast_percent, self.fast_percent)


class LoadProfileConfigTests(APITestCase):

    poi = POI.WORKPLACE
    year = 2020
    day_type = DayType.WEEKEND

    def test_create_load_profile_config(self):
        """Ensure we can create a new config of load profile object."""
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
        response = create_load_profile_config(LoadForecastConfigTests.config_name,
                                            self.poi,
                                            self.year,
                                            self.day_type)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LoadProfileConfig.objects.count(), 1)
        obj = LoadProfileConfig.objects.get()
        self.assertEqual(obj.lf_config.config_name, LoadForecastConfigTests.config_name)
        self.assertEqual(obj.poi, self.poi.name)


class GasConsumptionConfigTests(APITestCase):

    year = 2021

    def test_create_gas_consumption_config(self):
        """Ensure we can create a new config of gas consumption object."""
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
        response = create_gas_consumption_config(LoadForecastConfigTests.config_name, self.year)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GasConsumptionConfig.objects.count(), 1)
        obj = GasConsumptionConfig.objects.get()
        self.assertEqual(obj.lf_config.config_name, LoadForecastConfigTests.config_name)
        self.assertEqual(obj.year, self.year)


class CostBenefitConfigTests(APITestCase):

    year = 2022

    def test_create_cost_benefit_config(self):
        """Ensure we can create a new config of cost benefit object."""
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
        response = create_cost_benefit_config(LoadForecastConfigTests.config_name, self.year)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CostBenefitConfig.objects.count(), 1)
        obj = CostBenefitConfig.objects.get()
        self.assertEqual(obj.lf_config.config_name, LoadForecastConfigTests.config_name)
        self.assertEqual(obj.year, self.year)


class CostBenefitConfigTests(APITestCase):

    year = 2023

    def test_create_cost_benefit_config(self):
        """Ensure we can create a new config of cost benefit object."""
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
        response = create_cost_benefit_config(LoadForecastConfigTests.config_name, self.year)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CostBenefitConfig.objects.count(), 1)
        obj = CostBenefitConfig.objects.get()
        self.assertEqual(obj.lf_config.config_name, LoadForecastConfigTests.config_name)
        self.assertEqual(obj.year, self.year)


class NetPresentValueConfigTests(APITestCase):

    year = 2024

    def test_create_net_present_value_config(self):
        """Ensure we can create a new config of net present value object."""
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
        response = create_net_present_value_config(LoadForecastConfigTests.config_name, self.year)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(NetPresentValueConfig.objects.count(), 1)
        obj = NetPresentValueConfig.objects.get()
        self.assertEqual(obj.lf_config.config_name, LoadForecastConfigTests.config_name)
        self.assertEqual(obj.year, self.year)


class EmissionConfigTests(APITestCase):

    year = 2025

    def test_create_emission_config(self):
        """Ensure we can create a new config of emission object."""
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
        response = create_emission_config(LoadForecastConfigTests.config_name, self.year)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(EmissionConfig.objects.count(), 1)
        obj = EmissionConfig.objects.get()
        self.assertEqual(obj.lf_config.config_name, LoadForecastConfigTests.config_name)
        self.assertEqual(obj.year, self.year)
