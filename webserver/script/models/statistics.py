from django.db import models
from script.models.data import County
from script.validators import validate_month, validate_year

class Energy(models.Model):
    """Energy consumed by county and year-month"""
    county = models.ForeignKey(County, on_delete=models.CASCADE, db_column="county")
    year = models.IntegerField(validators=[validate_year])
    month = models.IntegerField(validators=[validate_month])
    energy = models.FloatField()

    class Meta:
        db_table = 'script_energy'
        unique_together = (('county', 'year', 'month'),)    

# [TODO] add more statistics
