param(
  [string]$StackName = "MemeMuseumStack",
  [string]$KeyName = "my-key",
  [string]$AdminEmail = "admin@example.com",
  [string]$GitRepo = "",
  [string]$PublicSubnetIds = "",
  [string]$VpcId = "",
  [string]$AdminCIDR = "0.0.0.0/0",
  [string]$Region = "us-east-1"
)

$gitParam = ""
if ($GitRepo -ne "") { $gitParam = " GitRepo=$GitRepo" }
$subnetParam = ""
if ($PublicSubnetIds -ne "") { $subnetParam = " PublicSubnetIds=$PublicSubnetIds" }
$vpcParam = ""
if ($VpcId -ne "") { $vpcParam = " VpcId=$VpcId" }
$adminCidParam = ""
if ($AdminCIDR -ne "") { $adminCidParam = " AdminCIDR=$AdminCIDR" }

aws cloudformation deploy `
  --stack-name $StackName `
  --template-file infra\cloudformation\meme_museum_stack.yaml `
  --capabilities CAPABILITY_NAMED_IAM `
  --parameter-overrides KeyName=$KeyName AdminEmail=$AdminEmail$gitParam$subnetParam$vpcParam$adminCidParam `
  --region $Region
