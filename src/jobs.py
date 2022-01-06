import os
import uuid
import redis
import datetime

from hotqueue import HotQueue


# Pass IP as an environment variable
redis_ip = os.environ.get('REDIS_IP')
if not redis_ip:
    raise Exception()

q = HotQueue("queue", host=redis_ip, port=6379, db=1)  # Jobs q
rd_jobs = redis.StrictRedis(host=redis_ip, port=6379, db=2)  # Jobs db
rd_raw = redis.StrictRedis(host=redis_ip, port=6379, db=3) # Raw data db
rd_images = redis.StrictRedis(host=redis_ip, port=6379, db=4) # Images db


def _generate_jid():
    return str(uuid.uuid4())


def _generate_job_key(jid):
    return 'job.{}'.format(jid)


def _instantiate_job(jid, status, time, parameter, start, end):
    """Returns a dict about the job."""
    if type(jid) == str:
        return {'id': jid,
                'status': status,
                'datetime': time,
                'parameter': parameter,
                'start': start,
                'end': end
                }
    return {'id': jid.decode('utf-8'),
            'status': status.decode('utf-8'),
            'datetime': time.decode('utf-8'),
            'parameter': parameter.decode('utf-8'),
            'start': start.decode('utf-8'),
            'end': end.decode('utf-8')
            }


def _save_job(job_key, job_dict):
    """Save a job object in the Redis jobs database."""
    rd_jobs.hmset(job_key, job_dict)


def _queue_job(jid):
    """Add a job to the hot queue."""
    q.put(jid)


def add_job(time, parameter, start, end, status="submitted"):
    """Add a job to the redis queue."""
    jid = _generate_jid()
    job_dict = _instantiate_job(jid, status, time, parameter, start, end)
    _save_job(_generate_job_key(jid), job_dict)
    _queue_job(jid)

    return job_dict


def update_job_status(jid, status):
    """Update the status of job with job id `jid` to status `status`."""
    # jid, status, time, parameter, start, end = rd_jobs.hmget(_generate_job_key(jid), 'id', 'status', 'datetime', 'parameter', 'start', 'end')
    # job = _instantiate_job(jid, status, time, parameter, start, end)
    #
    # if job:
    #     job['status'] = status
    #     _save_job(_generate_job_key(jid), job)
    # else:
    #     raise Exception()
    rd_jobs.hset(_generate_job_key(jid), 'status', status)