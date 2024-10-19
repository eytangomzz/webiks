import re

from flask import Flask, jsonify, request
import boto3
import subprocess
import os
import json

app = Flask(__name__)

aws_region = 'eu-west-3'
session = boto3.Session(region_name=aws_region)

client = session.client('resourcegroupstaggingapi')
TERRAFORM_DIR = './terraform'


def read_tfvars():
    tfvars_path = os.path.join(TERRAFORM_DIR, "terraform.tfvars")
    with open(tfvars_path, "r") as f:
        return f.read()

def write_tfvars(content):
    tfvars_path = os.path.join(TERRAFORM_DIR, "terraform.tfvars")
    with open(tfvars_path, "w") as f:
        f.write(content)

def run_terraform():
    try:
        subprocess.run(["terraform", "init"], cwd=TERRAFORM_DIR, check=True)

        apply_cmd = ["terraform", "plan", "-auto-approve"]
        subprocess.run(apply_cmd, cwd=TERRAFORM_DIR, check=True)

        result = subprocess.run(["terraform", "output", "-json"], cwd=TERRAFORM_DIR, capture_output=True, text=True)
        return json.loads(result.stdout)

    except subprocess.CalledProcessError as e:
        return {"error": str(e)}



def run_terraform_s3(params):

    try:
        new_bucket_names = request.json.get('bucket_names')
        print(new_bucket_names)

        bucket_names = []
        # bucket_names_var = ','.join(bucket_names)

        # tfvars_content = "\n".join([f"{key} = \"{value}\"" for key, value in params.items()])
        # with open(os.path.join(TERRAFORM_DIR, "terraform.tfvars"), "w") as f:
        #     f.write(tfvars_content)
        tfvars_file_path = os.path.join(TERRAFORM_DIR, "terraform.tfvars")
        if os.path.exists(tfvars_file_path):
            with open(tfvars_file_path, "r") as f:
                content = f.read()
                # Use regex to extract the current bucket_names array
                match = re.search(r'bucket_names\s*=\s*\[([^\]]*)\]', content)
                if match:
                    existing_bucket_names_str = match.group(1).strip()
                    if existing_bucket_names_str:
                        # Convert the string to a list (removing quotes and spaces)
                        existing_bucket_names = [
                            name.strip().strip('"')
                            for name in existing_bucket_names_str.split(",")
                        ]
                        bucket_names.extend(existing_bucket_names)

        bucket_names.extend(new_bucket_names)
        bucket_names = list(set(bucket_names))

        with open(tfvars_file_path, "w") as f:
            # Format bucket names as a properly formatted string for tfvars
            bucket_names_str = ', '.join([f'"{name}"' for name in bucket_names])
            f.write(f'bucket_names = [{bucket_names_str}]\n')

        subprocess.run(["terraform", "init"], cwd=TERRAFORM_DIR, check=True)

        apply_cmd = ["terraform", "apply", "-auto-approve"]
        subprocess.run(apply_cmd, cwd=TERRAFORM_DIR, check=True)
        result = subprocess.run(["terraform", "output", "-json"], cwd=TERRAFORM_DIR, capture_output=True, text=True)
        # apply_cmd = ["terraform", "apply", "-auto-approve", "-var", f"bucket_names={bucket_names}"]
        # subprocess.run(apply_cmd, cwd=TERRAFORM_DIR, check=True)

        # result = subprocess.run(["terraform", "output", "-json"], cwd=TERRAFORM_DIR, capture_output=True, text=True)
        return result.stdout

    except subprocess.CalledProcessError as e:
        return f"Error occurred: {str(e)}"

def append_database_name(db_name):
    content = read_tfvars()
    # Use regex to find existing variable definitions
    match = re.search(r'database_names\s*=\s*\[([^\]]*)\]', content)
    if match:
        # If the variable exists, append to the existing list
        existing_databases = match.group(1).strip().split(",") if match.group(1) else []
        existing_databases.append(f'"{db_name}"')  # Add new database name
        new_databases = ",".join(existing_databases)
        new_content = re.sub(r'database_names\s*=\s*\[([^\]]*)\]', f'database_names = [{new_databases}]', content)
    else:
        # If the variable doesn't exist, create it
        new_content = content + f"\ndatabase_names = [\"{db_name}\"]"

    write_tfvars(new_content)

def run_terraform_rds(params):
    db_name = request.json.get('db_name')
    print(db_name)
    append_database_name(params)
    write_tfvars("\n".join([f"{key} = \"{value}\"" for key, value in params.items()]))
    result = run_terraform()
    return result.stdout

def get_terraform_resources():
    try:
        response = client.get_resources(
            TagFilters=[
                {
                    'Key': 'terraform',
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
    result = 'error'
    if resource_type == 's3':
        params = {
            "bucket_name": request.json.get('bucket_name'),
        }
        result = run_terraform_s3(params)
    elif resource_type == 'rds':
        params = {
            "db_name": request.json.get('db_name'),
            "db_instance_class": request.json.get('db_instance_class'),
            "engine": request.json.get('engine'),
            "username": request.json.get('username'),
            "password": request.json.get('password'),
        }
        result = run_terraform_rds(params)
    else:
        return jsonify({"error": "Unsupported resource type"}), 400

    # params = request.json
    return jsonify(result), 201

@app.route('/resource/<resource_type>', methods=['DELETE'])
def delete_resource(resource_type):
    try:
        if resource_type == 's3':
            resource_name = request.args.get('bucket_name')
        elif resource_type == 'rds':
            resource_name = request.args.get('db_name')
        elif resource_type == 'lambda':
            resource_name = request.args.get('function_name')
        else:
            return jsonify({"error": "Unsupported resource type"}), 400

        if not resource_name:
            return jsonify({"error": f"Missing {resource_type} name parameter"}), 400

        tfvars_file_path = os.path.join(TERRAFORM_DIR, "terraform.tfvars")
        if os.path.exists(tfvars_file_path):
            with open(tfvars_file_path, "r") as f:
                content = f.read()

            match = re.search(r'bucket_names\s*=\s*\[([^\]]*)\]', content)
            if match:
                existing_bucket_names_str = match.group(1).strip()
                existing_bucket_names = [
                    name.strip().strip('"')
                    for name in existing_bucket_names_str.split(",")
                ]
                if resource_name in existing_bucket_names:
                    existing_bucket_names.remove(resource_name)
                else:
                    return jsonify({"error": "No bucket_names found in terraform.tfvars"}), 400

                bucket_names_str = ', '.join([f'"{name}"' for name in existing_bucket_names])
                with open(tfvars_file_path, "w") as f:
                    f.write(f'bucket_names = [{bucket_names_str}]\n')

                subprocess.run(["terraform", "init"], cwd=TERRAFORM_DIR, check=True)
                subprocess.run(["terraform", "apply", "-auto-approve"], cwd=TERRAFORM_DIR, check=True)

                return jsonify({"message": f"{resource_type} resource '{resource_name}' deleted successfully"}), 200
            else:
                return jsonify({"error": "No bucket_names found in terraform.tfvars"}), 400

        return jsonify({"error": "terraform.tfvars file not found"}), 400

    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
