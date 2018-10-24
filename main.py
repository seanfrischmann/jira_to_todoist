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
    fields = ['USER', 'PASSWORD', 'JIRA', 'JQL', 'TODOIST', 'ISSUELINK', 'PROJECT_OPTIONS']
    for field in fields:
        if (field not in config):
            print "Config File is missing:", field
            exit()

    activeTasks = makeRequest({"Authorization": "Bearer %s" % config['TODOIST']},
            {}, {"url": "https://beta.todoist.com/API/v8/tasks"})

    projects = makeRequest({"Authorization": "Bearer %s" % config['TODOIST']},
            {}, {"url": "https://beta.todoist.com/API/v8/projects"})

    labels = makeRequest({"Authorization": "Bearer %s" % config['TODOIST']},
            {}, {"url": "https://beta.todoist.com/API/v8/labels"})

    taskList = {}
    for task in activeTasks:
        taskList[task['content']] = task

    projectList = {}
    for project in projects:
        projectList[project['name']] = project

    labelList = {}
    for label in labels:
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
        todoapi = todoist.TodoistAPI(config['TODOIST'])

        if ('Jira-Issue' not in labelList):
            label = todoapi.labels.add('Jira-Issue')
            todoapi.commit()
            labelList['Jira-Issue'] = label

        configureInInbox = raw_input("Send (" + str(data['total']) +
                ") tasks to Inbox? (yes|no)\n")

        for issue in data['issues']:
            title = '[**' + issue['key'] + '**](' + config['ISSUELINK'] + issue['key']
            title +=  ') ' + issue['fields']['summary']

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

