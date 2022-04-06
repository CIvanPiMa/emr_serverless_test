I'll pass the links to the docs and register to the preview at the end 

# Requirements

the min requirements to run JOBS in an APP on EMR SERVERLESS are

- A bucket 

- A policy to access the bucket

- And a role with the policy attached to run the JOBs 

    > each JOB can have their own role, this grants great security for each JOB

## Create a bucket

```shell script
aws s3api create-bucket \
    --bucket civanpima-emr-serverless-bucket \
    --region us-east-1

```

## Create a policy  `emr-sample-access-policy.json`

Set the permissions that you need to run your job, in this case access to the bucket 

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "FullAccessToOutputBucket",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:ListBucket",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::civanpima-emr-serverless-bucket",
                "arn:aws:s3:::civanpima-emr-serverless-bucket/*"
            ]
        }
    ]
}
```

```shell script
aws iam create-policy \
    --policy-name civanpima-emr-serverless-s3-access-policy \
    --policy-document file://emr-sample-access-policy.json
```

### Save the ARN:

```shell script
export POLICY_ARN=arn:aws:iam::874799388578:policy/civanpima-emr-serverless-s3-access-policy

```

## Create a role `emr-serverless-trust-policy.json`

We need a ROLE to RUN ANY JOB, with this we will have a very ganular security for each job

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "EMRServerlessTrustPolicy",
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": "emr-serverless.amazonaws.com"
            }
        }
    ]
}
```

```shell script
aws iam create-role \
    --role-name civanpima-emr-serverless-job-execution-role \
    --assume-role-policy-document file://emr-serverless-trust-policy.json

```

### Save the ARN:

```shell script
export ROLE_ARN=arn:aws:iam::874799388578:role/civanpima-emr-serverless-job-execution-role

```

### Attach the policy to the role

```shell script
aws iam attach-role-policy \
    --role-name civanpima-emr-serverless-job-execution-role \
    --policy-arn $POLICY_ARN

```

# App:

## Create the Spark app

- **RUN THE COMMAND**!!! then you explain...
- In `type` we can set spark or hive 
- the only EMR version available right now is `emr-6.5.0-preview` 
    - We can't choose any instance type or size or anything
