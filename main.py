import os
import datetime
import json
import sys
import requests
import todoist
import pprint

pp = pprint.PrettyPrinter(indent=4, depth=6)

config = []
with open(os.path.join(sys.path[0], 'config.json')) as configFile:
    config = json.load(configFile)


def main():
    fields = ['USER', 'PASSWORD', 'JIRA', 'JQL', 'TODOIST', 'ISSUELINK', 'PROJECT_OPTIONS']
    for field in fields:
        if (field not in config):
            print "Config File is missing:", field
            exit()

    todoapi = todoist.TodoistAPI(config['TODOIST'])

    tasks = todoapi.state['items']
    projects = todoapi.state['projects']
    labels = todoapi.state['labels']

    taskList = {}
    for task in tasks:
        task = task.__dict__
        task = task['data']

        if (activeCheck(task)):
            taskList[task['content']] = task

    projectList = {}
    for project in projects:
        project = project.__dict__
        project = project['data']

        if (activeCheck(project)):
            projectList[project['name']] = project

    labelList = {}
    for label in labels:
        label = label.__dict__
        label = label['data']

        if (activeCheck(label)):
            labelList[label['name']] = label

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

        if ('Jira-Issue' not in labelList):
            label = todoapi.labels.add('Jira-Issue')
            todoapi.commit()
            labelList['Jira-Issue'] = label

        configureInInbox = raw_input("Send (" + str(data['total']) +
                ") tasks to Inbox? (yes|no)\n")

        for issue in data['issues']:
            title = '[**' + issue['key'] + '**](' + config['ISSUELINK'] + issue['key']
            title +=  ') ' + issue['fields']['summary']

            if (title in taskList):
                deleteTask = raw_input("Task (" + str(data['total']) +
                        ") already exists, would you like to delete it? (yes|no)\n")

                if (deleteTask == 'yes'):
                    print "Deleting: " + title + "\n"
                    item = todoapi.items.get_by_id(taskList[title]['id'])
                    item.close()
                    todoapi.commit()

                    item.delete()
                    todoapi.commit()
                    del taskList[title]
                else:
                    print "Skipping: " + title + "\n"

            if (title not in taskList):
                print 'adding task: ', title

                projectID = 0
                dueDate = ''

                if (configureInInbox == 'no'):
                    if ('PROJECT_OPTIONS' in config):
                        project = raw_input("Choose project: " +
                                config['PROJECT_OPTIONS'] + "\n")

                        if (project in projectList):
                            projectID = projectList[project]['id']

                    dueDate = raw_input("Choose a due date (ex. every day)\n")

                item = todoapi.items.add(content=title, project_id=projectID,
                        labels=[labelList['Jira-Issue']['id']], date_string=dueDate)

                todoapi.commit()

                if ('description' in issue['fields'] and issue['fields']['description']):
                    note = todoapi.notes.add(item['id'], issue['fields']['description'])
                    todoapi.commit()

def makeRequest(headers, params, options):
    if ('auth' in options):
        response = requests.get(options['url'], headers=headers, params=params,
                auth=(options['auth']['user'], options['auth']['password']))
    else:
        response = requests.get(options['url'], headers=headers, params=params)

    return response.json()

def activeCheck(item):
    active = True

    if ('is_archived' in item and item['is_archived'] == 1):
        active = False

    if ('is_deleted' in item and item['is_deleted'] == 1):
        active = False

    if ('in_history' in item and item['in_history'] == 1):
        active = False

    return active

main()

