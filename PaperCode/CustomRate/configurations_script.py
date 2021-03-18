import numpy as np
import pickle
import pandas as pd
import boto3


class FinalReport(object):
    """Simple case with residential, MUD, workplace, public L2, public fast charging."""
    def __init__(self, total_num_evs, aggregation_level='state', county=None, res_percent=0.5,
                 fast_percent=0.18, publicl2_percent=0.02,
                 work_percent=0.3, rent_percent=0,
                 l1_percent=0, res_l2_smooth=False, week_day=True,
                 res_daily_use=1.0, work_daily_use=1.0, fast_daily_use=0.3, publicl2_daily_use=1.0,
                 mixed_batteries=None, time_steps=1440, geo=None):

        if mixed_batteries is None:
            self.mixed_distributions = False
        else:
            self.mixed_distributions = True
            self.mixed_distribution_proportions = mixed_batteries

        self.week_day = week_day
        self.gmm_bucket = 'script.control.tool'
        self.s3client = boto3.client('s3')
        self.gmm_folder_path = 'Sessions_Model_Objects/'
        self.joint_gmms = True  # always true now
        self.reweight_gmms = False

        self.control_bucket = 'script.control.tool'
        self.control_folder_path = 'Control_Objects'

        self.aggregation_level = aggregation_level
        if self.aggregation_level == 'state':
            self.num_ev_owners = int(total_num_evs)
        elif self.aggregation_level == 'county':
            if county is None:
                print('Error! County chosen as aggregation level but no county given.')
            else:
                if geo is None:
                    geo_distribution = pd.read_csv(
                        's3://script.control.tool/geo_distribution/new_distribution_of_lightduty_evs_by_county.csv')
                else:
                    geo_distribution = geo.copy(deep=True)
                geo_distribution['Fraction'] = geo_distribution['EVs'].values / geo_distribution['EVs'].sum()
                county_index = geo_distribution[geo_distribution['County'] == county].index[0]
                self.num_ev_owners = int(geo_distribution.loc[county_index, 'Fraction'] * total_num_evs)

        self.num_fast = int(fast_daily_use * fast_percent * self.num_ev_owners)
        self.num_publicl2 = int(publicl2_daily_use * publicl2_percent * self.num_ev_owners)
        self.num_work = int(work_daily_use * work_percent * self.num_ev_owners)

        self.num_res = int(res_daily_use * res_percent * self.num_ev_owners)
        self.num_mud = int(rent_percent * self.num_res)
        self.num_res_l1 = int(l1_percent * (self.num_res - self.num_mud))
        self.num_res_l2 = int(self.num_res - self.num_mud - self.num_res_l1)

        # 1 minute vs 15 minute intervals
        self.sample_fast = False
        if time_steps == 1440:
            self.time_step = 1/60
            self.num_time_steps = 1440
            self.time_steps_per_hour = 60
            self.fast_time_steps_per_hour = 60
            self.fast_num_time_steps = 1440
            self.start_scaler = (1/60)
            self.sample_fast = False
        else:
            self.time_step = 0.25
            self.num_time_steps = 96
            self.time_steps_per_hour = 4
            self.fast_time_steps_per_hour = 60
            self.fast_num_time_steps = int(60 * 24)
            self.start_scaler = (1 / (60*15))

        self.categories_dict = {'Segment': ['Residential L1', 'Residential L2', 'Residential MUD', 'Work',
                                            'Public L2', 'Fast'],
                                'Label': ['Residential L1', 'Residential L2', 'Residential MUD', 'Workplace',
                                          'Public L2', 'Fast'],
                                'Vehicles': [self.num_res_l1, self.num_res_l2, self.num_mud, self.num_work,
                                             self.num_publicl2, self.num_fast],
                                'GMM Sub Path': ['sessions2019_home_slow_smoothl1_weekday_allbatt_se_5_gmm.p',
                                                 'sessions2019_home_slow_weekday_allbatt_se_5_gmm.p',
                                                 'sessions2019_mud_slow_weekday_allbatt_se_6_gmm.p',
                                                 'sessions2019_work_slow_weekday_allbatt_se_5_gmm.p',
                                                 'sessions2019_other_slow_weekday_allbatt_se_6_gmm.p',
                                                 'sessions2019_other_fast_weekday_allbatt_se_4_gmm.p'],
                                'Rate': [1.4, 6.6, 6.6, 6.6, 6.6, 150.0],
                                'Energy Clip': [40, 75, 75, 75, 75, 75],
                                'Num Time Steps': [self.num_time_steps, self.num_time_steps, self.num_time_steps,
                                                   self.num_time_steps, self.num_time_steps, self.fast_num_time_steps],
                                'Time Steps Per Hour': [self.time_steps_per_hour, self.time_steps_per_hour,
                                                        self.time_steps_per_hour, self.time_steps_per_hour,
                                                        self.time_steps_per_hour, self.fast_time_steps_per_hour],
                                'Start Time Scaler': [self.start_scaler, self.start_scaler, self.start_scaler,
                                                      self.start_scaler, self.start_scaler, (1 / 60)]}

        if not self.week_day:
            self.categories_dict['GMM Sub Path'] = ['sessions2019_home_slow_smoothl1_weekend_allbatt_se_6_gmm.p',
                                                    'sessions2019_home_slow_weekend_allbatt_se_6_gmm.p',
                                                    'sessions2019_mud_slow_weekend_allbatt_se_8_gmm.p',
                                                    'sessions2019_work_slow_weekend_allbatt_se_4_gmm.p',
                                                    'sessions2019_other_slow_weekend_allbatt_se_6_gmm.p',
                                                    'sessions2019_other_fast_weekend_allbatt_se_5_gmm.p']

        if res_l2_smooth:
            self.categories_dict['GMM Sub Path'][1] = self.categories_dict['GMM Sub Path'][0]

