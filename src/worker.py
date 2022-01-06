import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json

import jobs
from jobs import q, rd_jobs, rd_raw, rd_images, update_job_status


@q.worker()
def execute_job(jid):

    update_job_status(jid, "In progress...")

    # Get job data
    job = 'job.{}'.format(jid)
    parameter = str(rd_jobs.hget(job,'parameter').decode('utf-8'))
    start = float(rd_jobs.hget(job,'start').decode('utf-8'))
    end = float(rd_jobs.hget(job,'end').decode('utf-8'))

    # Get data out of rd_raw redis database
    housing_data = json.loads(rd_raw.get('Housing Data').decode('utf-8'))

    # Grab it straight out of /app/
    # housing_data = []
    #
    # with open("/app/Austin_Affordable_Housing.json", "r") as f:
    #     housing_data = json.load(f)

    # Create panda dataframe out of json data
    df_json = pd.DataFrame(housing_data)

    df_json['Longitude'] = pd.to_numeric(df_json['Longitude'])
    df_json['Latitude'] = pd.to_numeric(df_json['Latitude'])
    df_json['Zip Code'] = pd.to_numeric(df_json['Zip Code'])
    df_json['City Amount'] = pd.to_numeric(df_json['City Amount'])

    # Parse by parameter based on start and end
    q_valid_range = df_json[parameter] > start
    valid_df = df_json[q_valid_range]
    q_valid_range = df_json[parameter] < end
    valid_df = valid_df[q_valid_range]

    # Insert image of Austin map
    im = plt.imread('/app/austin-map.png')
    plt.imshow(im, zorder=0, extent=[-97.9, -97.5, 30.1, 30.5])

    # Plot
    plt.scatter(valid_df.Longitude, valid_df.Latitude, 0.5, 'r')
    plt.xlim(-97.9, -97.5)
    plt.ylim(30.1, 30.5)
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("Affordable Housing in Austin based on " + parameter)

    # Save image
    plt.savefig("output.png")

    with open('/app/output.png', 'rb') as f:
        img = f.read()
    rd_images.hset(jid, 'image', img)

    plt.close()

    jobs.update_job_status(jid, "Completed")


execute_job()