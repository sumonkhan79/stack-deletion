import json
import os
import json
import boto3
import datetime
import stack_retain

# list of regions
regions = [os.environ['AWS_REGION']]
print(type(regions))
print("Running in the region: {}".format(regions))
print("Stack retain list is: {}".format(stack_retain.stack_retain_list))

# filters to query ec2 instances. put your filters in json format
filters = [
    {
        'Name': 'tag:Name',
        'Values': ['sample']
    },
    {
        'Name': 'tag:Owner',
        'Values': ['Nas']
    }
]

# time threshold to delete stacks. current threshold is 10 days
time_threshold = 0

# get date 10 days ago
time_now = datetime.datetime.now()
delta = datetime.timedelta(days=time_threshold)
print("delta value is: {}".format(delta))
last_day = (time_now - delta)
print("Last day is: {}".format(last_day))


def list_ec2_names(region):
    ec2_name_list = []
    ec2 = boto3.client('ec2', region_name=region)

    # filter ec2 instances per given filters
    response = ec2.describe_instances(Filters=filters)
    print("Response from describing instance is: {}".format(response))
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            print("instance is: {}".format(instance))

            # get tags and launched time of an ec2 instances
            tags = instance["Tags"]
            print("tags are : {}".format(tags))
            launch_time = instance["LaunchTime"]
            print("launch time is: {}".format(launch_time))

            # if launch time is greater than time threshold get the names of ec2 instances
            print("launch date value is: {}".format(launch_time.strftime('%Y-%m-%d')))
            print("last date value is: {}".format(last_day.strftime('%Y-%m-%d')))
            if launch_time.strftime('%Y-%m-%d') >= last_day.strftime('%Y-%m-%d'):
                for tag in tags:
                    if tag['Key'] == 'Name':
                        ec2_name_list.append(tag['Value'])

    # return ec2 names
    print("List of EC2 instances returned are: {}".format(ec2_name_list))
    return ec2_name_list


def list_cloudformation_stacks(region):
    stack_list = []
    client = boto3.client('cloudformation', region_name=region)
    response = client.describe_stacks()
    for stack in response["Stacks"]:
        launch_time = stack["CreationTime"]
        print("Stack: {} has launch time of: {}".format(stack,launch_time))
        if launch_time.strftime('%Y-%m-%d') <= last_day.strftime('%Y-%m-%d'):
            stack_list.append(stack['StackName'])

    # return stack list
    print("Stack list is: {}".format(stack_list))
    return stack_list


def delete_cloudformation_stack(region, stack_name):
    client = boto3.client('cloudformation', region_name=region)
    response = client.delete_stack(StackName=stack_name)
    print("stacks older than the given days are deleted")


def lambda_handler(event, context):
    for region in regions:
        ec2_names = list_ec2_names(region)
        cloudformation_stacks = list_cloudformation_stacks(region)
        for stack in cloudformation_stacks:
            if stack in ec2_names and stack not in stack_retain.stack_retain_list:
                print("Stack to be deleted is: {}".format(stack))
                delete_cloudformation_stack(region, stack)
            else:
                print("This stack: {} does not meet the deletion criteria and wil not be deleted".format(stack)) 
