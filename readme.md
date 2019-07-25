# README


#### Project has two functions:
1. processor
2. archiver


#### Processor responsible for:
1. Virus scanning
2. File structure validation
3. Files management

#### Archiver responsible for:
1. Creating compressed files archives on a monthly basis
2. Storing archived files in bucket


#### Note:
Archiver is not aws lambda function. It can't perform its task using lambdas instead it must be deployed as scheduled ec2 instance which should turn off once it finished archiving process.

#### Running the project:
Project based on `docker` and `docker-compose`, `make`, therefore, you must have them installed.

To start project you need to:
1. `cd passport-scanner-data`
2. `make run`

Then you can simply ssh into function containers:
1. `make ssh-processor`
2. `make ssh-archiver`

Inside containers you can find even more makefiles containing handy shortcuts. 
