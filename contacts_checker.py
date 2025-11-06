import datetime
import json
import logging
import os
import threading
import traceback

import requests

import database

logger = logging.getLogger(__name__)


def get_target_access_token(sfmc_subdomain, client_id, client_secret):
    url = f"https://{sfmc_subdomain}.auth.marketingcloudapis.com/v2/token"
    payload = {"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret}
    res = requests.post(url, json=payload)
    res.raise_for_status()
    return res.json()["access_token"]


def get_contacts_amount(sfmc_subdomain, de_key, access_token):
    url = f"https://{sfmc_subdomain}.rest.marketingcloudapis.com/data/v1/customobjectdata/key/{de_key}/rowset"
    headers = {"Authorization": f"Bearer {access_token}"}
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    data = res.json()

    row = data["items"][0]
    values = row.get("values", {})
    count_str = list(values.values())[0]
    return int(count_str)


def send_message_to_slack(slack_user_id, message):
    workflow_webhook_url = os.environ.get("WORKFLOW_WEBHOOK_URL")
    if not workflow_webhook_url:
        logger.warning("WORKFLOW_WEBHOOK_URL not set — Slack messages will be skipped.")

    payload = {
        "message": message,
        "slack_user_id": slack_user_id
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(
        workflow_webhook_url,
        headers=headers,
        data=json.dumps(payload)
    )

    if not response.ok:
        logger.warning(
            f"Slack webhook returned {response.status_code}: {response.text}. "
            f"Slack will retry automatically."
        )
    else:
        logger.debug("Slack message delivered successfully.")
    

    
    return response.ok


def update_contract_data(contract_data, contacts_amount):
    contract_data.contacts_amount = contacts_amount
    contract_data.last_checked = datetime.datetime.now()
    contract_data.save()


def check_contract(contract_data):
    try:
        logger.info(f'Starting contract check | {contract_data.name}')
        target_access_token = get_target_access_token(contract_data.sfmc_subdomain,
                                                      contract_data.client_id,
                                                      contract_data.client_secret)
        logger.debug(f'Access token gathered | {contract_data.name}')

        contacts_amount = get_contacts_amount(contract_data.sfmc_subdomain, contract_data.de_key, target_access_token)
        logger.info(
            f'Contacts amount gathered: {contacts_amount}. Limit: {contract_data.contacts_limit} | {contract_data.name}')

        update_contract_data(contract_data, contacts_amount)

        if contacts_amount > contract_data.contacts_limit:
            logger.info(f'Limit reached, sending messages to {contract_data.slack_users_ids} | {contract_data.name}')

            message = f"⚠️ ALARM!\nContacts limit reached in: {contract_data.name}\nContacts Now: {contacts_amount}\nContacts Limit: {contract_data.contacts_limit}"

            for slack_user_id in contract_data.slack_users_ids:
                send_message_to_slack(slack_user_id, message)
                logger.debug(f'Message to {slack_user_id} sent | {contract_data.name}')

    except Exception as e:
        logger.error(f'Error during contract {contract_data.name} check. Details : {e}')
        logger.debug(traceback.format_exc())

        message = f"🤭 Error during target contacts check for {contract_data.name}. Details:\n{e}"
        for slack_user_id in contract_data.slack_users_ids:
            send_message_to_slack(slack_user_id, message)
            logger.debug(f'Error Message to {slack_user_id} sent | {contract_data.name}')


def check_all():
    logger.debug('Starting all contracts check')
    for contract_info in database.ContractData.select():
        t = threading.Thread(target=check_contract, args=(contract_info,), daemon=True)
        t.start()
