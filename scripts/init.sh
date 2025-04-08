#!/bin/bash
set -e  # Exit on error

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=${AWS_REGION:-us-east-1}  # Default to us-east-1 if not set

# Create S3 bucket and folder structure
BUCKET_NAME="oidc-github-${AWS_ACCOUNT_ID}"
echo "Creating S3 bucket: ${BUCKET_NAME}"
aws s3api create-bucket --bucket "${BUCKET_NAME}" --region "${REGION}"

for env in dev prod; do
    aws s3api put-object --bucket "${BUCKET_NAME}" --key "${env}/"
    aws s3api put-object --bucket "${BUCKET_NAME}" --key "${env}/ecr/"
done

# Create OIDC identity provider
OIDC_PROVIDER_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
if ! aws iam get-open-id-connect-provider --open-id-connect-provider-arn "${OIDC_PROVIDER_ARN}" >/dev/null 2>&1; then
    echo "Creating OIDC provider"
    aws iam create-open-id-connect-provider \
        --url "https://token.actions.githubusercontent.com" \
        --client-id-list "sts.amazonaws.com" \
fi

# Create IAM role
ROLE_NAME="oidc-github-role"
TRUST_POLICY=$(cat <<EOF
{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {
            "Federated": "arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
        },
        "Action": "sts:AssumeRoleWithWebIdentity",
        "Condition": {
            "StringEquals": {
                "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
            }
        }
    }]
}
EOF
)

echo "Creating IAM role: ${ROLE_NAME}"
aws iam create-role --role-name "${ROLE_NAME}" --assume-role-policy-document "${TRUST_POLICY}"

# Attach AdministratorAccess policy
echo "Attaching AdministratorAccess policy"
aws iam attach-role-policy \
    --role-name "${ROLE_NAME}" \
    --policy-arn "arn:aws:iam::aws:policy/AdministratorAccess"

# Create inline S3 policy
S3_POLICY=$(cat <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::${BUCKET_NAME}",
                "arn:aws:s3:::${BUCKET_NAME}/*"
            ]
        }
    ]
}
EOF
)

echo "Creating inline S3 policy"
aws iam put-role-policy \
    --role-name "${ROLE_NAME}" \
    --policy-name "oidc-github-policy" \
    --policy-document "${S3_POLICY}"

echo "Setup completed successfully!"
echo "Role ARN: arn:aws:iam::${AWS_ACCOUNT_ID}:role/${ROLE_NAME}"