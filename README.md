# Keycloak CSV users importer

## Usage
```
usage: importer.py [-h] [-f FILE] [-c FILE] [--delete] [-l LIMIT]
                   [--clientrole] [--realmrole]

Import users to Keycloak from CSV

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  CSV file that contains users
  -c FILE, --config FILE
                        Config file
  --delete              delete user list in CSV default add
  -l LIMIT, --limit LIMIT
                        limit CSV user to add
  --clientrole          import client roles in CSV
  --realmrole           import realm roles in CSV
```

## Add users in CSV
`python importer.py --config projects/config.ini --file ~/users.csv`

## Delete users in CSV
`python importer.py --config projects/config.ini --file ~/users.csv`

## Delete 5 first users in csv
`python importer.py --config projects/config.ini --file ~/users.csv --limit 5 --delete`