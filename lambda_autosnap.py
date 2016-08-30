#
# AWS auto snapshot script - 2015-10-09
# https://github.com/viyh/aws-scripts
#
# AWS Lambda Python script to snapshot all EC2 volumes and delete snapshots older than retention time
#
# Required IAM permissions:
#   ec2:DescribeInstances
#   ec2:DescribeVolumes
#   ec2:CreateSnapshot
#   ec2:DeleteSnapshot
#   ec2:DescribeSnapshots
#   ec2:CreateTags
#
# Event parameters:
#   * regions (default: [region where Lambda function is running])
#       list of regions to snapshot
#   * retention_days (default: 2)
#       integer number of days to keep snapshots
#

import boto3
import json, datetime
from datetime import tzinfo, timedelta, datetime


print('Loading function')

def lambda_handler(event, context):
    regions = [context.invoked_function_arn.split(':')[3]]
    if 'regions' in event:
        regions = event['regions']

    retention_days = 2
    if 'retention_days' in event:
        retention_days = event['retention_days']

    print("AWS snapshot backups stated at %s...\n" % datetime.now())
    for region in regions:
        print("Region: %s" % region)
        create_region_snapshots(region, retention_days)
    print("\nAWS snapshot backups completed at %s\n" % datetime.now())

# create snapshot for region
def create_region_snapshots(region, retention_days):
    ec2 = boto3.resource('ec2', region_name=region)
    instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    for i in instances:
        instance_name = filter(lambda tag: tag['Key'] == 'Name', i.tags)[0]['Value']
        print("\t%s - %s" % (instance_name, i.id))
        volumes = ec2.volumes.filter(Filters=[{'Name': 'attachment.instance-id', 'Values': [i.id]}])
        snapshot_volumes(instance_name, retention_days, volumes)

# create and prune snapshots for volume
def snapshot_volumes(instance_name, retention_days, volumes):
    for v in volumes:
        print("\t\tVolume found: \t%s" % v.volume_id)
        create_volume_snapshot(instance_name, v)
        prune_volume_snapshots(retention_days, v)

# create snapshot for volume
def create_volume_snapshot(instance_name, volume):
    description = 'autosnap-%s.%s-%s' % ( instance_name, volume.volume_id,
        datetime.now().strftime("%Y%m%d-%H%M%S") )
    snapshot = volume.create_snapshot(Description=description)
    if snapshot:
        snapshot.create_tags(Tags=[{'Key': 'Name', 'Value': description}])
        print("\t\t\tSnapshot created with description [%s]" % description)

# find and delete snapshots older than retention_days
def prune_volume_snapshots(retention_days, volume):
    for s in volume.snapshots.all():
        now = datetime.now(s.start_time.tzinfo)
        old_snapshot = ( now - s.start_time ) > timedelta(days=retention_days)
        if not old_snapshot or not s.description.startswith('autosnap-'): continue
        print("\t\t\tDeleting snapshot [%s - %s] created [%s]" % ( s.snapshot_id, s.description, str( s.start_time )))
        s.delete()
