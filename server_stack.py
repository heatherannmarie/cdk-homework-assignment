from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_rds as rds,
)
from constructs import Construct

class ServerStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # security group
        web_server_sg = ec2.SecurityGroup(
            self,
            "WebServerSecurityGroup",
            vpc=vpc,
            description="Security group for web servers",
            allow_all_outbound=True
        )

        # inbound traffic rule
        web_server_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            "Allow HTTP traffic from anywhere"
        )

        # iam role
        instance_role = iam.Role(
            self,
            "WebServerRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com")
        )
        instance_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")
        )

        # apache install script
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "#!/bin/bash",
            "yum update -y",
            "yum install -y httpd",
            "systemctl start httpd",
            "systemctl enable httpd",
            "echo '<html><h1>Web Server in AZ: $(ec2-metadata --availability-zone | cut -d \" \" -f 2)</h1></html>' > /var/www/html/index.html"
        )

        # public subnets
        public_subnets = vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC).subnets

        # public webserver 1 in one subnet
        web_server_1 = ec2.Instance(
            self,
            "WebServer1",
            vpc=vpc,
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ec2.AmazonLinuxImage(
                generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2
            ),
            role=instance_role,
            security_group=web_server_sg,
            vpc_subnets=ec2.SubnetSelection(subnets=[public_subnets[0]]),
            user_data=user_data
        )

        # public webserver 2 in second subnet
        web_server_2 = ec2.Instance(
            self,
            "WebServer2",
            vpc=vpc,
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ec2.AmazonLinuxImage(
                generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2
            ),
            role=instance_role,
            security_group=web_server_sg,
            vpc_subnets=ec2.SubnetSelection(subnets=[public_subnets[1]]),
            user_data=user_data
        )

        # rds instance security group
        rds_sg = ec2.SecurityGroup(
            self,
            "RDSSecurityGroup",
            vpc=vpc,
            description="Security group for RDS MySQL instance",
            allow_all_outbound=True
        )

        # mysql traffic rules
        rds_sg.add_ingress_rule(
            web_server_sg,
            ec2.Port.tcp(3306),
            "Allow MySQL traffic from web servers only"
        )

        # database subnet group
        db_subnet_group = rds.SubnetGroup(
            self,
            "DBSubnetGroup",
            description="Subnet group for RDS instance",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
        )

        # mySQL database
        db_instance = rds.DatabaseInstance(
            self,
            "MySQLDatabase",
            engine=rds.DatabaseInstanceEngine.mysql(
                version=rds.MysqlEngineVersion.VER_8_0
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3,
                ec2.InstanceSize.MICRO
            ),
            vpc=vpc,
            security_groups=[rds_sg],
            subnet_group=db_subnet_group,
            allocated_storage=20,
            database_name="myappdatabase",
            credentials=rds.Credentials.from_generated_secret("admin"),
            multi_az=False,
            publicly_accessible=False,
            removal_policy=Stack.of(self).removal_policy if hasattr(Stack.of(self), 'removal_policy') else None
        )