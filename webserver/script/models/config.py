from django.db import models
from script.models.data import County
from script.models.enums import DayType, POI, AggregationLevel
from script.validators import validate_positive, validate_year

# Create your models of config of algorithm results here.

class LoadControllerConfig(models.Model):
    """Algorithm: Load Controller inputs:
        (1) county
        (2) rate_energy_peak
        (3) rate_energy_partpeak
        (4) rate_energy_offpeak
        (5) rate_demand_peak
        (6) rate_demand_partpeak
        (7) rate_demand_overall
    """

    county = models.ForeignKey(County, on_delete=models.CASCADE, db_column="county")
    rate_energy_peak = models.FloatField(validators=[validate_positive])
    rate_energy_partpeak = models.FloatField(validators=[validate_positive])
    rate_energy_offpeak = models.FloatField(validators=[validate_positive])
    rate_demand_peak = models.FloatField(validators=[validate_positive])
    rate_demand_partpeak = models.FloatField(validators=[validate_positive])
    rate_demand_overall = models.FloatField(validators=[validate_positive])

    class Meta:
        db_table = 'script_config_load_controller'
        unique_together = (('county',
                            'rate_energy_peak',
                            'rate_energy_partpeak',
                            'rate_energy_offpeak',
                            'rate_demand_peak',
                            'rate_demand_partpeak',
                            'rate_demand_overall'),)


class LoadForecastConfig(models.Model):
    """Algorithm: EV Load Forecast inputs:
        (0) config_name
        (1) aggregation_level
        (2) num_evs
        (3) choice, which should base on which kind of aggregation level selected
        (4) fast_percent
        (5) work_percent
        (6) res_percent
        (7) l1_percent
        (8) public_l2_percent
    """

    config_name = models.CharField(max_length=100, blank=False, primary_key=True)
    aggregation_level = models.CharField(max_length=10, choices=AggregationLevel.choices(), default=AggregationLevel.COUNTY)
    num_evs = models.IntegerField(validators=[validate_positive])
    # TODO: how validate choice and aggregation together at model level rather than serializer level?
    choice = models.CharField(max_length=30)
    fast_percent = models.FloatField()
    work_percent = models.FloatField()
    res_percent = models.FloatField()
    l1_percent = models.FloatField()
    public_l2_percent = models.FloatField()
    res_daily_use = models.FloatField()
    work_daily_use = models.FloatField()
    fast_daily_use = models.FloatField()
    rent_percent = models.FloatField()
    res_l2_smooth = models.CharField(max_length=30)
    week_day = models.CharField(max_length=30)
    publicl2_daily_use = models.FloatField()
    mixed_batteries = models.CharField(max_length=50)
    timer_control = models.CharField(max_length=30)
    work_control = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'script_config_ev_load_forecast'


class CostBenefitConfig(models.Model):
    """Algorithm: Cost Benefit inputs:
        (1) lf_config of LoadForecastConfig
        (2) year
    """

    lf_config = models.ForeignKey(LoadForecastConfig, on_delete=models.CASCADE, db_column="lf_config")
    year = models.IntegerField()

    class Meta:
        db_table = 'script_config_cba_cost_benefit'
        unique_together = (('lf_config',
                            'year'),)
