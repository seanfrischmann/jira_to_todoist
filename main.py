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

    activeTasks = makeRequest({"Authorization": "Bearer %s" % config['TODOIST']},
            {}, {"url": "https://beta.todoist.com/API/v8/tasks"})

    taskList = {}
    for task in activeTasks:
        taskList[task['content']] = task

    headers = {
        'Content-Type': 'application/json',
    }

    params = (
        ('jql', config['JQL'] ),
    )

    options = {'url': config['JIRA'], 'auth': { 'user': config['USER'],
        'password': config['PASSWORD']}}

    data = makeRequest(headers, params, options)

    if (data):
        todoapi = todoist.TodoistAPI(config['TODOIST'])

        for issue in data['issues']:
            title = '[**' + issue['key'] + '**](' + config['ISSUELINK'] + issue['key']
            title +=  ') ' + issue['fields']['summary']

            if (title not in taskList):
                print 'adding task: ', title
                item = todoapi.items.add(title, 0)
                todoapi.commit()

                note = todoapi.notes.add(item['id'], issue['fields']['description'])
                todoapi.commit()

def makeRequest(headers, params, options):
    if ('auth' in options):
        response = requests.get(options['url'], headers=headers, params=params,
                auth=(options['auth']['user'], options['auth']['password']))
    else:
        response = requests.get(options['url'], headers=headers, params=params)

    return response.json()

main()

