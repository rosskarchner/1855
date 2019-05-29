import boto3

cloudformation = boto3.client("cloudformation")


def outputs_for_cloudformation_stack(stack_id):
    stack = cloudformation.describe_stacks(StackName=stack_id)["Stacks"][0]
    return {o["OutputKey"]: o["OutputValue"] for o in stack["Outputs"]}
