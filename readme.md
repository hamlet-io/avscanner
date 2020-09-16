# README

## Description

Virus-scan files that arrive in an S3 bucket, and either move the file to quarantine or dispatch a validation task to a queue. 

## Structure:

Project consists of 1 workers and 2 queues, 2 buckets. Both queues used to pass s3 object created event to workers.

##### Note:
Buckets and queues names provided in default `.env` file located at the project root directory.
Also `.env` file contains connection parameters for both sqs and s3 as well as file prefixes/directories.

#### Workers:
1. Virus scanner - checks that data files are not viruses.

#### Queues:
1. Inbound queue - receives initial object created event in passport scanner data bucket.
1. Outbound queue - receives events after virus scanner worker verified that file is not a virus.

#### Buckets:
1. Quarantine - contains potentially hazardous files/viruses.
1. Unprocessed - contains raw unprocessed files which virus scanner and validator workers will process.

#### Notifications(SNS Topics):
1. Virus - notifies subscribers about detection of a virus in the unprocessed bucket

##### Note:
Unprocessed bucket files expect to have the key structure:

 `<submission_guid>/<filename>`.

Otherwise event will be considered invalid and removed from the queue and file will not be processed.

# General workflow:
1. Object created in the unprocessed  data bucket.
1. Object created event gets posted into virus scanning queue.
1. Virus scanner worker pulls the event from virus scanning queue and performs virus scan.
1. Non virus files object created events forwarded into validation queue.
1. Virus files moved to quarantine bucket. Virus notification sent, copy of notification stored alongside quarantined files as `<filename>.report.json`.

##### Note:
Successfully processed events always deleted from the workers queues. The only situation when file remains in the queue after a worker started processing is an unexpected error which may be caused by an auto-scaling group which may shut down the worker before it finished event processing.

## Test/Demo run:

Make sure you have modern docker installation (if you get some weird errors about Dockefile syntax - upgrade it).
Also, after you have run `make run` - ensure that local directories for buckets are created. To do it check the `.env` file, read values of next variables and create these directories in the `minio/data`:

* QUARANTINE_BUCKET_NAME
* UNPROCESSED_BUCKET_NAME

1. Run `cd <project_root>`
1. Run `make run`
1. In new session `make ssh-processor`
2. Run `py.test` or `make test-integration` inside the container. This will run the tests which mock workflow described above. You'll see verbose logs which are pretty self explanatory.


## Known issues:
1. Integration tests may fail because clamd is not initialized at the moment of the test run. Usually, it takes up to 1 minute to initialize clamd. Wait 1 minute and try again. If the issue persists this maybe something different.
