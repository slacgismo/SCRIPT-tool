# SCRIPT - Smart ChaRging Infrastructure Planning Tool
This repository comprises two parts: 
1. Information about the journal paper "Large Scale Scenarios of Electric Vehicle Charging with a Data-Driven Model of Control", and
2. Code to run the tool itself.

This project was funded by the California Energy Commission under grant EPC-16-057. 

Principal Investigator: Gustavo Vianna Cezar. 

For more information about the Grid Integration Systems and Mobility (GISMo) group within SLAC National Accelerator Laboratory visit https://gismo.slac.stanford.edu/. SLAC National Accelerator Laboratory is operated for the US Department of Energy by Stanford University under Contract DE-AC02-76SF00515.

# Paper
Powell, S., Cezar, G. V., Apostolaki-Iosifidou, E., & Rajagopal, R. (2021). "Large Scale Scenarios of Electric Vehicle Charging with a Data-Driven Model of Control." Under review. 

Corresponding authors: Siobhan Powell (siobhan.powell at stanford.edu) and Ram Rajagopal (ramr at stanford.edu).

### Summary

Long-term planning for transportation electrification demands large-scale, detailed, data-driven scenarios for future charging demand. Controlled charging is a powerful and growing tool for managing the impact of charging on the grid; it is critical to include in planning scenarios. 

Many scenario tools today, however, are expensive to scale and cannot represent complex load controls. In this paper and tool we address that gap. We present a scalable tool for scenario generation based in real data from the California Bay Area, and we present a novel methodology to model the impact of load management control on aggregate charging profiles using machine learning. 

### Model Objects

Core to our methodology is the separation of model training from scenario generation. The tool below does not reference the raw data directly but uses pre-trained model objects. To make those easy to access by the research community, we have made the model objects available for download here: 

* Control models: https://s3-us-west-1.amazonaws.com/script.control.tool/Control_Objects/public_control_model_objects.zip
* Sessions models: https://s3-us-west-1.amazonaws.com/script.control.tool/Sessions_Model_Objects/public_sessions_model_objects.zip


### Paper Code 

The paper highlights rate design as an application for this tool using the following procedure:
1. Generate data using the sessions model
2. Define a custom rate schedule to study
3. Build training data for that rate schedule and learn its mapping
4. Apply the mapping within the model to study its impact on a large-scale scenario.
Code for that application is included here in the folder `PaperCode/CustomRate`

The main model code is also embedded and used in the tool below to generate new scenarios. Further code associated with the paper is available on request. 



# Tool
Developers: Anna Peery, Derin Serbetcioglu, Jonathan Goncalves

Supervised by: Gustavo Vianna Cezar

Contributors: Robbie Shaw, Siobhan Powell, Yanqing Wang, Heather Zhang, Proverbs Xu, Leezki, and xinyile

### Structure

```text
SCRIPT/
    webserver/                  ---- Django REST Framework web server
        manage.py
        app/                    ---- settings
        script/                 ---- script web app
    frontend/                   ---- React
        src/                    ---- source code
    ec2setup/                   ---- code running on EC2
    utils/                      ---- Utils which can be copied by all images during image build
        mosek/                  ---- mosek license
    variable.env                ---- Configuration for environment variables
    UploadToCounty/             ---- Includes script to populate the counties table
```

## Getting Started with SCRIPT Running Locally

### install postgres first to avoid headaches
```sh
$ brew install postgresql
```

### to start the DB server you can just:
```sh
$ brew services start postgresql
```

### to create the DB
```sh
$ createdb scriptdb
```

##### To connect to the DB - I used [TablePlus](https://tableplus.com/). Connection params for development are the postgres defaults. You can also check the settings file to find them: `webserver/app/settings/base.py`. For now just save the new connection - we will connect to it once the Django Server is running


### Creating the env - ensure you are running the anaconda `4.5.x +`
```sh
$ conda env create -f environment.yml
```

### Updating the env with latest
```sh
$ conda env update -f environment.yml
```

### Updating the environment.yml file after adding new packages locally
```sh
$ conda env export --name venv_script > environment.yml
```

### Starting the env
```sh
$ conda activate venv_script
```

### Stopping the env
```sh
$ conda deactivate
```

### Migrate the DB
```sh
$ cd webserver
$ python manage.py migrate --settings=app.settings.base
```

### Upload County Data (this part will take about 15 minutes)
```sh
$ cd UploadToCounty
$ python UploadToPostgresCountiesZips.py
```

### Ensure that node version is loaded and consistent with the .nvmrc file
```sh
$ cd frontend
$ nvm use
```

### Install JS dependencies (make sure npm is installed)
```sh
$ cd frontend
$ yarn install
```

## Running The App (make sure venv_script env is active on all the below terminals)

### Run Django server (terminal 1)
```sh
$ cd webserver
$ python manage.py runserver --settings=app.settings.base
```

### Run Redis in another tab (terminal 2)
```sh
$ cd webserver
$ redis-server
```

### Run celery in another tab (terminal 3)
```sh
$ cd webserver
$ celery -A app worker --loglevel=INFO
```

### Run flower in another tab (terminal 4)
```sh
$ cd webserver
$ flower -A app --port=5555
```

### Start JS server (terminal 5)
```sh
$ cd frontend
$ yarn start
```

#### Note: Make sure your aws credentials are configured in your local machine
#### Note: If you run into errors when getting started, attempting to install dependencies individually might lead to breakage due to inconsistencies in versioning. Your best option would be to remove conda env and recreate it with the existing environment.yml file. Further make sure the node version being used matches with the .nvmrc file.
