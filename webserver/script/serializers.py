import datetime
from rest_framework import serializers
from script.models.data import County, ZipCode
from script.models.statistics import Energy
from script.models.config import LoadControllerConfig, LoadForecastConfig, CostBenefitConfig
from script.models.algorithms import LoadController, LoadForecast, CostBenefit


class CountySerializer(serializers.ModelSerializer):
    class Meta:
        model = County
        fields = '__all__'


class ZipCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZipCode
        fields = '__all__'

class EnergySerializer(serializers.ModelSerializer):
    class Meta:
        model = Energy
        fields = '__all__'


class LoadControllerConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoadControllerConfig
        fields = '__all__'


class LoadForecastConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoadForecastConfig
        fields = '__all__'


class CostBenefitConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostBenefitConfig
        fields = '__all__'


class LoadControllerSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoadController
        fields = '__all__'


class LoadForecastSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoadForecast
        fields = '__all__'


class CostBenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostBenefit
        fields = '__all__'
        depth = 1
