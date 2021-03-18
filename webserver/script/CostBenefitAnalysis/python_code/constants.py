from __future__ import unicode_literals

### MODEL CONSTANTS ###
demandcharge_components = {1: 'monthly_max',
                           2: 'peak_max',
                           3: 'partpeak_max1',
                           4: 'partpeak_max2',
                           5: 'additional_demand_charge'}
inflation = 0.022

charger_name_to_population_attr = {
    'Residential L2': 'res_evses',
    'Residential L1': 'res_evses',
    'Public L2': 'public_l2_evses',
    'DCFC': 'dcfc_evses',
    'Workplace L2': 'workplace_evses'
}

charger_name_conversion = {'Residential L2': 'Res',
                           'Residential L1': 'Res',
                           'Workplace L2': 'Work',
                           'Public L2': 'L2',
                           'DCFC': 'DC'}

demand_charge_weighting = {
    0: 0.026202004,
    1: 0.027443322,
    2: 0.027981455,
    3: 0.025765024,
    4: 0.027566949,
    5: 0.033585224,
    6: 0.042799335,
    7: 0.047177492,
    8: 0.058827305,
    9: 0.058713982,
    10: 0.06289745,
    11: 0.055118541,
    12: 0.064267933,
    13: 0.067388808,
    14: 0.05822333,
    15: 0.053568604,
    16: 0.043086649,
    17: 0.037605278,
    18: 0.03403196,
    19: 0.029161013,
    20: 0.029837142,
    21: 0.028384777,
    22: 0.03128368,
    23: 0.029082743}

directory_list = ['LOCAL_CASE_DIR','RESULTS_DIR']

MMBTU_per_gal = 120476
