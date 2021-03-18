from script.LoadForecasting.EvLoadModel import EVLoadModel
from script.LoadForecasting.configurations import FinalReport
import numpy as np
import pandas as pd
from script.LoadForecasting.UploadToPostgres import *
import logging
from pathlib import Path


logger = logging.getLogger(__name__)

def lf_runner(argv):

    mixed_batteries = {'smallbatt': argv['small_batt'], 'allbatt': argv['all_batt'], 'bigbatt': argv['big_batt']}

    config = FinalReport(total_num_evs=argv['total_num_evs'], aggregation_level=argv['aggregation_level'], county=argv['county'],
                         res_percent=argv['res_percent'], fast_percent=argv['fast_percent'], publicl2_percent=argv['publicl2_percent'], work_percent=argv['work_percent'],
                         rent_percent=argv['rent_percent'], l1_percent=argv['l1_percent'], res_l2_smooth=argv['res_l2_smooth'], week_day=argv['week_day'],
                         res_daily_use=argv['res_daily_use'], work_daily_use=argv['work_daily_use'], fast_daily_use=argv['fast_daily_use'], publicl2_daily_use=argv['publicl2_daily_use'],
                         mixed_batteries=mixed_batteries, time_steps=1440)

    model = EVLoadModel(config)
    model.calculate_basic_load(verbose=False)

    # uncontrolled data prep before db
    total = np.zeros((np.shape(model.load_segments['Residential L1']['Load'])[0], 7))
    total[:, 0] = model.load_segments['Residential L1']['Load']
    total[:, 1] = model.load_segments['Residential L2']['Load']
    total[:, 2] = model.load_segments['Residential MUD']['Load']
    total[:, 3] = model.load_segments['Work']['Load']
    total[:, 4] = model.load_segments['Fast']['Load'][np.arange(0, 1440, 1)]
    total[:, 5] = model.load_segments['Public L2']['Load']
    total[:, 6] = np.sum(total, axis=1)
    total_df = pd.DataFrame(data=total, columns=['Residential L1', 'Residential L2', 'Residential MUD', 'Work', 'Fast', 'Public L2', 'Total'])


    # apply control, controlled data prep before db
    model.apply_control(control_rule=argv['work_control'], segment='Work')
    total_controlled = np.zeros((np.shape(model.sampled_controlled_loads_dict['Residential L1'])[0], 7))
    total_controlled[:, 0] = model.sampled_controlled_loads_dict['Residential L1']
    total_controlled[:, 1] = model.sampled_controlled_loads_dict['Residential L2']
    total_controlled[:, 2] = model.sampled_controlled_loads_dict['Residential MUD']
    total_controlled[:, 3] = model.sampled_controlled_loads_dict['Work']
    total_controlled[:, 4] = model.sampled_controlled_loads_dict['Fast']
    total_controlled[:, 5] = model.sampled_controlled_loads_dict['Public L2']
    total_controlled[:, 6] = np.sum(total_controlled, axis=1)
    total_controlled_df = pd.DataFrame(data=total_controlled, columns=['Residential L1', 'Residential L2', 'Residential MUD', 'Work', 'Fast', 'Public L2', 'Total'])

    upload_to_postgres_client = UploadToPostgres(
        total[:, 0],
        total[:, 1],
        total[:, 2],
        total[:, 3],
        total[:, 4],
        total[:, 5],
        total[:, 6],
        total_controlled[:, 0],
        total_controlled[:, 1],
        total_controlled[:, 2],
        total_controlled[:, 3],
        total_controlled[:, 4],
        total_controlled[:, 5],
        total_controlled[:, 6],
    )

    upload_to_postgres_client.run(
        argv['config_name'],
        argv['aggregation_level'],
        argv['total_num_evs'],
        argv['county'],
        argv['fast_percent'],
        argv['work_percent'],
        argv['res_percent'],
        argv['l1_percent'],
        argv['publicl2_percent'],
        argv['res_daily_use'],
        argv['work_daily_use'],
        argv['fast_daily_use'],
        argv['rent_percent'],
        argv['res_l2_smooth'],
        argv['week_day'],
        argv['publicl2_daily_use'],
        mixed_batteries,
        argv['timer_control'],
        argv['work_control']
    )
    
    # set file path to save csv models
    path = Path(__file__).parent.resolve()
    parent_path = path.parent

    # get correct county choice name
    if argv['aggregation_level'] == 'state':
        county = "All California"
    else:
        county = argv['county']
    
    # save uncontrolled and uncontrolled models
    if argv['week_day']:
        week_choice = 'weekday'
        pd.DataFrame(model.sampled_loads_dict).to_csv(str(parent_path)+'/costbenefitanalysis/preprocessing_loadprofiles/inputs/weekdays/BaseCase_2025_' + week_choice + '_' + county + '_county_uncontrolled_load_' + argv['config_name'] + '.csv') 
        pd.DataFrame(model.sampled_controlled_loads_dict).to_csv(str(parent_path)+'/costbenefitanalysis/preprocessing_loadprofiles/inputs/weekdays/BaseCase_2025_'+ week_choice + '_' + county + '_county_e19controlled_load_' + argv['config_name'] + '.csv')
    else:
        week_choice = 'weekend'
        pd.DataFrame(model.sampled_loads_dict).to_csv(str(parent_path)+'/costbenefitanalysis/preprocessing_loadprofiles/inputs/weekends/BaseCase_2025_' + week_choice + '_' + county + '_county_uncontrolled_load_' + argv['config_name'] + '.csv')
        pd.DataFrame(model.sampled_controlled_loads_dict).to_csv(str(parent_path)+'/costbenefitanalysis/preprocessing_loadprofiles/inputs/weekends/BaseCase_2025_'+ week_choice + '_' + county + '_county_e19controlled_load_' + argv['config_name'] + '.csv')


    logger.info('Upload to Postgres for Load Forecasting succeeded.')
