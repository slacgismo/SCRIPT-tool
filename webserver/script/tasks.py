import sys
from celery import shared_task, current_task
from script.CostBenefitAnalysis.preprocessing_loadprofiles.split_file import split_file
from script.CostBenefitAnalysis.UploadToPostgres import UploadToPostgres
from script.LoadForecasting.LoadForecastingRunner import lf_runner
#for running CBA tool
sys.path.append("script/CostBenefitAnalysis/python_code/")
from model_class import ModelInstance

@shared_task
def run_cba_tool(profile_name, county_data):
    split_file(load_profile = profile_name, county = county_data[0], controlled_types = ["uncontrolled", "e19controlled"])
    ModelInstance("BaseCase_" + county_data[0] + "_uncontrolled_load")
    ModelInstance("BaseCase_" + county_data[0] + "_e19controlled_load")
    UploadToPostgres(load_profile = profile_name, county=county_data[0])

@shared_task
def run_lf_runner(lf_argv):
    lf_runner(argv = lf_argv)
