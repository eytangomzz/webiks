from flask import Flask, jsonify
import boto3

app = Flask(__name__)

aws_region = 'eu-west-3'  # Set your region here
session = boto3.Session(region_name=aws_region)

client = session.client('resourcegroupstaggingapi')


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
    """Return a JSON response with all ARNs of resources created by Terraform."""
    arns = get_terraform_resources()
    return jsonify({"terraform_resources": arns})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
