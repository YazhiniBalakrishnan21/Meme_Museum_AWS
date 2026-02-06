# Lab Validation Checklist ✅

Follow these steps after you've deployed the CloudFormation stack to verify the Meme Museum app is fully functional in AWS.

## 1) Quick smoke check
- Run the health endpoint check locally with the provided stack outputs (or Use `scripts/validate_lab.py`):

  ```bash
  python scripts/validate_lab.py --stack <STACK_NAME> --region <AWS_REGION> --admin-email <YOUR_ADMIN_EMAIL>
  ```

  - Expect exit code 0 and messages showing ALB health OK, at least one healthy target, DynamoDB tables available, SNS subscription confirmed, and CloudWatch log group present.

## 2) SNS subscription
- When the stack is created, an email subscription will be sent to the `AdminEmail` you provided.
- Confirm the subscription from your email inbox so SNS can deliver notifications (this is manual).

## 3) CloudWatch and logs
- Open the CloudWatch console and inspect the log group named by the CloudFormation output `GunicornLogGroupName`. You should see log streams from the instance(s) running gunicorn. If not, check instance boot logs and the user-data in the Launch Template.

## 4) DynamoDB tables
- Console: Verify tables `MemeUsers`, `MemeItems`, `MemeLikes`, `MemeLogs` exist and have at least the right key schema.

## 5) ALB / Application
- Open the ALB DNS (CloudFormation output `ALB_DNS`) in a browser and
  - Visit `http://<ALB_DNS>/` and the site should load
  - Visit `http://<ALB_DNS>/health` and get a `200 OK` with a health message

## 6) Functional tests (manual web flow)
- Register a new user via the web UI
- Login and upload an image (the app runs Rekognition; if an image is flagged it will be rejected)
- Confirm the meme appears on the dashboard after upload and that you can view, like, and download
- Check `MemeItems` in DynamoDB for stored metadata

## 7) Post-checks
- Check the SNS topic for Publish activity when a new meme is uploaded or when log events occur
- Check CloudWatch for errors or stack traces if anything fails

---

If any automated check fails, collect the CloudFormation events and `/var/log/cloud-init-output.log` from the instance via SSM (if enabled) or by SSH (if you used a key pair) and inspect boot-time errors.

If you want, run the simple ALB health check directly:

```bash
curl -v http://$(aws cloudformation describe-stacks --stack-name <STACK_NAME> --query 'Stacks[0].Outputs[?OutputKey==`ALB_DNS`].OutputValue' --output text)/health
```

Good luck — open a ticket with the stack name, ALB DNS, and any CloudWatch logs if you need help diagnosing problems. 🔧
