from enum import Enum

class EnumWithChoices(Enum):
    @classmethod
    def choices(cls):
        return tuple((i.name, i.value) for i in cls)


class AggregationLevel(EnumWithChoices):
    """Aggregation level"""
    STATE = 'state'
    COUNTY = 'county'
    ZIP = 'zip'


class POI(EnumWithChoices):
    """Place of interest"""
    ALL = 'All'
    WORKPLACE = 'Workplace'
    DCFC = 'DC Fast Charger'
    RESIDENTIAL = 'Residential'
    PUBLIC_L2 = 'Public L2'
    UNKNOWN = 'Unknown'
    # [TODO] add more POIs


class POISub(EnumWithChoices):
    """Place of interest sub-category"""
    HT = 'High-Tech'
    UNKNOWN = 'Unknown'
    # [TODO] add more POI sub-categories


class ChargingConnector(EnumWithChoices):
    """Charging connector type"""
    CHADEMO = 'CHAdeMO'
    COMBO = 'Combo'
    J1772 = 'J1772'
    UNKNOWN = 'Unknown'
    # [TODO] add more connector types


class VehicleMake(EnumWithChoices):
    """Vehicle make"""
    NISSAN = 'Nissan'
    CHEVROLET = 'Chevrolet'
    AUDI = 'Audi'
    BMW = 'BMW'
    HONDA = 'Honda'
    UNKNOWN = 'Unknown'
    # [TODO] add more vehicle makes


class EVType(EnumWithChoices):
    """EV type"""
    PLUGIN = 'PLUGIN'
    HYBRID = 'HYBRID'
    UNKNOWN = 'UNKNOWN'
    # [TODO] add more EV types


class DayType(EnumWithChoices):
    """Day type"""
    WEEKDAY = 'weekday'
    WEEKEND = 'weekend'
    PEAK = 'peak'
