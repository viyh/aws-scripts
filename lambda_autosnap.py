#
# AWS auto snapshot script - 2015-10-09
# https://github.com/viyh/aws-scripts
#
# AWS Lambda Python script to snapshot all EC2 volumes and delete snapshots older than retention time
#

import boto3
import json
import datetime

print('Loading function')


def lambda_handler(event, context):
    # print("Received event: " + json.dumps(event, indent=2))
    print("AWS snapshot backups stated at %s...\n" % datetime.datetime.now())

    retention_days = 2
    if 'retention_days' in event:
        retention_days = event['retention_days']

    ec2 = boto3.resource('ec2')

    instances = ec2.instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])

    for i in instances:
        instance_name = filter(lambda tag: tag['Key'] == 'Name', i.tags)[0]['Value']
        print("%s - %s" % (instance_name, i.id))

        # loop through volumes and create snapshots
        for v in ec2.volumes.filter(Filters=[{'Name': 'attachment.instance-id', 'Values': [i.id]}]):
            print("\t%s" % v.volume_id)
            description = 'autosnap-%s.%s-%s' % ( instance_name, v.volume_id,
                datetime.datetime.now().strftime("%Y%m%d-%H%M%S") )

            # create snapshot
            if v.create_snapshot(description):
                print("\t\tSnapshot created with description [%s]" % description)

            # find and delete snapshots older than retention_days
            for s in v.snapshots.all():
                print("\t\tsnapshot found: [%s - %s] created [%s]" % ( s.snapshot_id, s.description,
                    str( s.start_time ) ) )
                if s.description.startswith('autosnap-') and ( datetime.datetime.now() - s.start_time ) > datetime.timedelta(days=retention_days):
                    print("\t\tDeleting snapshot [%s - %s]" % ( s.snapshot_id, s.description ))
                    s.delete()
                    prin("yep.")


    print("\n\nAWS snapshot backups completed at %s\n" % datetime.datetime.now())
    return True
