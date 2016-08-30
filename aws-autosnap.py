#!/usr/bin/python

######
#
# AWS auto snapshot script - 2016-03-31
# https://github.com/viyh/aws-scripts
#
# Snapshot all EC2 volumes and delete snapshots older than retention time
#
# Required IAM permissions:
#   ec2:DescribeInstances
#   ec2:DescribeVolumes
#   ec2:CreateSnapshot
#   ec2:DeleteSnapshot
#   ec2:DescribeSnapshots
#   ec2:CreateTags
#

import boto3
import datetime
from datetime import tzinfo, timedelta, datetime

# number of days to retain snapshots for
retention_days = 7

# create snapshot for volume
def create_volume_snapshot(instance_name, volume):
    description = 'autosnap-%s.%s-%s' % ( instance_name, volume.volume_id,
        datetime.now().strftime("%Y%m%d-%H%M%S") )
    snapshot = volume.create_snapshot(Description=description)
    if snapshot:
        snapshot.create_tags(Tags=[{'Key': 'Name', 'Value': description}])
        print("\t\tSnapshot created with description [%s]" % description)

# find and delete snapshots older than retention_days
def prune_volume_snapshots(retention_days, volume):
    for s in volume.snapshots.all():
        now = datetime.now(s.start_time.tzinfo)
        old_snapshot = ( now - s.start_time ) > timedelta(days=retention_days)
        if not old_snapshot or not s.description.startswith('autosnap-'): continue
        print("\t\tDeleting snapshot [%s - %s] created [%s]" % ( s.snapshot_id, s.description, str( s.start_time )))
        s.delete()

def snapshot_volumes(instance_name, retention_days, volumes):
    for v in volumes:
        print("\t%s" % v.volume_id)
        create_volume_snapshot(instance_name, v)
        prune_volume_snapshots(retention_days, v)

#####
#####
#####

print("AWS snapshot backups stated at %s...\n" % datetime.now())

ec2 = boto3.resource('ec2')
instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
for i in instances:
    instance_name = filter(lambda tag: tag['Key'] == 'Name', i.tags)[0]['Value']
    print("%s - %s" % (instance_name, i.id))
    volumes = ec2.volumes.filter(Filters=[{'Name': 'attachment.instance-id', 'Values': [i.id]}])
    snapshot_volumes(instance_name, retention_days, volumes)
print("\n\nAWS snapshot backups completed at %s\n" % datetime.now())
