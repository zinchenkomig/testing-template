import json

from client import GrafanaClient
import subprocess


def run_cmd(command: str) -> str:
    return subprocess.run(command,
                          shell=True, capture_output=True).stdout.decode('utf-8')


def get_postgres_password() -> str:
    return run_cmd('kubectl get secret '
                   'postgres_svc '
                   '-o jsonpath="{.data.password}" | base64 -d')


def get_osearch_password() -> str:
    return run_cmd('kubectl get secret '
                   'opensearch-cluster-master '
                   '-o jsonpath="{.data.opensearch-password}" | base64 -d')


def get_grafana_password():
    return run_cmd('kubectl get secret '
                   'grafana '
                   '-o jsonpath="{.data.admin-password}" | base64 -d')


def get_grafana_auth() -> dict:
    passwd = get_grafana_password()
    return {
        'user': 'admin',
        'password': passwd
    }


if __name__ == '__main__':
    grafana = GrafanaClient(base_url='grafana.mikhailzinchenko.test',
                            **get_grafana_auth())
    pg_pass = get_postgres_password()
    with open('pg_datasource.json', 'r') as fp:
        pg_ds = json.load(fp)
    pg_uid = grafana.add_datasource(pg_ds, password=pg_pass)

    osearch_pass = get_osearch_password()
    with open('elastic_datasource.json', 'r') as fp:
        elastic_ds = json.load(fp)
    elastic_uid = grafana.add_datasource(elastic_ds, password=osearch_pass)

    with open('prometheus_sources.json', 'r') as fp:
        prometheus_ds = json.load(fp)
    prometheus_uid = grafana.add_datasource(prometheus_ds)

    uid_map = {
        'prometheus': prometheus_uid,
        'postgres': pg_uid,
        'elasticsearch': elastic_uid,
    }

    with open('dashboards.json', 'r') as fp:
        dash_data = json.load(fp)

    for i in range(len(dash_data['panels'])):
        ds = dash_data['panels'][i]['datasource']
        uid = uid_map[ds['type']]
        dash_data['panels'][i]['datasource']['uid'] = uid
        for j in range(len(dash_data['panels'][i]['targets'])):
            ds_target = dash_data['panels'][i]['targets'][j]['datasource']
            target_uid = uid_map[ds_target['type']]
            dash_data['panels'][i]['targets'][j]['datasource']['uid'] = target_uid

    grafana.add_dashboard(dash_data)
