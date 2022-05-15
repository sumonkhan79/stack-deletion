import json
import os
import json
import boto3
import datetime
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# list of regions
regions = ['us-east-2']

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
time_threshold = 10

# get date 10 days ago
time_now = datetime.datetime.now()
logger.info("script started "+time_now.strftime('%Y-%m-%d'))
delta = datetime.timedelta(days=time_threshold)
last_day = (time_now - delta)

def list_ec2_names(region):
    ec2_name_list = []
    response = None
    try:
        ec2 = boto3.client('ec2', region_name=region)
    # filter ec2 instances per given filters
        response = ec2.describe_instances(Filters=filters)
        
    except Exception as e:
        print("ERROR: "+str(e))
        logger.error(str(e))
        
    if response != None:
        try:
            for reservation in response["Reservations"]:
                for instance in reservation["Instances"]:
            
                    #get tags and launched time of an ec2 instances
                    tags = instance["Tags"]
                    launch_time = instance["LaunchTime"]
            
                    # if launch time is greater than time threshold get the names of ec2 instances
                    if launch_time.strftime('%Y-%m-%d') > last_day.strftime('%Y-%m-%d'):
                        for tag in tags:
                            if tag['Key'] == 'Name':
                                ec2_name_list.append(tag['Value'])
            
        except Exception as e:
            print("ERROR: "+str(e))
            logger.error(str(e))
    
    # return ec2 names                        
    return ec2_name_list
    logger.info("ec2 name list: "+str(ec2_name_list))
    
    
def list_cloudformation_stacks(region):
    delete_stack_list = []
    keep_stack_list = []
    response = None
    
    try:
        client = boto3.client('cloudformation', region_name=region)
        response = client.describe_stacks()
    except Exception as e:
        print("ERROR: "+str(e))
        logger.error(str(e))
        
    if response != None:
        try:
            for stack in response["Stacks"]:
                launch_time = stack["CreationTime"]
                if launch_time.strftime('%Y-%m-%d') > last_day.strftime('%Y-%m-%d'):
                    delete_stack_list.append(stack['StackName'])
                else:
                    keep_stack_list.append(stack['StackName'])
        except Exception as e:
            print("ERROR: "+str(e))
            logger.error(str(e))
    
    # return stack lists
    return delete_stack_list, keep_stack_list
    logger.info("stacks to delete: "+str(delete_stack_list))
    logger.info("stacks to keep: "+str(keep_stack_list))
    
def delete_cloudformation_stack(region,stack_name):
    try:
        client = boto3.client('cloudformation', region_name=region)
        response = client.delete_stack(StackName=stack_name)
        print(str(stack_name)+" stack deleted")
        logger.info(str(stack_name)+" stack deleted")
    except Exception as e:
        print("ERROR: "+str(e))
        logger.error(str(e))
    

def lambda_handler(event, context):
    try:
        for region in regions:
            ec2_names = list_ec2_names(region)
            cloudformation_stacks = list_cloudformation_stacks(region)
            for stack in cloudformation_stacks:
                if stack in ec2_names:
                    delete_cloudformation_stack(region,stack)
        logger.info("script executed! good bye!!")
    except Exception as e:
        print("ERROR: "+str(e))
        logger.error(str(e))
        
