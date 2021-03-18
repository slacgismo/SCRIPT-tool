from django.urls import path, include
from rest_framework import routers
from script.views import CountyViewSet, ZipCodeViewSet, EnergyViewSet
from script.views import LoadControllerConfigViewSet, LoadForecastConfigViewSet, CostBenefitConfigViewSet
from script.views import LoadForecastViewSet, LoadControllerViewSet, CostBenefitViewSet
from script.views import  CostBenefitAnalysisRunner
from script.views import LoadControlRunner, LoadForecastRunner, DownloadCBAZip
# set up a router for RESTful API
# ref1: https://www.django-rest-framework.org/api-guide/routers/
# ref2: https://www.django-rest-framework.org/api-guide/filtering/
# an idea: /api/<algorithm_name>/<unique_hash_of_parameter>, if algorithm parameters are not too many
# router.register('api/energy/county/(?P<county>[-\w]+)/year/(?P<year>[-\w]+)/month/(?P<month>[-\w]+)', EnergyView.as_view(), 'energy')

# Tip:
# 1. replace space with %20 in the request urls


router = routers.DefaultRouter()
router.register('county', CountyViewSet, 'county')
router.register('zipcode', ZipCodeViewSet, 'zipcode')
router.register('energy', EnergyViewSet, 'energy')


# Configuration for algorithms:
router.register('config/load_controller', LoadControllerConfigViewSet, 'config/load_controller')
router.register('config/load_forecast', LoadForecastConfigViewSet, 'config/load_forecast')
router.register('config/cost_benefit', CostBenefitConfigViewSet, 'config/cost_benefit')


# Algorithm-1: load controller
router.register('algorithm/load_controller', LoadControllerViewSet, 'algorithm/load_controller')

# Algorithm-2: EV load forecast
router.register('algorithm/load_forecast', LoadForecastViewSet, 'algorithm/load_forecast')

# Algorithm-3: cost benefit analysis
router.register('algorithm/cost_benefit_analysis/cost_benefit', CostBenefitViewSet, 'algorithm/cost_benefit_analysis/cost_benefit')

urlpatterns = [
    path('load_control_runner', LoadControlRunner.as_view()),
    path('cost_benefit_analysis_runner', CostBenefitAnalysisRunner.as_view()),
    path('load_forecast_runner', LoadForecastRunner.as_view()),
    path('download_cba_zip', DownloadCBAZip.as_view()),
    path('', include(router.urls)),
]
