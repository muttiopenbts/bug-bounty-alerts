# -*- coding: utf-8 -*-
"""Submits PagerDuty incident based on HackerOne reports.

This script queries HackerOne account for reports of a certain type, like,
critical, and triaged, and then searches you Pager Duty service to see if the
given h1 report url already has an alert submitted, if not, the alert is 
triggered to PD.

When run, the script will loop indefinetely checking for new h1 reports at a set interval.
"""
import requests
import os
from decouple import config
import datetime
from pytz import timezone
import json
import http.client
from apscheduler.schedulers.background import BackgroundScheduler
import time
import socket
from typing import List, Set, Dict, Tuple, Optional


# Configuration settings
settings = {
    'h1_api_token': config('H1_API_KEY'),
    'h1_api_token_name': config('H1_API_KEY_NAME'),
    'h1_severities': ['high','critical'],
    'h1_states': ['triaged'],
    'h1_program_name': [config('H1_PROGRAM_NAME')],
    'pd_api_token': config('PD_TOKEN'),
    'pd_service_id': config('PD_SERVICE_ID'),
}


def get_h1_report(**kwargs: str) -> dict:
    '''https://api.hackerone.com/core-resources/#reports-get-report
    '''
    api_token = kwargs.get('api_token', settings.get('h1_api_token'))
    api_token_name = kwargs.get('h1_api_token_name', settings.get('h1_api_token_name'))

    headers = {
        'Accept': 'application/json'
    }
    report_id = kwargs.get('id', None)

    url_path = f'reports/{report_id}'

    r = requests.get(
        f'https://api.hackerone.com/v1/{url_path}',
        auth=(api_token_name, api_token),
        headers=headers
    )

    result = r.json().get("data", {})

    if result:
        report = result.get("id")
        report += f' {result.get("attributes").get("state")}'
        report += f' {result.get("attributes").get("triaged_at")}'
        report += f' {result.get("relationships").get("severity").get("data").get("attributes").get("rating")}'
        # print(f'{report}')

    return result


def get_h1_reports(**kwargs: str) -> dict:
    '''Obtain a list of hackerone reports that meet criteria.
    Searches from number of days back set by DAYS_BACK to current time.
    https://api.hackerone.com/core-resources/#reports-get-all-reports
    '''
    api_token = kwargs.get('api_token', settings.get('h1_api_token'))
    api_token_name = kwargs.get('h1_api_token_name', settings.get('h1_api_token_name'))
    h1_program_name: List[str] = kwargs.get('h1_program_name', settings.get('h1_program_name'))

    headers = {
        'Accept': 'application/json'
    }
    MONTHS_BACK = kwargs.get('months_back', 1)
    DAYS_BACK = kwargs.get('days_back', 30)
    list_of_states = kwargs.get('states', [])
    list_of_severities = kwargs.get('severities', [])

    # Months back
    date_time = datetime.datetime.now(
        timezone('UTC')) - datetime.timedelta(days=((365)/12)*MONTHS_BACK)
    # Days back
    date_time = datetime.datetime.now() - datetime.timedelta(days=DAYS_BACK)
    date_time_from = date_time.strftime("%Y-%m-%d")

    params = {
        'filter[program][]': h1_program_name,
        'filter[state][]': list_of_states,
        'filter[severity][]': list_of_severities,
        'filter[triaged_at__gt]': [date_time_from],
    }

    r = requests.get(
        'https://api.hackerone.com/v1/reports',
        auth=(api_token_name, api_token),
        params=params,
        headers=headers
    )

    print(f'Search back from: {date_time_from}')

    if r.json().get('errors'):
        raise Exception(f'Error: {r.json()}')

    result = r.json().get("data", {})

    print(f'Found {len(result)} matching reports.')

    return result


def set_pd_incident(**kwargs: str) -> dict:
    api_token = kwargs.get('pd_api_token', settings.get('pd_api_token'))
    # Test service
    service_id = kwargs.get('service_id', settings.get('pd_service_id'))
    conn = http.client.HTTPSConnection("api.pagerduty.com")
    incident_key = kwargs.get('incident_key')
    title = kwargs.get('title')

    details = kwargs.get('details', 'MISSING DETAILS')

    payload = {
        "incident": {
            "type": "incident",  # *
            "title": title,  # *
            "service": {
                "id": service_id,
                "summary": "INCIDENT",
                "type": "service_reference",
            },
            "urgency": "high",
            "body": {
                "type": "incident_body",
                "details": details
            },
        }
    }

    if incident_key:
        payload['incident']['incident_key'] = incident_key

    payload = json.dumps(payload)

    headers = {
        'accept': "application/vnd.pagerduty+json;version=2",
        'content-type': "application/json",
        'from': f"Host: {socket.getfqdn()}",
        'authorization': f"Token token={api_token}"
    }

    conn.request("POST", "/incidents", str(payload), headers)

    res = conn.getresponse()
    data = json.loads(res.read())

    if data.get('error'):
        raise Exception(f'Error: {data}')

    return data


