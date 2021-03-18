from django.core.exceptions import ValidationError

import datetime

# Validators

def validate_year(year):
    if year < 2000 or year > datetime.datetime.now().year:
        raise ValidationError("Year must be 2000~now.")


def validate_month(month):
    if month < 1 or month > 12:
        raise ValidationError("Month must be 1~12.")


def validate_positive(value):
    if value < 0:
        raise ValidationError("Value must be a positive.")


def validate_zipcode(zipcode):
    if len(zipcode) != 5 or not zipcode.isdigit():
        raise ValidationError("Incorrect zip code.")
