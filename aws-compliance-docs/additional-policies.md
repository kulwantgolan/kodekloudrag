# Additional AWS Compliance Policies

## Lambda Function Configuration Requirements

### Timeout and Memory Settings
All Lambda functions must adhere to the following configuration standards:
- Maximum timeout limit: 900 seconds (15 minutes)
- Default timeout should be set to 30 seconds for standard functions
- Memory allocation between 128 MB and 10,240 MB
- Reserved concurrent executions must be configured for production functions

Policy ID: AWS-POL-LAMBDA-001
Compliance Level: Required
Audit Frequency: Monthly

## EBS Volume Encryption Standards

### Encryption Requirements
All EBS volumes must implement encryption for data protection:
- Encryption is required for all production EBS volumes
- Use AWS managed keys (aws/ebs) or customer managed KMS keys
- Default encryption must be enabled at the account level
- Unencrypted volumes in development must be tagged with "encryption-exception"

Policy ID: AWS-POL-EBS-001
Compliance Level: Mandatory
Review Cycle: Quarterly

## EC2 Advanced Compliance Policies

### Policy AWS-POL-EC2-002
This policy defines advanced EC2 instance requirements:
- All EC2 instances must have detailed monitoring enabled
- Instance metadata service version 2 (IMDSv2) is required
- Instances must be part of an Auto Scaling group or have a documented exception
- Public IP addresses are prohibited except for NAT instances and bastion hosts
- All instances must have AWS Systems Manager (SSM) agent installed and running

Compliance Scope: All production and staging environments
Enforcement: Automated via AWS Config rules
Last Updated: January 2024

## Database Backup Policies

### RDS Automated Backup Requirements
- Automated backups must be enabled with minimum 7-day retention
- Point-in-time recovery must be available
- Manual snapshots required before major changes
- Cross-region backup replication for critical databases

### DynamoDB Backup Standards
- Point-in-time recovery (PITR) enabled for all production tables
- Daily automated backups with 35-day retention
- On-demand backups before schema modifications

## Network Security Addendum

### NACLs and Security Groups
- Network ACLs must be configured with explicit deny rules
- Security groups should follow the principle of least privilege
- Outbound rules must be explicitly defined (no 0.0.0.0/0 allow all)
- Regular review and cleanup of unused security groups (monthly)

### VPC Endpoint Requirements
- Use VPC endpoints for S3 and DynamoDB to avoid internet gateway traffic
- PrivateLink endpoints required for accessing AWS services from private subnets
- Endpoint policies must restrict access to authorized resources only

## Monitoring and Alerting Standards

### CloudWatch Alarms Configuration
- CPU utilization alarms for all EC2 instances (threshold: 80%)
- Disk space monitoring for all instances (threshold: 85%)
- Failed login attempts alarm (threshold: 5 attempts in 5 minutes)
- Billing alarms must be configured with appropriate thresholds

### Log Aggregation Requirements
- All application logs must be sent to CloudWatch Logs
- Log groups must have defined retention periods (90 days default)
- Sensitive data must be masked in logs using CloudWatch Logs Insights patterns
- Export critical logs to S3 for long-term storage (1 year minimum)