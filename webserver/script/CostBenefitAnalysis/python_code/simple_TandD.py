from __future__ import unicode_literals

from builtins import range
from builtins import object
import helpers

class SimpleTandD(object):

    def __init__(self, tandd_years, cost_per_incremental_kw, load_profiles_by_rate_and_charger):

        self.cumulative_peak_shape = {year: {i: 0.0 for i in range(24)} for year in tandd_years}

        for year in tandd_years:
            for loadprofile in list(load_profiles_by_rate_and_charger.values()):
                for hour in range(24):
                    peakday_mw = loadprofile.peak_shape[year][hour]
                    peakday_kw = peakday_mw * 1000.0
                    self.cumulative_peak_shape[year][hour] += peakday_kw

        self.cumulative_peak = {year: max(self.cumulative_peak_shape[year].values()) for year in tandd_years}

        self.incremental_peak = {year: 0. for year in tandd_years}
        for year in tandd_years:
            if year == min(tandd_years):
                self.incremental_peak[year] = self.cumulative_peak[year]
            else:
                self.incremental_peak[year] = max(self.cumulative_peak[year] - self.cumulative_peak[year-1], 0)

        self.incremental_cost = {year: self.incremental_peak[year] * cost_per_incremental_kw for year in tandd_years}
