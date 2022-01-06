import json
import jobs
import datetime
import redis

from flask import Flask, request, send_file
from jobs import q, rd_jobs, rd_raw, rd_images

app = Flask(__name__)


@app.route('/', methods=['GET'])
def help():
    return """
    blah blah blah
    put stuff here
    
    Hello world! \n
    """


# Database Operations ==================================================================================================

@app.route('/data', methods=['GET'])
def get_data():
    data = json.loads(rd_raw.get('Housing Data'))
    return data


def delete_database():
    rd_raw.flushall()


@app.route('/data/load', methods=['GET'])
def load_data():
    delete_database()  # Deletes all data on the redis db to start on clean slate.

    with open("Austin_Affordable_Housing.json", "r") as f:
        housing_data = json.load(f)

    rd_raw.set('Housing Data', json.dumps(housing_data, indent=2))

    return "Housing data has been loaded. \n"


@app.route('/data/reset_jobs', methods=['GET'])
def delete_jobs_database():
    rd_jobs.flushall()

    return "Jobs database has been cleared. \n"


# Job Operations =======================================================================================================

# Run a new job based on parameters such as City Amount from $20000 to $150000
# curl -X POST -d '{"parameter": "Zip Code", "start": 78000, "end": 79000}' localhost:5035/run
# curl -X POST -d '{"parameter": "Zip Code", "start": 78000, "end": 79000}' <api_ip>:5000/run
@app.route('/run', methods=['GET', 'POST'])
def run_job():
    if request.method == 'POST':
        try:
            job = request.get_json(force=True)
        except Exception as e:
            return True, json.dumps({'status': "Error", 'message': 'Invalid JSON: {}.'.format(e)})

        return json.dumps(jobs.add_job(str(datetime.datetime.now()), job['parameter'], job['start'], job['end'])) + "\n"

    else:
        return """
    This is a route for POSTing a job to graph a scatterplot of houses by specifying a start/end range for a certain parameter.
    Parameters include: "Zip Code" and "City Amount"
        
    For example, the json arguments may look like this:
                {"parameter": "Zip Code", "start": 78xxx, "end": 78xxx}
                {"parameter": "City Amount", "start": 20000, "end": 150000}
        
    To curl, use the form:
                curl -X POST -d '{"parameter": <parameter>, "start": <start>, "end": <end>}' localhost:5035/run \n
    """


# List past jobs and its status
@app.route('/jobs', methods=['GET'])
def get_jobs():
    redis_dict = {}

    for key in rd_jobs.keys():
        redis_dict[str(key.decode('utf-8'))] = {}
        redis_dict[str(key.decode('utf-8'))]['id'] = rd_jobs.hget(key, 'id').decode('utf-8')
        redis_dict[str(key.decode('utf-8'))]['status'] = rd_jobs.hget(key, 'status').decode('utf-8')
        redis_dict[str(key.decode('utf-8'))]['datetime'] = rd_jobs.hget(key, 'datetime').decode('utf-8')

    return json.dumps(redis_dict, indent=4)


# Download an image from a job
@app.route('/download/<jid>', methods=['GET'])
def download(jid):
    path = f'/app/{jid}.png'

    with open(path, 'wb') as f:
        f.write(rd_images.hget(jid, 'image'))

    return send_file(path, mimetype='image/png', as_attachment=True)


# CRUD Operations ======================================================================================================

# CREATE - Add a new property
# curl localhost:5035/data/add_house -X POST -H "Content-Type: application/json" -d '{"Address": "5812 Berkman Dr","Zip Code": "78723", "Unit Type": "", "Tenure": "", "City Amount": "46000", "Longitude": "-97.69232", "Latitude": "30.292107", "Property Manager Phone Number": "", "Property Manager Email": ""}'
@app.route('/data/add_house', methods=['POST'])
def add_house():
    housing_data = get_data()

    new_house = request.get_json(force=True)
    new_project_id = str(project_id_count())
    new_address = new_house['Address']
    new_zip = new_house['Zip Code']
    new_unit_type = new_house['Unit Type']
    new_tenure = new_house['Tenure']
    new_city_amount = new_house['City Amount']
    new_longitude = new_house['Longitude']
    new_latitude = new_house['Latitude']
    new_manager_number = new_house['Property Manager Phone Number']
    new_manager_email = new_house['Property Manager Email']

    housing_data.append({"Project ID": new_project_id, "Address": new_address, "Zip Code": new_zip,
                         "Unit Type": new_unit_type, "Tenure": new_tenure,
                         "City Amount": new_city_amount, \
                         "Longitude": new_longitude, "Latitude": new_latitude, \
                         "Property Manager Phone Number": new_manager_number, \
                         "Property Manager Email": new_manager_email})

    rd_raw.set('Housing Data', json.dumps(housing_data, indent=2))

    return "New property has been added. \n"


count = 0


# Jank hardcode w/ global var to keep the original .csv project ID format
def project_id_count():
    global count
    count += 1
    return 5805 + count


# READ - Print out property data of specific house using project ID
@app.route('/data/get/<Project_ID>', methods=['GET'])
def get_house(Project_ID):
    housing_data = get_data()

    selected_house = [x for x in housing_data if x['Project ID'] == Project_ID]

    if len(selected_house) == 0:
        return "House #" + Project_ID + " does not exist. \n"

    return json.dumps([x for x in housing_data if x['Project ID'] == Project_ID]) + "\n"


# UPDATE: Update house info
# curl -X POST -d '{"id": "5805", "parameter": "Zip Code", "edit": "77777"}' localhost:5035/data/update
# curl -X POST -d '{"id": "5805", "parameter": "City Amount", "edit": "120030"}' localhost:5035/data/update
@app.route('/data/update', methods=['POST'])
def update_house():
    housing_data = get_data()

    update_request = request.get_json(force=True)

    project_id = update_request["id"]
    parameter = update_request["parameter"]
    edit = update_request["edit"]

    selected_house = [x for x in housing_data if x['Project ID'] == project_id]

    if len(selected_house) == 0:
        return "House #" + project_id + " does not exist. \n"

    index = housing_data.index(selected_house[0])

    housing_data[index][parameter] = edit

    delete_database()  # not a really pretty way of doing this
    rd_raw.set('Housing Data', json.dumps(housing_data, indent=2))

    return "Property " + project_id + " has been updated. \n"


# DELETE - Delete house info
@app.route('/data/delete/<Project_ID>', methods=['GET', 'DELETE'])
def delete_house(Project_ID):
    housing_data = get_data()

    selected_house = [x for x in housing_data if x['Project ID'] == Project_ID]

    if len(selected_house) == 0:
        return "House #" + Project_ID + " does not exist. \n"

    housing_data.remove(selected_house[0])

    delete_database()  # not a really pretty way of doing this
    rd_raw.set('Housing Data', json.dumps(housing_data, indent=2))

    return "Property has been deleted. \n"


# Main =================================================================================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
