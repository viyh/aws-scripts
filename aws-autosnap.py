#/usr/bin/env python

#
# AWS auto snapshot script - 2013-08-17
# https://github.com/viyh/aws-scripts
#
# cron script to snapshot all EC2 volumes and delete snapshots older than retention time
#

import boto
import datetime

# number of days to retain snapshots for
retention_days = 2

# AWS access/secret keys
aws_access      = 'FILL_THIS_IN'
aws_secret      = 'ALSO_THIS'

######

print "AWS snapshot backups stated at %s...\n" % datetime.datetime.now()

ec2 = boto.connect_ec2(aws_access_key_id=aws_access, aws_secret_access_key=aws_secret)

reservations = ec2.get_all_instances(filters={'instance-state-name': 'running'})

# look through each instance for EBS volumes
for i in [i for r in reservations for i in r.instances]:

    print "%s - %s" % (i.tags.get('Name'), i.id)

    # loop through volumes and create snapshots
    for v in ec2.get_all_volumes(filters={'attachment.instance-id': i.id}):
        print "\t%s" % v.id
        description = 'autosnap-%s.%s-%s' % ( i.tags.get('Name'), v.id, datetime.datetime.now().strftime("%Y%m%d-%H%M%S") )

        # create snapshot
        if v.create_snapshot(description):
            print "\t\tSnapshot created with description [%s]" % description

        # find and delete snapshots older than retention_days
        for s in v.snapshots():
            print "\t\tsnapshot found: [%s - %s] created [%s]" % ( s.id, s.description, str( boto.utils.parse_ts(s.start_time) ) )
            if s.description.startswith('autosnap-') and ( datetime.datetime.now() - boto.utils.parse_ts(s.start_time) ) > datetime.timedelta(days=retention_days):
                print "\t\tDeleting snapshot [%s - %s]" % ( s.id, s.description )
                try:
                    s.delete()
                    print "yep."
                except EC2ResponseError as e:
                    print "%s" % str(e)
                    pass

print "\n\nAWS snapshot backups completed at %s\n" % datetime.datetime.now()

