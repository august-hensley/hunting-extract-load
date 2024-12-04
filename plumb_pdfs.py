import pandas as pd
import numpy as np
import pdfplumber
import sys
import os
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('species', help='Required, specify any of these after the file name: \
                                    \n deer, elk, moose, pronghorn, or turkey')
parser.add_argument('--start', help='Optional: choose the first year of data to collect. Default is 2019',
                     default=2019)
parser.add_argument('--end', help='Optional: choose the last year of data to collect. Default is 2019',
                     default=2024)
args = parser.parse_args()
start_year = int(args.start)
end_year = int(args.end) + 1

species = args.species
years = [year for year in range(start_year, end_year)]

# The desired tables are found at varying indecies, this maps to the appropriate ones
applicant_table_numbers = {
                            'deer': {'default': 6, 2020: 5},
                            'elk': {'default': 6, 2020: 5},
                            'pronghorn': {'default': 6, 2020: 5, 2024: 5},
                            'turkey': {'default': 6, 2021: 5, 2024: 5},
                            'moose': {'default': 7, 2020: 6, 2024: 6},
                          }

def plumb_files(year):
    if year in applicant_table_numbers[species].keys():
        app_table_num = applicant_table_numbers[species][year]
    else:
        app_table_num = applicant_table_numbers[species]['default']
    succ_table_num = app_table_num + 1

    destination_path = f'draw_report_data/{species.lower()}/{year}'
    pdf_path = os.path.join(os.getcwd(), 'draw_recap_files', species, f'{year}_{species}_draw_report.pdf')
    
    with pdfplumber.open(pdf_path) as pdf:
        if not os.path.exists(destination_path):
            os.makedirs(destination_path)
        
        i = 2
        for page in pdf.pages[2:]:
            i += 1
            # Using pdfplumber's extract_tables() -- https://github.com/jsvine/pdfplumber
            tables = page.extract_tables()
            if len(tables) == 0:
                continue

            # This makes sure the new page isn't a spillover of the hunt code from previous page
            new_code = tables[0][0][0][:11] == 'Total Quota' or tables[0][0][0] == 'Pre-Draw\nQuotas'
            if new_code == False:
                continue
            # Collecting the new hunt code
            if species == 'turkey':
                if year not in [2021, 2024]:
                    hunt_code = tables[0][2][1]
                else:
                    hunt_code = tables[0][1][1]
            # TODO: make this explicit #
            elif year != 2015:
                try:
                    hunt_code = tables[0][2][1]
                except:
                    hunt_code = tables[0][1][1]
            else:
                try:
                    hunt_code = tables[4][1][1]
                except:
                    print(page, tables[0][0][0])
                    continue
            # --------------   #
            
            # Extracting the desired tables (highlighted in orange and blue within the pdf)
            applicants = tables[app_table_num][3:]
            successful = tables[succ_table_num][3:]

            # Checks if the last row is truly the last row or the end of the page
            if applicants[-1][0] != 'Grand Total' and applicants[-1][1] != 'Grand Total':
                # If it's the end of the page then this collects the remaining rows from the next page
                tables_cont = pdf.pages[i].extract_tables()
                
                if species == 'moose':
                    num_columns = 9
                else:
                    num_columns = 8
                for row in tables_cont[0]:
                    while len(row) < num_columns:
                        row.insert(1, '')
                    applicants.append(row)
                    if row[0] == 'Grand Total':
                        break
                   
                for row in tables_cont[1]:
                    while len(row) < num_columns:
                        row.insert(1, '')
                    successful.append(row)
                    if row[0] == 'Grand Total':
                        break
                    
            try:
                apps = np.array(applicants)
                succ = np.array(successful)
            except:
                print(page, hunt_code, successful)
                apps = np.array(applicants)
                succ = np.array(successful)
            
            if species == 'moose':
                df = pd.DataFrame({
                    'choice': apps[:,0],
                    'points': apps[:,1],
                    'weighted_points': apps[:,2],
                    'res_apps': apps[:,3],
                    'res_draws': succ[:,3],
                    'non_res_apps': apps[:,4],
                    'non_res_draws': succ[:,4],
                })
            else:
                df = pd.DataFrame({
                    'choice': apps[:,0],
                    'points': apps[:,1],
                    'res_apps': apps[:,2],
                    'res_draws': succ[:,2],
                    'non_res_apps': apps[:,3],
                    'non_res_draws': succ[:,3],
                })

            df['year'] = year
            df['hunt_code'] = hunt_code
            
            df['res_apps'] = df['res_apps'].replace('-', 0).astype(int)
            df['res_draws'] = df['res_draws'].replace('-', 0).astype(int)
            df['non_res_apps'] = df['non_res_apps'].replace('-', 0).astype(int)
            df['non_res_draws'] = df['non_res_draws'].replace('-', 0).astype(int)

            df.to_csv(f'{destination_path}/{hunt_code}_{year}.csv', index=False)



for year in years:
    plumb_files(year)
    print(year, 'successfully plumbed')