#
# Gateway Grabber - 2014-02-27
# joe@uberboxen.net
#
# Repoints the default gw for a routing table to the current instance
# that is running this script.
#
# Set the CFN_ROUTETABLE env var with your CloudFormation template
#

import boto
import boto.utils
import os
import sys

dry_run = False

# AWS access/secret keys (None if using EC2 role)
aws_access      = None
aws_secret      = None
region_name     = 'us-east-1'

DEFAULT_ROUTE = '0.0.0.0/0'

try:
    cfn_routetable = os.environ['CFN_ROUTETABLE']
except:
    print("CFN_ROUTETABLE environment variable is not set!")
    sys.exit(1)

try:
    instance_id = boto.utils.get_instance_metadata()['instance-id']
except:
    print("Could not get EC2 instance ID!")
    sys.exit(1)

vpc_conn = boto.connect_vpc(aws_access_key_id=aws_access, aws_secret_access_key=aws_secret)
ec2_conn = boto.connect_ec2(aws_access_key_id=aws_access, aws_secret_access_key=aws_secret)

try:
    rt = vpc_conn.get_all_route_tables(route_table_ids=os.environ['CFN_ROUTETABLE'])[0]
except Exception, e:
    print("Could not find route table [%s]: %s" % (os.environ['CFN_ROUTETABLE'], e))
    sys.exit(1)

print("Found the route table: %s" % (rt.id,))

source_dest_check = ec2_conn.get_instance_attribute(instance_id, 'sourceDestCheck')['sourceDestCheck']

print("Source/Dest check: %s" % (source_dest_check,))

if source_dest_check:
    print("Instance must have source/dest checking disabled to NAT properly!")
    try:
        ec2_conn.modify_instance_attribute(instance_id, 'sourceDestCheck', False, dry_run=dry_run)
    except Exception, e:
        print("Could not modify source/dest check: %s" % (e,))
        sys.exit(1)

gw_route = next(route for route in rt.routes if route.destination_cidr_block == DEFAULT_ROUTE, None)
if not gw_route:
    print("Could not find default gw route in routing table!")
else:
    print("Found a gateway route: %s, %s, %s" % (rt.id, gw_route.destination_cidr_block, instance_id))
    try:
        vpc_conn.delete_route(rt.id, DEFAULT_ROUTE, dry_run=dry_run)
    except Exception, e:
        print("Could not delete gw route! %s" % (e,))
        sys.exit(1)

try:
    vpc_conn.create_route(rt.id, DEFAULT_ROUTE, instance_id=instance_id, dry_run=dry_run)
except Exception, e:
    print("Could not replace gw route! %s" % (e,))
    sys.exit(1)

print("Gateway grabbed!")

