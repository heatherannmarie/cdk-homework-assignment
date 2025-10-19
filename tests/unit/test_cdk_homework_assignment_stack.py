import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_homework_assignment.cdk_homework_assignment_stack import CdkHomeworkAssignmentStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_homework_assignment/cdk_homework_assignment_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkHomeworkAssignmentStack(app, "cdk-homework-assignment")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
