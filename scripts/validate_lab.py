"""Comprehensive lab validation for Meme Museum deployment.
Usage: python scripts/validate_lab.py --stack MemeMuseumStack --region us-east-1
Performs checks:
 - CloudFormation outputs presence
 - ALB /health endpoint
 - TargetGroup health (at least one healthy target)
 - DynamoDB tables existence
 - SNS topic subscription status
 - CloudWatch Log Group presence
Exits with code 0 on success, non-zero on failure.
"""
import argparse
import boto3
import sys
import time
import requests


def get_stack_outputs(cf, stack_name):
    resp = cf.describe_stacks(StackName=stack_name)
    outputs = resp['Stacks'][0].get('Outputs', [])
    return {o['OutputKey']: o['OutputValue'] for o in outputs}


def check_alb_health(alb_dns):
    url = f'http://{alb_dns}/health'
    try:
        r = requests.get(url, timeout=10)
        print('ALB health GET', url, '->', r.status_code)
        print('Response:', r.text)
        return r.status_code == 200
    except Exception as e:
        print('Failed to reach ALB health:', e)
        return False


def check_target_group(elbv2, tg_arn):
    try:
        resp = elbv2.describe_target_health(TargetGroupArn=tg_arn)
        states = resp.get('TargetHealthDescriptions', [])
        print('Targets:', len(states))
        healthy = [s for s in states if s.get('TargetHealth', {}).get('State') == 'healthy']
        for s in states:
            print(' -', s.get('Target', {}), 'state=', s.get('TargetHealth', {}).get('State'))
        return len(healthy) > 0
    except Exception as e:
        print('Error describing target group:', e)
        return False


def check_dynamodb_tables(dynamodb, tables):
    missing = []
    for t in tables:
        try:
            resp = dynamodb.describe_table(TableName=t)
            status = resp['Table'].get('TableStatus')
            print(f'DynamoDB table {t} status: {status}')
        except Exception as e:
            print('DynamoDB table missing or error for', t, e)
            missing.append(t)
    return missing


def check_sns_subscriptions(sns_client, topic_arn, admin_email):
    try:
        subs = sns_client.list_subscriptions_by_topic(TopicArn=topic_arn).get('Subscriptions', [])
        print('SNS subscriptions:', len(subs))
        found = [s for s in subs if s.get('Endpoint') == admin_email]
        if not found:
            print('Admin email not subscribed to topic - you need to confirm subscription from email inbox.')
            return False
        state = found[0].get('SubscriptionArn')
        print('Subscription ARN:', state)
        if found[0].get('SubscriptionArn') == 'PendingConfirmation':
            print('Subscription is pending confirmation - open your email and click confirm link.')
            return False
        return True
    except Exception as e:
        print('Error checking SNS subscriptions:', e)
        return False


def check_cloudwatch_group(cw, group_name):
    try:
        resp = cw.describe_log_groups(logGroupNamePrefix=group_name)
        groups = resp.get('logGroups', [])
        if not groups:
            print('No CloudWatch log group found with prefix', group_name)
            return False
        print('Found CloudWatch Log Group:', groups[0].get('logGroupName'))
        return True
    except Exception as e:
        print('Error checking CloudWatch log groups:', e)
        return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--stack', required=True)
    p.add_argument('--region', default='us-east-1')
    p.add_argument('--admin-email', required=False)
    args = p.parse_args()

    cf = boto3.client('cloudformation', region_name=args.region)
    elbv2 = boto3.client('elbv2', region_name=args.region)
    dynamodb = boto3.client('dynamodb', region_name=args.region)
    sns = boto3.client('sns', region_name=args.region)
    cw = boto3.client('logs', region_name=args.region)

    print('Fetching CloudFormation outputs...')
    outputs = get_stack_outputs(cf, args.stack)
    print(outputs)

    alb = outputs.get('ALB_DNS')
    tg = outputs.get('TargetGroupArn')
    gunicorn_group = outputs.get('GunicornLogGroupName')
    topic_arn = outputs.get('SNS_Topic_ARN')

    ok = True

    if not alb:
        print('ALB_DNS not found in stack outputs')
        ok = False
    else:
        print('Checking ALB health endpoint...')
        if not check_alb_health(alb):
            ok = False

    if not tg:
        print('TargetGroupArn not found in outputs')
        ok = False
    else:
        print('Checking target group health...')
        if not check_target_group(elbv2, tg):
            ok = False

    # DynamoDB checks
    print('Checking DynamoDB tables...')
    missing = check_dynamodb_tables(dynamodb, ['MemeUsers', 'MemeItems', 'MemeLikes', 'MemeLogs'])
    if missing:
        print('Missing tables:', missing)
        ok = False

    if topic_arn:
        print('Checking SNS topic subscriptions...')
        if not args.admin_email:
            print('Admin email not provided; cannot fully verify subscription state')
        else:
            if not check_sns_subscriptions(sns, topic_arn, args.admin_email):
                ok = False
    else:
        print('SNS topic ARN not found in outputs')
        ok = False

    if gunicorn_group:
        print('Checking CloudWatch log group...')
        if not check_cloudwatch_group(cw, gunicorn_group):
            ok = False
    else:
        print('Gunicorn log group name not found in outputs')
        ok = False

    if ok:
        print('\nAll checks passed. Lab deployment appears healthy.')
        sys.exit(0)
    else:
        print('\nOne or more checks failed. See messages above to resolve.')
        sys.exit(2)

if __name__ == '__main__':
    main()
