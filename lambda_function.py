import json
import os
import json
import boto3
import datetime
import logging
import stack_retain
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# list of regions
regions = ['us-east-1']

# filters to query ec2 instances. put your filters in json format
filters = [
            {
                'Name': 'tag:Name',
                'Values': ['sample']
            },
            {
                'Name': 'tag:Owner',
                'Values': ['Tutu']
            }
        ]

# time threshold to delete stacks. current threshold is 10 days
time_threshold = 0

# get date 10 days ago
time_now = datetime.datetime.now()
logger.info("script started "+time_now.strftime('%Y-%m-%d'))
delta = datetime.timedelta(days=time_threshold)
logger.info("delta value is: {}".format(delta))
last_day = (time_now - delta)
logger.info("last_day is: {}".format(last_day))

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
                    logger.info("Launch time of the instance: {} is:  {}".format(instance,launch_time))
            
                    # if launch time is greater than time threshold get the names of ec2 instances
                    if launch_time.strftime('%Y-%m-%d') <= last_day.strftime('%Y-%m-%d'):
                        for tag in tags:
                            if tag['Key'] == 'Name':
                                if tag['Value'] not in ec2_name_list:
                                    ec2_name_list.append(tag['Value'])
            
        except Exception as e:
            print("ERROR: "+str(e))
            logger.error(str(e))
    
    # return ec2 names
    logger.info("ec2 name list: "+str(ec2_name_list))
    return ec2_name_list
    
    
    
def list_cloudformation_stacks(region):
    stack_list = []
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
                if launch_time.strftime('%Y-%m-%d') <= last_day.strftime('%Y-%m-%d'):
                    if stack['StackName'] in list_ec2_names(region):
                        stack_list.append(stack['StackName'])
        except Exception as e:
            print("ERROR: "+str(e))
            logger.error(str(e))
    
    # return stack lists
    logger.info("stacks in the list are: "+str(stack_list))
    return stack_list
    
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
                if stack in ec2_names and stack not in stack_retain.stack_retain_list:
                    logger.info("Stack to be deleted is: {}".format(stack))
                    delete_cloudformation_stack(region,stack)
                else:
                    logger.info("This stack: {} does not meet the deletion criteria and wil not be deleted".format(stack)) 
        logger.info("Lambda execution is completed! good bye!!")
    except Exception as e:
        print("ERROR: "+str(e))
        logger.error(str(e))
        
