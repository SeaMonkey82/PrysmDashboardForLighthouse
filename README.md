# PrysmDashboardForLighthouse
Port of the Prysm Validator Dashboard for Lighthouse

<img src=screenshot.png>

Prerequisites:
- Prometheus
- Grafana
- python-pip
- cryptowat-exporter (https://github.com/nbarrientos/cryptowat_exporter)

Instructions:
- Edit `lighthouse-supplemental.py` and assign all of the variables at the top to their appropriate values.
- `pip3 install psutil && pip3 install prometheus_client`
- `python3 lighthouse-supplemental.py`
- Launch Prometheus using the included `prometheus.yml` config or update your existing configuration as necessary
- Import `Prysm Dashboard for Lighthouse.json` into Grafana

Big thanks to Ocaa/Grums for creating the original dashboard and to c-time and suclearnub for helping out with the python and jq.
