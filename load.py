import psycopg2
import glob
import argparse
import time
from configobj import ConfigObj

conf = ConfigObj('postgres_cfg.ini')
section = conf['user secrets']
username = section['username']
password = section['password']
db = section['database']


parser = argparse.ArgumentParser()
parser.add_argument('species', help='Required, specify any of these after the file name: \
                                    \n deer, elk, moose, pronghorn, or turkey',
                    default='all')
args = parser.parse_args()
species = args.species
if species == 'all':
    species = ['deer', 'elk', 'pronghorn', 'moose', 'turkey']
else:
    species = [species]


def get_create_sql(animal):
    if animal == 'moose':
        wp = 'weighted_points varchar,'
    else:
        wp = ''

    return f"""
            CREATE TABLE IF NOT EXISTS {animal}_draw (
                choice varchar,
                points varchar,
                {wp}
                res_apps integer,
                res_draws integer,
                non_res_apps integer,
                non_res_draws integer,
                year smallint,
                hunt_code varchar
            );
            """


conn = psycopg2.connect(
    host="localhost",
    database=db,
    user=username,
    password=password
)
cur = conn.cursor()

for animal in species:
    t0 = time.time()
    cur.execute(f'DROP TABLE IF EXISTS {animal}_draw;')
    cur.execute(get_create_sql(animal))
    conn.commit()

    csvs = glob.glob(f'draw_report_data/{animal}/*/*.csv')

    for csv in csvs:
        with open(csv, 'r') as f:
            cur.copy_expert(f"COPY {animal}_draw FROM STDIN WITH CSV HEADER DELIMITER ','", f)
            conn.commit()

    t1 = time.time()
    print(f'{animal} loaded to public schema in {round((t1 - t0), 2)} seconds')

cur.close()
conn.close()