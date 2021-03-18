import boto3
import json
import psycopg2
import numpy as np
import pandas as pd
import csv


class UploadToPostgres():
    def __init__(self):
        with open("postgres_info.json") as json_file:
            postgres_info = json.load(json_file)

        self.db_host = postgres_info["DB_HOST"]
        self.table_county = "script_county"
        self.postgres_db = postgres_info['POSTGRES_DB']
        self.postgres_user = postgres_info['POSTGRES_USER']
        self.postgres_password = postgres_info['POSTGRES_PASSWORD']


    def run(self):

        conn = psycopg2.connect(
            host=self.db_host,
            dbname=self.postgres_db,
            user=self.postgres_user,
            password=self.postgres_password,
            port="5432"
        )
        county_data = pd.read_csv("s3://script.control.tool/County List/county_summary_data.csv")
        # For each county, using the data from 2019: what is the total number of sessions throughout the year? what is the total energy delivered throughout the year? what is the maximum amount of energy delivered on any one day of the year (peak energy)?
        cur = conn.cursor()

        for x, (k, name) in enumerate(county_data["name"].items()):
            cur.execute("INSERT INTO " + self.table_county + \
                " (name, total_session, total_energy, peak_energy)" + \
                " VALUES (%s, %s, %s, %s)",
                (
                    name,
                    county_data["total_session"][k],
                    county_data["total_energy"][k],
                    county_data["peak_energy"][k]
                )
            )

        conn.commit()
        conn.close()

if __name__ == "__main__":
    client = UploadToPostgres()
    client.run()
