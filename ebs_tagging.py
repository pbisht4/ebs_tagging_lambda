import sys
import os
import re
import collections
import time, datetime
import traceback
import argparse
import csv
import json
import boto3
import botocore
import pprint

import smtplib
import os
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

fromaddr = 'xyz@abc.com'
toaddr = 'xyz@abc.com
msg = MIMEMultipart()
msg['From'] = fromaddr
msg['To'] = toaddr

def lambda_function(event, context):
    try:
        tags = []
        instance_id_tags = []

        client = boto3.client('ec2', 'us-east-1')
        ec2 = boto3.resource('ec2', 'us-east-1')

        response = client.describe_instances()['Reservations']

        # Get instanceID, and tags for all available instances.
        for r in range(len(response)):
            for i in range(len(response[r]['Instances'])):
                instance = []
                #tags.append(response[r]['Instances'][i]['Tags'])
                instance_id = response[r]['Instances'][i]['InstanceId']
                instance_type = response[r]['Instances'][i]['InstanceType']
                inst = ec2.Instance(instance_id)
                tag = inst.tags
                instance.append(instance_id)
                instance.append(instance_type)
                for t in tag:
                    if t.values()[1] in ['ProjectName', 'Owner', 'CostCenterID']:
                        instance.append((t.values()[1], t.values()[0]))
                instance_id_tags.append(instance)

        # Get all available volumes and the instance they are associated with.
        volumesIds = []
        volumes = client.describe_volumes()['Volumes']
        for i in range(len(volumes)):
            volumesIds.append(volumes[i]['VolumeId'])

        # Match the volumes with the tags of the instancesself.
        for v in range(len(volumesIds)):
            volume = ec2.Volume(volumesIds[v])
            # check that the volume is attached to an instance.
            if volume.attachments != []:
                tags = [element for element in instance_id_tags if element[0] in volume.attachments[0]['InstanceId']]
                Tags = []
                count = 0
                for t in tags[0]:
                    if count >= 2:
                        Tags.append({'Key':t[0], 'Value':t[1]})
                    count += 1
                volume.create_tags(Tags=Tags) #write the tags to the volume
            else:
                print(volumesIds[v], '- this volume is not attached to an instance')

    except Exception, e:
        logger.error("ERROR: Lambda function has been failed.")

        msg['Subject'] = "Lambda function has been failed"
        html="<h2>Lambda function has been failed</h2>"
        # SMTP block start to send mail
        msg.attach(MIMEText(html, 'html'))
        server = smtplib.SMTP('XXX.XXX.XXX.XX:XX')
        server.starttls()
        #server.login(fromaddr)
        text = msg.as_string()
        print (text)
        server.sendmail(fromaddr, toaddr, text)
        server.quit()
        # SMTP block end to send mail
        print ("Lambda function has been failed")
        raise e
