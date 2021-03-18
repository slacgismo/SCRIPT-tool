import boto3
import json
import psycopg2
from django.conf import settings


class UploadToPostgres():
    def __init__(
        self,
        county,
        rate_energy_peak,
        rate_energy_partpeak,
        rate_energy_offpeak,
        rate_demand_peak,
        rate_demand_partpeak,
        rate_demand_overall
    ):
        with open(settings.BASE_DIR + '/postgres_info.json') as json_file:
            postgres_info = json.load(json_file)

        self.db_host = postgres_info['DB_HOST']
        self.table_name = "script_config_load_controller"
        self.postgres_db = postgres_info['POSTGRES_DB']
        self.postgres_user = postgres_info['POSTGRES_USER']
        self.postgres_password = postgres_info['POSTGRES_PASSWORD']
        self.county = county
        self.rate_energy_peak = rate_energy_peak
        self.rate_energy_partpeak = rate_energy_partpeak
        self.rate_energy_offpeak = rate_energy_offpeak
        self.rate_demand_peak = rate_demand_peak
        self.rate_demand_partpeak = rate_demand_partpeak
        self.rate_demand_overall = rate_demand_overall
        self.num_of_run = 4

    def run(self, baseline_profiles, controlled_profiles):

        conn = psycopg2.connect(
            host=self.db_host,
            dbname=self.postgres_db,
            user=self.postgres_user,
            password=self.postgres_password,
            port='5432'
        )

        cur = conn.cursor()

        # upload data into Postgres
        baseline_profiles_list = []
        controlled_profiles_list = []

        start_hour = 0
        start_minute = 0

        lines = len(baseline_profiles / 4)
        for line in range(lines):
            hour_str = str((start_hour + line % 4)% 24)
            minute = 15 * (line % 4)
            if minute is 0:
                minute_str = '00'
            else:
                minute_str = str(minute)

            baseline_profiles_list.append(
                {
                    'time': hour_str + ':' + minute_str,
                    'load': str(baseline_profiles[line][self.num_of_run - 1])
                }
            )

            controlled_profiles_list.append(
                {
                    'time': hour_str + ':' + minute_str,
                    'load': str(controlled_profiles[line][self.num_of_run - 1])
                }
            )


        cur.execute("INSERT INTO " + self.table_name + \
            " (county, rate_energy_peak, rate_energy_partpeak, rate_energy_offpeak," + \
            " rate_demand_peak, rate_demand_partpeak, rate_demand_overall)" + \
            " VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (
                self.county, str(self.rate_energy_peak), str(self.rate_energy_partpeak), str(self.rate_energy_offpeak),
                str(self.rate_demand_peak), str(self.rate_demand_partpeak), str(self.rate_demand_overall)
            )
        )

        conn.commit()

        cur.execute("SELECT id FROM " + self.table_name + " ORDER BY id DESC LIMIT 1")

        config_id = cur.fetchone()

        cur.execute("INSERT INTO script_algorithm_load_controller" + \
            " (config, uncontrolled_load, controlled_load)" + \
            " VALUES (%s, %s, %s)",
            (
                config_id, json.dumps(baseline_profiles_list), json.dumps(controlled_profiles_list)
            )
        )

        print('Insertion finished...')
        # Make the changes to the database persistent
        conn.commit()

        # Close communication with the database
        cur.close()
        conn.close()
