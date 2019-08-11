# README

## Description

Validate and archive files put into passport scanner data s3 bucket.

## Structure:

Project consists of 3 workers and 2 queues, 3 buckets. Both queues used to pass s3 object created event to workers.

##### Note:
Buckets and queues names provided in default `.env` file located at the project root directory.
Also `.env` file contains connection parameters for both sqs and s3 as well as file prefixes/directories. 

#### Workers:
1. Archiver - archives valid data files on a monthly basis.
1. Validator - validates data files format.
1. Virus scanner - checks that data files are not viruses.

#### Queues:
1. Virus scanning queue - receives initial object created event in passport scanner data bucket.
1. Validation queue - receives events after virus scanner worker verified that file is not a virus.

#### Buckets:
1. Archive - contains files which passed virus scanning.
1. Quarantine - contains potentially hazardous files/viruses.
1. Unprocessed - contains raw unprocessed files which virus scanner and validator workers will process.

##### Note:
Passport scanner data bucket files must always have the next key structure:

 `<year>/<month>/<day>/<user>/<filename>`.

Otherwise event will be considered invalid and removed from the queue and file will not be processed.

# General workflow:
1. Object created in the passport scanner data bucket.
1. Object created event gets posted into virus scanning queue.
1. Virus scanner worker pulls the event from virus scanning queue and performs virus scan.
1. Non virus files object created events forwarded into validation queue.
1. Virus files moved to quarantine bucket.
1. Validator worker pulls event from validation queue and performs validation.
1. Valid files saved to archive bucket with `valid/` key prefix.
1. Invalid files saved to archive bucket with `invalid/` key prefix.
1. Then once a month archer worker starts, grabs files from archive bucket by common prefix `valid/<year>/<previous_month>`, compresses them, deletes them from the bucket and post compressed archive as a single file as `compressed/<year>/<previous_month>/archive.zip`.

##### Note:
Successfully processed events always deleted from the workers queues. The only situation when file remains in the queue after a worker started processing is an unexpected error which may be caused by an auto-scaling group which may shut down the worker before it finished event processing.

## Test/Demo run:
1. Run `cd <project_root>`
1. Run `make run`
1. In new session `make ssh-project`
1. In ssh session `make test-integration`. This will run the tests which mock workflow described above. You'll see verbose logs which are pretty self explanatory.


## Known issues:
1. Integration tests may fail because clamd is not initialized at the moment of the test run. Usually, it takes up to 1 minute to initialize clamd. Wait 1 minute and try again. If the issue persists this maybe something different.
