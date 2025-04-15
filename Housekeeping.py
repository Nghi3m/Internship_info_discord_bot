import json
import os
from typing import List, Dict
import requests


class Housekeeping:
    _FIELDS_TO_KEEP = ['fullname', 'shortname', '_id']
    _FILE_NAME = 'companies.json'
    _TIMEOUT = 10
    _last_queried_companies: List[Dict[str, str]] = []
    _current_queried_companies: List[Dict[str, str]] = []
    _ENDPOINT = ''
    def __init__(self, endpoint):
        self._ENDPOINT = endpoint
        self._read_from_disk_to_last()
    def _read_from_disk_to_last(self):
        # get list of companies from last saved
        if os.path.exists(self._FILE_NAME):
            with open(self._FILE_NAME, 'rt') as f:
                self._last_queried_companies = json.load(f)
    def _save_last_to_disk(self):
        # save companies to disk in case of abrupt bot shutting down
        with open(self._FILE_NAME, 'w') as f:
            json.dump(self._last_queried_companies, f, indent=4)
    def _pull_from_endpoint(self):
        # pull from endpoint and filter out all fields except the useful ones
        response = requests.get(self._ENDPOINT, timeout=10)
        items = response.json()['items']
        self._current_queried_companies = \
            [{key: company[key] for key in company
                if key in self._FIELDS_TO_KEEP}
            for company in items]
    def _mark_current_outdated(self):
        # mark current list of companies outdated
        self._last_queried_companies = self._current_queried_companies
        self._current_queried_companies = []
    def _get_added_company_names(self):
        # filter out companies that are on outdated list by their id and return their names
        last_ids: List[str] = [company['_id'] for company in self._last_queried_companies]
        added_company_names = [company['shortname'] for company in self._current_queried_companies
                            if not company['_id'] in last_ids]
        return added_company_names
    async def send_message_if_added(self, send_message, is_sending_while_none_added = False):
        # send the added companies if they exist with the provided method for sending message
        try:
            self._pull_from_endpoint()
            company_names = self._get_added_company_names()
            self._mark_current_outdated()
            self._save_last_to_disk()
            if company_names:
                name_on_each_line = ""
                for name in company_names:
                    name_on_each_line += f'{name}\n'
                await send_message(f"@everyone\n✅ Added:\n{name_on_each_line}")
            elif is_sending_while_none_added:
                await send_message(f"@everyone\nNone added")

        # error handling
        except requests.exceptions.HTTPError as errh:
            await send_message(f"@everyone\n❌ HTTP Error:\n{errh}")
        except requests.exceptions.ConnectionError as errc:
            await send_message(
                f"@everyone\n❌ Connection Error (maybe the server is down):\n{errc}")
        except requests.exceptions.Timeout as errt:
            await send_message(f"@everyone\n❌ Timeout Error:\n{errt}")
        except requests.exceptions.RequestException as err:
            await send_message(f"@everyone\n❌ General Error:\n{err}")

