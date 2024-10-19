from flask import Flask, jsonify, request
import boto3
import subprocess
import os

app = Flask(__name__)

aws_region = 'eu-west-3'
session = boto3.Session(region_name=aws_region)

client = session.client('resourcegroupstaggingapi')
TERRAFORM_DIR = './terraform'

def run_terraform(params):

    try:
        tfvars_content = "\n".join([f"{key} = \"{value}\"" for key, value in params.items()])
        with open(os.path.join(TERRAFORM_DIR, "terraform.tfvars"), "w") as f:
            f.write(tfvars_content)

        subprocess.run(["terraform", "init"], cwd=TERRAFORM_DIR, check=True)
        subprocess.run(["terraform", "apply", "-auto-approve"], cwd=TERRAFORM_DIR, check=True)

        result = subprocess.run(["terraform", "output", "-json"], cwd=TERRAFORM_DIR, capture_output=True, text=True)
        return result.stdout

    except subprocess.CalledProcessError as e:
        return f"Error occurred: {str(e)}"


def get_terraform_resources():
    try:
        response = client.get_resources(
            TagFilters=[
                {
                    'Key': 'Terraform',
                },
            ]
        )
        resources = response['ResourceTagMappingList']

        arns = [resource['ResourceARN'] for resource in resources]
        return arns

    except Exception as e:
        print(f"Error fetching resources: {e}")
        return []


@app.route('/resources', methods=['GET'])
def list_resources():
    arns = get_terraform_resources()
    return jsonify({"terraform_resources": arns})

@app.route('/resource/<resource_type>', methods=['POST'])
def create_resource(resource_type):
    params = request.json

    if resource_type not in ['s3', 'rds', 'lambda']:
        return jsonify({"error": "Invalid resource type. Choose from 's3', 'rds', or 'lambda'."}), 400


    result = run_terraform(params)

    return jsonify({"resource_type": resource_type, "result": result})



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
