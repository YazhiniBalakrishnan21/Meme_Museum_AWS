VENV=venv

.PHONY: venv install start check deploy validate

venv:
	python -m venv $(VENV)
	@echo "Run 'source $(VENV)/Scripts/Activate.ps1' (PowerShell) or 'source $(VENV)/bin/activate' (bash)"

install:
	$(VENV)/Scripts/pip install -r requirements.txt

start:
	python app.py

check:
	pwsh -File scripts/check_prereqs.ps1

deploy:
	pwsh -File scripts/deploy_cf.ps1 -KeyName "my-keypair" -AdminEmail "admin@example.com" -GitRepo "https://github.com/<you>/<repo>.git" -PublicSubnetIds "subnet-aaa,subnet-bbb" -VpcId "vpc-xxxx" -AdminCIDR "YOUR_IP/32"

validate:
	python scripts/validate_deployment.py --stack MemeMuseumStack --region us-east-1