- The `initial-capacity` is a configuration to have ALWAYS available when we START the APP
    - CREATE an APP is to let AWS know what kind of resources we are gonna need (but the cluster doesn't exist yet)
- The `maximum-capacity` is the TOTAL SUM of `cpu`/`memory` an so on AVAILABLE for your APP

```shell script
aws emr-serverless create-application \
    --type SPARK \
    --name civanpima-emr-serverless-app \
    --release-label "emr-6.5.0-preview" \
    --initial-capacity '{
      "DRIVER": {
        "workerCount": 1,
        "resourceConfiguration": {
          "cpu": "4vCPU",
          "memory": "10GB",
          "disk": "8GB"
        }
      },
      "EXECUTOR": {
        "workerCount": 2,
        "resourceConfiguration": {
          "cpu": "2vCPU",
          "memory": "2GB",
          "disk": "2GB"
        }
      }
    }' \
    --maximum-capacity '{
        "cpu": "48vCPU",
        "memory": "40GB",
        "disk": "30GB"
	}'


```

### Save the `applicationId`:

```shell script
export APP_ID=00evr7b1kssgt609

```

### Check the app status

Until it is `CREATED`

```shell script
aws emr-serverless get-application \
    --application-id $APP_ID

```

## Start the app:

- **RUN THE COMMAND**!!! then you explain...

- NOW we are going to create the APP (the cluster)

    > From here is where we are suppoused to be charged for the resources, but everything it's going to be FREE while it is in a PREVIEW state.

```shell script
aws emr-serverless start-application \
    --application-id $APP_ID

```

### Check the app status

Until it is `STARTED`

```shell script
aws emr-serverless get-application \
    --application-id $APP_ID

```

## Run jobs in the app:

- **RUN THE COMMAND**!!! then you explain...

- To run a Spark Job we heve to give 

    - the APP ID

    - The Role with the appropriate permissions 

    - the `configuration-overrides` we specify WHERE to write any output of the program (logs/errors/prints and so on)

    - The `job-driver` is "like" the `spark-submit` part of the command

        - `entryPoint` is the S3 path to the pyspark script

        - `sparkSubmitParameters` we can set all the configurations to be able to run the SPARK JOB

            - The `py-files` is the key to work with EMR-Serverless with our current architecture. Every `.py` or `.zip` file that we add there will be distributed with the spark app and will be available through the `PYTHON_PATH` 

        - The `entryPointArguments`: is the list of arguments that we need to pass to the script 

            > Like `input_path`/`output_path` or whatever else we may need

```shell script
aws emr-serverless start-job-run \
    --application-id $APP_ID \
    --execution-role-arn $ROLE_ARN \
    --configuration-overrides '{
        "monitoringConfiguration": {
           "s3MonitoringConfiguration": {
             "logUri": "s3://civanpima-emr-serverless-bucket/logs"
           }
        }
    }' \
    --job-driver '{
        "sparkSubmit": {
            "entryPoint": "s3://civanpima-emr-serverless-bucket/test_emr_serverless/main.py",
            "sparkSubmitParameters": "--py-files s3://civanpima-emr-serverless-bucket/test_emr_serverless/my_project.zip,s3://civanpima-emr-serverless-bucket/test_emr_serverless/required_modules.zip --executor-cores 2 --executor-memory 1g --driver-cores 2 --driver-memory 1g --conf spark.executor.instances=1",
            "entryPointArguments": [
                "my_argument_1",
                "--optional_arg", "my_argument_2"
            ]
        }
	}'


```

### Save the `jobRunId`:

```shell script
export JOB_RUN_ID=00evr7e7s0k33001

```

### "Equivalent" `spark-submit` CMD

```shell
# Env with the code base and modules installed
pipenv run spark-submit \
    ~/Desktop/test_emr_serverless/main.py \
    arg1 \
    --optional_arg arg2

# Env with only the `main.py` script without the dependencies
pipenv run spark-submit \
    ~/Desktop/test_emr_serverless_empty/main.py \
    arg1 \
    --optional_arg arg2

# Env with only the `main.py` script without the required modules
pipenv run spark-submit \
	--py-files /Users/cesar.pina/Desktop/test_emr_serverless/my_project.zip \
    ~/Desktop/test_emr_serverless_empty/main.py \
    arg1 \
    --optional_arg arg2

# Env with only the `main.py` script with all the dependencies
pipenv run spark-submit \
    --py-files /Users/cesar.pina/Desktop/test_emr_serverless/my_project.zip,/Users/cesar.pina/Desktop/test_emr_serverless/required_modules.zip \
    ~/Desktop/test_emr_serverless_empty/main.py \
    arg1 \
    --optional_arg arg2
```

### Check the JOB status 

Until it is `SUCCESS` or `FAILED`

```shell script
aws emr-serverless get-job-run \
    --application-id $APP_ID \
    --job-run-id $JOB_RUN_ID

```

### Check the JOB logs

```shell script
aws s3 cp s3://civanpima-emr-serverless-bucket/logs/applications/$APP_ID/jobs/$JOB_RUN_ID/SPARK_DRIVER/stdout.gz - | gunzip

```

## Stop the App

```shell script
aws emr-serverless stop-application \
    --application-id $APP_ID

```

## Delete the app

```shell script
aws emr-serverless delete-application \
    --application-id $APP_ID

```



# What we'll need

1. Sync the `cdp` repo in S3

2. Package the synced `cdp` repo in S3 

3. Package the required modules in S3

    1. Have a `default_modules.zip` with all the "usual" modules that we use across the pipelines

    2. Have a specific package with the required modules for a pipeline with specific needs

        > Like in `zoominfo` we require the `PyJWT` module

```
s3://.../repo/cdp/...
s3://.../packages/cdp.zip
s3://.../packages/modules/default.zip
s3://.../packages/modules/zoominfo.zip
```



# Links

- [Getting started](https://docs.aws.amazon.com/emr/latest/EMR-Serverless-UserGuide/getting-started.html)

- EMR Serverless [PDF](https://docs.aws.amazon.com/emr/latest/EMR-Serverless-UserGuide/emr-serverless-user-guide.pdf)

- [Main](https://docs.aws.amazon.com/emr/index.html#:~:text=PDF-,Amazon%20EMR%20Serverless,-Run%20big%20data) docs page

- Register for the [Preview](https://pages.awscloud.com/EMR-Serverless-Preview.html) (~3 days response)

    - Upgrade from AWS CLI v1 to v2

    - When given access:
        - Only available in **N. Virginia** (`us-east-1`)

        - Add the `emr-serverless` to the CLI

            ```shell
            aws s3 cp s3://elasticmapreduce/emr-serverless-preview/artifacts/latest/dev/cli/service.json ./service.json
            ```

            ```shell
            aws configure add-model --service-model file://service.json
            ```

        - check if everything works

            ```shell
            aws emr-serverless list-applications
            ```

# UPDATE the code:

## Prepare the `requirements`

```shell script
/Users/cesar.pina/Documents/Projects/test_emr_serverless
export REQUIREMENTS_PATH=/Users/cesar.pina/Documents/Projects/test_emr_serverless/requirements_dir
export CODE_BASE_PATH=/Users/cesar.pina/Documents/Projects/test_emr_serverless
export PACKAGES_PATH=/Users/cesar.pina/.local/share/virtualenvs/test_emr_serverless-QO4uorui/lib/python3.10/site-packages
export PACKAGES=(pydantic typing_extensions requests certifi charset_normalizer idna urllib3)

for directory in my_project required_modules
  do
    rm -r $REQUIREMENTS_PATH/$directory
    mkdir $REQUIREMENTS_PATH/$directory
    if [ $directory = "my_project" ]; then
      # Get the code base package
      cp -R $CODE_BASE_PATH/my_module $REQUIREMENTS_PATH/$directory
      cp $CODE_BASE_PATH/main.py $REQUIREMENTS_PATH/$directory
    else
      # Get the required_modules package
      for package in $PACKAGES
        do
          cp -R $PACKAGES_PATH/$package* $REQUIREMENTS_PATH/$directory
        done
    fi
    # Write the package
    python3 -m zipfile -c $CODE_BASE_PATH/$directory.zip $REQUIREMENTS_PATH/$directory/.
  done

```

## AWS S3

```shell script
# Update the main
aws s3 cp ~/Documents/Projects/test_emr_serverless/main.py s3://civanpima-emr-serverless-bucket/test_emr_serverless/main.py

# Update the requirements
aws s3 cp ~/Documents/Projects/test_emr_serverless/my_project.zip s3://civanpima-emr-serverless-bucket/test_emr_serverless/my_project.zip
aws s3 cp ~/Documents/Projects/test_emr_serverless/required_modules.zip s3://civanpima-emr-serverless-bucket/test_emr_serverless/required_modules.zip

# Update the data
#aws s3 cp --recursive ~/Documents/Projects/test_emr_serverless/data s3://civanpima-emr-serverless-bucket/test_emr_serverless/data
```

