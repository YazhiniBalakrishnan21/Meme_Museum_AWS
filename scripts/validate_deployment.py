"""Validate deployment: fetch CloudFormation stack outputs and hit /health on the EC2 public IP.
Usage: python scripts/validate_deployment.py --stack MemeMuseumStack --region us-east-1
"""
import argparse
import boto3
import requests
import sys


def get_stack_output(stack_name, region):
    cf = boto3.client('cloudformation', region_name=region)
    resp = cf.describe_stacks(StackName=stack_name)
    if not resp['Stacks']:
        return {}
    outputs = resp['Stacks'][0].get('Outputs', [])
    return {o['OutputKey']: o['OutputValue'] for o in outputs}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--stack', required=True)
    p.add_argument('--region', default='us-east-1')
    args = p.parse_args()

    outputs = get_stack_output(args.stack, args.region)
    print('Stack outputs:', outputs)

    alb = outputs.get('ALB_DNS')
    if not alb:
        print('No ALB_DNS in outputs. Exiting.')
        sys.exit(2)

    url = f'http://{alb}/health'
    try:
        r = requests.get(url, timeout=10)
        print('GET', url, '->', r.status_code, r.text)
    except Exception as e:
        print('Failed to reach health endpoint:', e)
        sys.exit(2)

if __name__ == '__main__':
    main()
