# Scatter Plot Location of New Affordable Housing Developments

This project explores the current housing climate in within the Travis County area. The program will scatter-plott a map of housing based on user-inputted parameters. Housing data
was pulled from Austin’s Open Data Portal.

# Cloning from GitHub

---

First, `cd` into the desired location to clone the repository.

Second, clone and update the repo with the address below onto the local ISP.
```gitexclude
git clone https://github.com/vulong2505/COE-332.git
```
Navigate to the `/final` folder for the relevant scripts.

# Deploying the k8s

---

Perform the following command to deploy the k8s cluster.

```
# cd into the /kubernetes/prod
kubectl apply -f final-prod-api-deployment.yml
kubectl apply -f final-prod-api-service.yml
kubectl apply -f final-prod-db-deployment.yml
kubectl apply -f final-prod-db-pvc.yml
kubectl apply -f final-prod-db-service.yml
kubectl apply -f final-prod-wrk-deployment.yml
```

The `REDIS_IP` in `vulong25-final-prod-api-deployment` and  `vulong25-final-prod-api-deployment` must match the pod IP of the 
redis deployment `vulong25-prod-db-deployment`.


You can find the pod IP of the redis deployment using
```
kubectl get pods -o wide
```


# Documentation

---


## Database Operations


**/data/load**
* Loads the .json onto the redis database
```python
curl localhost:5035/data/load
```


**/data/reset_jobs**
* Clears the jobs database
```python
curl localhost:5035/data/reset_jobs
```


## Job Operations


**/run**
* Creates POST for a job based on a parameter, start, and end
```python
curl -X POST -d '{"parameter": "Zip Code", "start": 78000, "end": 79000}' localhost:5035/run
```


**/jobs**
* Lists all performed jobs and relevant information
```python
curl localhost:5035/jobs
```


**/download/jid**
* Downloads image for a performed job using the relevant jid
```python
curl localhost:5035/download/<jid>
```


## CRUD Operations


**/data/add_house**
* Creates and adds a new entry to the database
```python
curl localhost:5035/data/add_house -X POST -H "Content-Type: application/json" -d '{"Address": "5812 Berkman Dr","Zip Code": "78723", "Unit Type": "", "Tenure": "", "City Amount": "46000", "Longitude": "-97.69232", "Latitude": "30.292107", "Property Manager Phone Number": "", "Property Manager Email": ""}'
```


**/data/get/Project_ID**
* Reads an assigned project ID for a house and prints out its property data
```python
curl localhost:5035/data/get/<Project_ID>
```


**/data/update**
* Updates an existing property based on project id, a parameter, and the desired change
```python
curl -X POST -d '{"id": "5805", "parameter": "Zip Code", "edit": "77777"}' localhost:5035/data/update
```


**/data/delete/Project_ID**
* Deletes a property from the database
```python
curl localhost:5035/data/delete/<Project_ID>
```


# Running the CRUD API

It is necessary to first load the json into the redis database using the following command:
```python
curl localhost:5035/data/load
```
This allows the workers to actually perform a job on a dataset.

All other operations may be performed asynchronously.


# Downloading an Image

Once a worker has completed a job on a k8s cluster, perform a `kublect cp` command to save the image
to a local computer.
```python
kubectl cp <debug_pod>:output.png output.png
```