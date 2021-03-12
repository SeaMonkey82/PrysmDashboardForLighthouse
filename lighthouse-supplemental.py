from prometheus_client import start_http_server, Gauge
import time
from requests import get
import requests
import json
import psutil

NETWORK = 'pyrmont'             		# 'pyrmont' or 'mainnet' MUST BE SPECIFIED WITH --network WHEN LAUNCHING LIGHTHOUSE
VALIDATOR_TRIGGER = 'vc'			# 'validator', 'vc', or 'v'
BEACON_TRIGGER = 'bn'				# 'beacon', 'bn', or 'b'
VALIDATOR_INDICES = [101,102,103]    	        # REPLACE THIS WITH YOUR VALIDATOR INDICES
URL_PREFIX = "http://127.0.0.1:5052/eth/v1/beacon/states/head/validators/"
UPDATE_INTERVAL = 15
SUPPLEMENTAL_METRICS_PORT = 9010 		# Prometheus metrics port for this process

balance_gauge = Gauge('validator_balance', 'Validator balance, in ETH', ['index'])
validator_statuses = Gauge('validator_statuses', 'validator statuses: 0 UNKNOWN, 1 DEPOSITED, 2 PENDING, 3 ACTIVE, 4 EXITING, 5 SLASHING, 6 EXITED', ['index'])
process_start_time = Gauge('process_start_time', 'Process start time', ['process'])
cpu_usage = Gauge('cpu_usage', 'CPU usage rate', ['process'])
validators_total_balance = Gauge('validators_total_balance', 'The total balance of validators, in ETH', ['state'])

start_http_server(SUPPLEMENTAL_METRICS_PORT)

def findValidatorProcess():
	ValidatorProcessObjects = []
	for proc in psutil.process_iter():
		try:
			pinfo = proc.as_dict(attrs=['pid', 'cmdline', 'create_time'])
			if "lighthouse" in pinfo['cmdline'] and NETWORK in pinfo['cmdline'] and VALIDATOR_TRIGGER in pinfo['cmdline'] :
				ValidatorProcessObjects.append(pinfo)
		except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) :
			pass
	return ValidatorProcessObjects;

def findBeaconProcess():
	BeaconProcessObjects = []
	for proc in psutil.process_iter():
		try:
			pinfo = proc.as_dict(attrs=['pid', 'cmdline', 'create_time'])
			if "lighthouse" in pinfo['cmdline'] and NETWORK in pinfo['cmdline'] and BEACON_TRIGGER in pinfo['cmdline'] :
				BeaconProcessObjects.append(pinfo)
		except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) :
			pass
	return BeaconProcessObjects;

while (True):
	for validator_index in VALIDATOR_INDICES:
		balance = get(URL_PREFIX+str(validator_index)).json()["data"]["balance"]
		balance_gauge.labels(index=validator_index).set(float(balance)/10**9)
		status = get(URL_PREFIX+str(validator_index)).json()["data"]["status"]
		if status == "waiting_in_queue":
			validator_statuses.labels(index=validator_index).set(1)
		elif status == "standby_for_active":
			validator_statuses.labels(index=validator_index).set(2)
		elif status == "waiting_for_finality":
			validator_statuses.labels(index=validator_index).set(2)
		elif status == "active_ongoing":
			validator_statuses.labels(index=validator_index).set(3)
		elif status == "active_awaiting_voluntary_exit":
			validator_statuses.labels(index=validator_index).set(4)
		elif status == "active_awaiting_slashed_exit":
			validator_statuses.labels(index=validator_index).set(5)
		elif status == "exited_voluntarily":
			validator_statuses.labels(index=validator_index).set(6)
		elif status == "exited_slashed":
			validator_statuses.labels(index=validator_index).set(6)
		elif status == "withdrawable":
			validator_statuses.labels(index=validator_index).set(6)
		elif status == "withdrawn":
			validator_statuses.labels(index=validator_index).set(6)
		else:
			validator_statuses.labels(index=validator_index).set(0)

	ValidatorProcess = findValidatorProcess()
	for elem in ValidatorProcess:
		processCreationTime = elem['create_time']
		process_start_time.labels(process='validator').set(processCreationTime)
		validatorPid = elem['pid']
		p = psutil.Process(validatorPid)
		validator_usage = p.cpu_percent(interval=1)
		validator_usage = p.cpu_percent(interval=1) / psutil.cpu_count()
		cpu_usage.labels(process='validator').set(validator_usage)

	BeaconProcess = findBeaconProcess()
	for elem in BeaconProcess:
		processCreationTime = elem['create_time']
		process_start_time.labels(process='beacon').set(processCreationTime)
		beaconPid = elem['pid']
		p = psutil.Process(beaconPid)
		beacon_usage = p.cpu_percent(interval=1)
		beacon_usage = p.cpu_percent(interval=1) / psutil.cpu_count()
		cpu_usage.labels(process='beacon').set(beacon_usage)

	r = requests.get(URL_PREFIX)
	vals = r.json()['data']

	waiting_for_eligibility = (sum([int(x['balance']) for x in vals if x['status'] == 'waiting_for_eligibility']))/(10**9)
	waiting_in_queue = (sum([int(x['balance']) for x in vals if x['status'] == 'waiting_in_queue']))/(10**9)
	waiting_for_finality = (sum([int(x['balance']) for x in vals if x['status'] == 'waiting_for_finality']))/(10**9)
	standby_for_active = (sum([int(x['balance']) for x in vals if x['status'] == 'standby_for_active']))/(10**9)
	total_pending = waiting_for_eligibility + waiting_in_queue + waiting_for_finality + standby_for_active
	validators_total_balance.labels(state='Pending').set(total_pending)

	active = (sum([int(x['balance']) for x in vals if x['status'] == 'active_ongoing']))/(10**9)
	validators_total_balance.labels(state='Active').set(active)

	active_awaiting_voluntary_exit = (sum([int(x['balance']) for x in vals if x['status'] == 'active_awaiting_voluntary_exit']))/(10**9)
	validators_total_balance.labels(state='Exiting').set(active_awaiting_voluntary_exit)

	time.sleep(UPDATE_INTERVAL)
