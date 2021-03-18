import json
import boto3
import datetime
import psycopg2
from django.conf import settings
from script.models.algorithms import LoadForecast
from script.models.config import LoadForecastConfig


class UploadToPostgres():
    def __init__(
        self,
        residential_l1_load_uncontrolled,
        residential_l2_load_uncontrolled,
        residential_mud_load_uncontrolled,
        work_load_uncontrolled,
        fast_load_uncontrolled,
        public_l2_load_uncontrolled,
        total_load_uncontrolled,
        residential_l1_load_controlled,
        residential_l2_load_controlled,
        residential_mud_load_controlled,
        work_load_controlled,
        fast_load_controlled,
        public_l2_load_controlled,
        total_load_controlled,
    ):

        with open(settings.BASE_DIR + '/postgres_info.json') as json_file:
            postgres_info = json.load(json_file)

        self.db_host = postgres_info['DB_HOST']
        self.table_name = "script_algorithm_ev_load_forecast"
        self.config_table_name = "script_config_ev_load_forecast"
        self.postgres_db = postgres_info['POSTGRES_DB']
        self.postgres_user = postgres_info['POSTGRES_USER']
        self.postgres_password = postgres_info['POSTGRES_PASSWORD']
        self.max_profiles = 4
        self.residential_l1_load_uncontrolled = residential_l1_load_uncontrolled
        self.residential_l2_load_uncontrolled = residential_l2_load_uncontrolled
        self.residential_mud_load_uncontrolled = residential_mud_load_uncontrolled
        self.fast_load_uncontrolled = fast_load_uncontrolled
        self.work_load_uncontrolled = work_load_uncontrolled
        self.public_l2_load_uncontrolled = public_l2_load_uncontrolled
        self.total_load_uncontrolled = total_load_uncontrolled
        self.residential_l1_load_controlled = residential_l1_load_controlled
        self.residential_l2_load_controlled = residential_l2_load_controlled
        self.residential_mud_load_controlled = residential_mud_load_controlled
        self.fast_load_controlled = fast_load_controlled
        self.work_load_controlled = work_load_controlled
        self.public_l2_load_controlled = public_l2_load_controlled
        self.total_load_controlled = total_load_controlled


    def prep_data(
        self,
        residential_l1_load,
        residential_l2_load,
        residential_mud_load,
        work_load,
        fast_load,
        public_l2_load,
        total_load,
    ):
        ''' data separated into lists before upload to db '''
        residential_l1_load_list = []
        residential_l2_load_list = []
        residential_mud_load_list = []
        fast_load_list = []
        work_load_list = []
        public_l2_load_list = []
        total_load_list = []

        start_hour = 0
        start_minute = 0

        time_point_len = len(residential_l1_load)

        for i in range(time_point_len):
            hour_str = str((start_hour + i // 60) % 24)
            minute = i % 60
            if minute in range(10):
                minute_str = '0' + str(minute)
            else:
                minute_str = str(minute)

            residential_l1_load_list.append(
                {
                    'time': hour_str + ':' + minute_str,
                    'load': str(round(residential_l1_load[i], 2))
                }
            )

            residential_l2_load_list.append(
                {
                    'time': hour_str + ':' + minute_str,
                    'load': str(round(residential_l2_load[i], 2))
                }
            )

            residential_mud_load_list.append(
                {
                    'time': hour_str + ':' + minute_str,
                    'load': str(round(residential_mud_load[i], 2))
                }
            )

            fast_load_list.append(
                {
                    'time': hour_str + ':' + minute_str,
                    'load': str(round(fast_load[i], 2))
                }
            )

            work_load_list.append(
                {
                    'time': hour_str + ':' + minute_str,
                    'load': str(round(work_load[i], 2))
                }
            )

            public_l2_load_list.append(
                {
                    'time': hour_str + ':' + minute_str,
                    'load': str(round(public_l2_load[i], 2))
                }
            )

            total_load_list.append(
                {
                    'time': hour_str + ':' + minute_str,
                    'load': str(round(total_load[i], 2))
                }
            )

        return (residential_l1_load_list,
                residential_l2_load_list,
                residential_mud_load_list,
                fast_load_list,
                work_load_list,
                public_l2_load_list,
                total_load_list)


    def run(
        self,
        config_name,
        aggregation_level,
        num_evs,
        county_choice,
        fast_percent,
        work_percent,
        res_percent,
        l1_percent,
        publicl2_percent,
        res_daily_use,
        work_daily_use,
        fast_daily_use,
        rent_percent,
        res_l2_smooth,
        week_day,
        publicl2_daily_use,
        mixed_batteries,
        timer_control,
        work_control
    ):
        # replaces the oldest profile when profile count reaches max
        profile_count = LoadForecastConfig.objects.count()
        if (profile_count >= self.max_profiles):
            oldest_profile = LoadForecastConfig.objects.order_by('created_at')[0]
            oldest_profile.loadforecast_set.all().delete()
            oldest_profile.delete()

        conn = psycopg2.connect(
            host=self.db_host,
            dbname=self.postgres_db,
            user=self.postgres_user,
            password=self.postgres_password,
            port='5432'
        )
        cur = conn.cursor()

        cur.execute("INSERT INTO " + self.config_table_name + \
            " (config_name, aggregation_level, num_evs, choice," + \
            " fast_percent, work_percent, res_percent, l1_percent, public_l2_percent," + \
            " res_daily_use, work_daily_use, fast_daily_use, rent_percent, res_l2_smooth," + \
            " week_day, publicl2_daily_use, mixed_batteries, timer_control, work_control, created_at)" + \
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                str(config_name), str(aggregation_level), str(int(num_evs)), str(county_choice), str(fast_percent), \
                str(work_percent), str(res_percent), str(l1_percent), str(publicl2_percent), str(res_daily_use), \
                str(work_daily_use), str(fast_daily_use), str(rent_percent), str(res_l2_smooth), str(week_day), \
                str(publicl2_daily_use), str(mixed_batteries), str(timer_control), str(work_control), \
                datetime.datetime.now()
            )
        )

        # uncontrolled
        (residential_l1_load_list_uncontrolled,
        residential_l2_load_list_uncontrolled,
        residential_mud_load_list_uncontrolled,
        fast_load_list_uncontrolled,
        work_load_list_uncontrolled,
        public_l2_load_list_uncontrolled,
        total_load_list_uncontrolled) = self.prep_data(
            self.residential_l1_load_uncontrolled,
            self.residential_l2_load_uncontrolled,
            self.residential_mud_load_uncontrolled,
            self.fast_load_uncontrolled,
            self.work_load_uncontrolled,
            self.public_l2_load_uncontrolled,
            self.total_load_uncontrolled,
            )

        cur.execute("INSERT INTO " + self.table_name + \
            " (config, controlled, residential_l1_load, residential_l2_load, residential_mud_load, fast_load," + \
            " work_load, public_l2_load, total_load)" + \
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                str(config_name), str(0),
                json.dumps(residential_l1_load_list_uncontrolled), json.dumps(residential_l2_load_list_uncontrolled),
                json.dumps(residential_mud_load_list_uncontrolled), json.dumps(fast_load_list_uncontrolled),
                json.dumps(work_load_list_uncontrolled), json.dumps(public_l2_load_list_uncontrolled), json.dumps(total_load_list_uncontrolled)
            )
        )

        # controlled
        (residential_l1_load_list_controlled,
        residential_l2_load_list_controlled,
        residential_mud_load_list_controlled,
        fast_load_list_controlled,
        work_load_list_controlled,
        public_l2_load_list_controlled,
        total_load_list_controlled) = self.prep_data(
            self.residential_l1_load_controlled,
            self.residential_l2_load_controlled,
            self.residential_mud_load_controlled,
            self.fast_load_controlled,
            self.work_load_controlled,
            self.public_l2_load_controlled,
            self.total_load_controlled,
            )

        cur.execute("INSERT INTO " + self.table_name + \
            " (config, controlled, residential_l1_load, residential_l2_load, residential_mud_load, fast_load," + \
            " work_load, public_l2_load, total_load)" + \
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                str(config_name), str(1),
                json.dumps(residential_l1_load_list_controlled), json.dumps(residential_l2_load_list_controlled),
                json.dumps(residential_mud_load_list_controlled), json.dumps(fast_load_list_controlled),
                json.dumps(work_load_list_controlled), json.dumps(public_l2_load_list_controlled), json.dumps(total_load_list_controlled)
            )
        )

        # Make the changes to the database persistent
        conn.commit()

        # Close communication with the database
        cur.close()
        conn.close()
