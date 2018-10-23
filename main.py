import os
import datetime
import json
import sys
import requests
import todoist
import pprint

pp = pprint.PrettyPrinter(indent=4)

config = []
with open(os.path.join(sys.path[0], 'config.json')) as configFile:
    config = json.load(configFile)


def main():
    for field in ['USER', 'PASSWORD', 'JIRA', 'JQL', 'TODOIST', 'ISSUELINK']:
        if (field not in config):
            print "Config File is missing:", field
            exit()

    headers = {
        'Content-Type': 'application/json',
    }

    params = (
        ('jql', config['JQL'] ),
    )

    response = requests.get(config['JIRA'],
            headers=headers, params=params, auth=(config['USER'], config['PASSWORD']))

    data = response.json()

    if (data):
        todoapi = todoist.TodoistAPI(config['TODOIST'])

        for issue in data['issues']:
            title = '[**' + issue['key'] + '**](' + config['ISSUELINK'] + issue['key']
            title +=  ') ' + issue['fields']['summary']
            print 'adding: ', title

            item = todoapi.items.add(title, 0)
            todoapi.commit()

            note = todoapi.notes.add(item['id'], issue['fields']['description'])
            todoapi.commit()

main()