def get_pd_incident(**kwargs: str) -> dict:
    api_token = kwargs.get('pd_api_token', settings.get('pd_api_token'))
    id = kwargs.get('id', None)

    if not id:
        raise Exception('Must specify PD incident id')

    conn = http.client.HTTPSConnection("api.pagerduty.com")

    headers = {
        'accept': "application/vnd.pagerduty+json;version=2",
        'content-type': "application/json",
        'authorization': f"Token token={api_token}"
    }

    conn.request("GET", f"/incidents/{id}", headers=headers)

    res = conn.getresponse()
    data = json.loads(res.read())

    return data


def list_pd_incidents(**kwargs: str) -> dict:
    '''https://developer.pagerduty.com/api-reference/reference/REST/openapiv3.json/paths/~1incidents/get
    '''
    api_token = kwargs.get('pd_api_token', settings.get('pd_api_token'))
    incident_key = kwargs.get('incident_key', None)

    # Comma seperated list of ids
    service_ids: str = kwargs.get('service_ids', None)

    conn = http.client.HTTPSConnection("api.pagerduty.com")

    headers = {
        'accept': "application/vnd.pagerduty+json;version=2",
        'content-type': "application/json",
        'authorization': f"Token token={api_token}"
    }

    url_path = f'{"/incidents?total=false&time_zone=UTC"}'

    if incident_key:
        url_path += f'&incident_key={incident_key}'

    if service_ids:
        url_path += f'&service_ids[]={service_ids}'

    conn.request("GET", url_path, headers=headers)

    res = conn.getresponse()
    data = json.loads(res.read())

    return data


def get_pd_service(**kwargs: str) -> dict:
    api_token: str = kwargs.get('pd_api_token', settings.get('pd_api_token'))
    service_id: str = kwargs.get('service_id', settings.get('pd_service_id'))

    if not service_id:
        raise Exception('Must specify PD service_id')

    headers = {
        'accept': "application/vnd.pagerduty+json;version=2",
        'content-type': "application/json",
        'authorization': f"Token token={api_token}"
    }

    conn = http.client.HTTPSConnection("api.pagerduty.com")
    conn.request("GET", f"/services/{service_id}", headers=headers)

    res = conn.getresponse()
    data = json.loads(res.read())

    return data


def do_alerts():
    # Search for h1 reports that are severity high or above and in triaged state
    found_reports = get_h1_reports(
        severities=settings.get('h1_severities'),
        states=settings.get('h1_states'),
    )

    for report in found_reports:
        # Check if h1 report already has pagerduty alert
        h1_report = get_h1_report(id=report.get("id"))
        h1_id = h1_report.get('id')

        # Generate a unique key for each new pd incident. Uniqueness is not enforced in pd.
        # This sudo key will be used in subsequent searches to prevent duplicate pd incidences.
        pd_incident_key = f'https://hackerone.com/reports/{h1_id}'
        # print(pd_incident_key)

        # Search for matching pd incident based on key generated from h1 report url
        list_of_incidents = list_pd_incidents(
            incident_key=pd_incident_key,
            service_ids=settings.get('pd_service_id', None)
        ).get('incidents', {})

        if list_of_incidents:
            print(
                f'Found {len(list_of_incidents)} existing incidents matching {pd_incident_key}.')
            for incident in list_of_incidents:
                print(f'PD ID: {incident.get("id")}')
                print(f'Status: {incident.get("status")}')
        else:
            # If no matching incidences found. Trigger an alert.
            details = f'Creating new alart for {pd_incident_key}'
            details += f'\nState: {h1_report.get("attributes").get("state")}'
            details += f'\nTitle: {h1_report.get("attributes").get("title")}'
            details += f'\nSeverity: {h1_report.get("relationships").get("severity").get("data").get("attributes").get("rating")}'
            print(details)

            set_pd_incident(
                incident_key = pd_incident_key,
                details = details,
                title = f'HackerOne alart generated by {socket.gethostname()}',
            )


def main():
    '''This function will loop forever (block) while looking
    for h1 reports to pager duty alert on.
    '''
    # creating the BackgroundScheduler object
    scheduler = BackgroundScheduler()
    # setting the scheduled task
    scheduler.add_job(do_alerts, 'interval', minutes=1)
    # starting the scheduled task using the scheduler object
    scheduler.start()

    try:
        # To simulate application activity (which keeps the main thread alive).
        while True:
            time.sleep(1)

    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary but recommended
        scheduler.shutdown()
    except Exception:
        scheduler.shutdown()

if __name__ == '__main__':
    main()
