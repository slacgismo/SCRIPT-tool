import numpy as np
from s3fs.core import S3FileSystem
import json

# Loads and displays pre-calculated load profiles for the given control rate and county. 

def getScaData(item_name, bucket_name="script.control.tool"):
    ''' gets and cleans the sca data when there is no user data input '''
    s3 = S3FileSystem()
    df = np.load(s3.open("{}/{}".format(bucket_name, item_name)))
    sca_load = (0.25*np.arange(0, 96), df[0, :]) # sample first profile for examples

    data_final = []
    for x in range(len(sca_load[0])):
        row = {"load": str(sca_load[1][x]), "time": str(sca_load[0][x])}
        data_final.append(row)

    return data_final
