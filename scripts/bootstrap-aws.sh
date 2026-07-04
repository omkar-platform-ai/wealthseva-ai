#!/usr/bin/env bash
# =============================================================================
#  WealthSeva AI — Prototype AWS Bootstrap  (Jul 9 deadline)
#  Run once from your local machine or CloudShell (ap-south-1)
#
#  What this script provisions:
#   Day 1 ── ECR repo, Secrets Manager secrets, EC2 IAM role + CloudWatch log group
#   Day 2 ── CloudFront + WAF, ACM certificate
#   Day 3 ── Amplify app (GitHub connection)
#
#  Usage:
#   chmod +x scripts/bootstrap-aws.sh
#   ./scripts/bootstrap-aws.sh          # full run
#   ./scripts/bootstrap-aws.sh day1     # only Day 1 resources
#   ./scripts/bootstrap-aws.sh day2     # only Day 2 resources
#   ./scripts/bootstrap-aws.sh day3     # only Day 3 resources
#
#  Prerequisites:
#   - AWS CLI v2 configured: aws configure  (profile with AdministratorAccess)
#   - jq installed: brew install jq  /  apt-get install jq
#   - Your EC2 instance already running (t3.medium, Ubuntu 22.04)
#   - Docker installed on EC2 (script will install it if not present)
#
#  After running:
#   1. Copy the printed GitHub secrets into your repo Settings → Secrets
#   2. Push to main → watch the Actions tab
# =============================================================================

set -euo pipefail

# ─────────────────────────────── CONFIGURATION ───────────────────────────────
AWS_REGION="ap-south-1"
APP_NAME="wealthseva"
ECR_REPO_NAME="wealthseva-backend"
DOMAIN=""                        # e.g. "wealthseva.yourdomain.com" — leave blank to skip ACM/CloudFront custom domain

# EC2 instance — set your instance ID here
EC2_INSTANCE_ID=""               # e.g. "i-0abc123def456789"

# Secrets to store in Secrets Manager
# Fill these in before running (or export as env vars)
ELEVENLABS_API_KEY="${ELEVENLABS_API_KEY:-PLACEHOLDER}"
ELEVENLABS_VOICE_ID_HINDI="${ELEVENLABS_VOICE_ID_HINDI:-PLACEHOLDER}"
ELEVENLABS_VOICE_ID_ENGLISH="${ELEVENLABS_VOICE_ID_ENGLISH:-PLACEHOLDER}"
ELEVENLABS_VOICE_ID_MARATHI="${ELEVENLABS_VOICE_ID_MARATHI:-PLACEHOLDER}"
ELEVENLABS_VOICE_ID_TAMIL="${ELEVENLABS_VOICE_ID_TAMIL:-PLACEHOLDER}"
ELEVENLABS_VOICE_ID_BENGALI="${ELEVENLABS_VOICE_ID_BENGALI:-PLACEHOLDER}"
PINECONE_API_KEY="${PINECONE_API_KEY:-PLACEHOLDER}"
PINECONE_INDEX="${PINECONE_INDEX:-wealthseva-index}"
IDBI_CLIENT_ID="${IDBI_CLIENT_ID:-PLACEHOLDER}"
IDBI_CLIENT_SECRET="${IDBI_CLIENT_SECRET:-PLACEHOLDER}"
SUPABASE_URL="${SUPABASE_URL:-PLACEHOLDER}"
SUPABASE_ANON_KEY="${SUPABASE_ANON_KEY:-PLACEHOLDER}"
SUPABASE_SERVICE_KEY="${SUPABASE_SERVICE_KEY:-PLACEHOLDER}"

# GitHub repo for Amplify (frontend)
GITHUB_REPO="https://github.com/YOUR_ORG/wealthseva-ai"  # update this
# ─────────────────────────────────────────────────────────────────────────────

# ── Helpers ──────────────────────────────────────────────────────────────────
step()  { echo; echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; echo "  $1"; echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; }
ok()    { echo "  ✅  $1"; }
info()  { echo "  ℹ️   $1"; }
warn()  { echo "  ⚠️   $1"; }
die()   { echo "  ❌  $1" >&2; exit 1; }

check_prereqs() {
  command -v aws  >/dev/null 2>&1 || die "aws CLI not found. Install from https://aws.amazon.com/cli/"
  command -v jq   >/dev/null 2>&1 || die "jq not found. brew install jq"
  aws sts get-caller-identity --region "$AWS_REGION" >/dev/null 2>&1 || die "AWS credentials not configured. Run: aws configure"
}

get_account_id() {
  aws sts get-caller-identity --query Account --output text
}

# ═════════════════════════════ DAY 1 ══════════════════════════════════════════
day1() {
  step "DAY 1 — ECR · Secrets Manager · IAM Role · CloudWatch Logs"

  ACCOUNT_ID=$(get_account_id)
  info "Account: ${ACCOUNT_ID}  Region: ${AWS_REGION}"

  # ── 1a. ECR repository ────────────────────────────────────────────────────
  step "1a. Creating ECR repository: ${ECR_REPO_NAME}"
  if aws ecr describe-repositories \
       --repository-names "${ECR_REPO_NAME}" \
       --region "${AWS_REGION}" >/dev/null 2>&1; then
    info "ECR repo already exists — skipping"
  else
    aws ecr create-repository \
      --repository-name "${ECR_REPO_NAME}" \
      --region "${AWS_REGION}" \
      --image-scanning-configuration scanOnPush=true \
      --encryption-configuration encryptionType=AES256 \
      --output json | jq -r '.repository.repositoryUri'
    ok "ECR repo created"
  fi
  ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"
  info "ECR URI: ${ECR_URI}"

  # Lifecycle policy — keep last 10 images, delete untagged after 1 day
  aws ecr put-lifecycle-policy \
    --repository-name "${ECR_REPO_NAME}" \
    --region "${AWS_REGION}" \
    --lifecycle-policy-text '{
      "rules": [
        {"rulePriority": 1, "description": "Expire untagged after 1 day",
         "selection": {"tagStatus": "untagged", "countType": "sinceImagePushed", "countUnit": "days", "countNumber": 1},
         "action": {"type": "expire"}},
        {"rulePriority": 2, "description": "Keep last 10 tagged images",
         "selection": {"tagStatus": "tagged", "tagPrefixList": ["sha-"], "countType": "imageCountMoreThan", "countNumber": 10},
         "action": {"type": "expire"}}
      ]
    }' >/dev/null
  ok "ECR lifecycle policy set"

  # ── 1b. Secrets Manager ───────────────────────────────────────────────────
  step "1b. Storing secrets in AWS Secrets Manager"
  SECRET_NAME="${APP_NAME}/production"
  SECRET_VALUE=$(jq -n \
    --arg el_key   "$ELEVENLABS_API_KEY" \
    --arg el_hi    "$ELEVENLABS_VOICE_ID_HINDI" \
    --arg el_en    "$ELEVENLABS_VOICE_ID_ENGLISH" \
    --arg el_mr    "$ELEVENLABS_VOICE_ID_MARATHI" \
    --arg el_ta    "$ELEVENLABS_VOICE_ID_TAMIL" \
    --arg el_bn    "$ELEVENLABS_VOICE_ID_BENGALI" \
    --arg pc_key   "$PINECONE_API_KEY" \
    --arg pc_idx   "$PINECONE_INDEX" \
    --arg idbi_id  "$IDBI_CLIENT_ID" \
    --arg idbi_sec "$IDBI_CLIENT_SECRET" \
    --arg sb_url   "$SUPABASE_URL" \
    --arg sb_anon  "$SUPABASE_ANON_KEY" \
    --arg sb_svc   "$SUPABASE_SERVICE_KEY" \
    '{
      ELEVENLABS_API_KEY: $el_key,
      ELEVENLABS_VOICE_ID_HINDI: $el_hi,
      ELEVENLABS_VOICE_ID_ENGLISH: $el_en,
      ELEVENLABS_VOICE_ID_MARATHI: $el_mr,
      ELEVENLABS_VOICE_ID_TAMIL: $el_ta,
      ELEVENLABS_VOICE_ID_BENGALI: $el_bn,
      PINECONE_API_KEY: $pc_key,
      PINECONE_INDEX: $pc_idx,
      IDBI_CLIENT_ID: $idbi_id,
      IDBI_CLIENT_SECRET: $idbi_sec,
      SUPABASE_URL: $sb_url,
      SUPABASE_ANON_KEY: $sb_anon,
      SUPABASE_SERVICE_ROLE_KEY: $sb_svc
    }')

  if aws secretsmanager describe-secret \
       --secret-id "${SECRET_NAME}" \
       --region "${AWS_REGION}" >/dev/null 2>&1; then
    aws secretsmanager update-secret \
      --secret-id "${SECRET_NAME}" \
      --secret-string "${SECRET_VALUE}" \
      --region "${AWS_REGION}" >/dev/null
    ok "Secret '${SECRET_NAME}' updated"
  else
    aws secretsmanager create-secret \
      --name "${SECRET_NAME}" \
      --description "WealthSeva AI production secrets" \
      --secret-string "${SECRET_VALUE}" \
      --region "${AWS_REGION}" >/dev/null
    ok "Secret '${SECRET_NAME}' created"
  fi

  # ── 1c. CloudWatch Log Group ──────────────────────────────────────────────
  step "1c. Creating CloudWatch log group"
  LOG_GROUP="/wealthseva/backend"
  aws logs create-log-group \
    --log-group-name "${LOG_GROUP}" \
    --region "${AWS_REGION}" 2>/dev/null || true
  aws logs put-retention-policy \
    --log-group-name "${LOG_GROUP}" \
    --retention-in-days 14 \
    --region "${AWS_REGION}" >/dev/null
  ok "Log group '${LOG_GROUP}' ready (14-day retention)"

  # ── 1d. IAM Role for EC2 ──────────────────────────────────────────────────
  step "1d. Creating IAM Role: ${APP_NAME}-ec2-role"
  ROLE_NAME="${APP_NAME}-ec2-role"
  TRUST_POLICY='{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

  if aws iam get-role --role-name "${ROLE_NAME}" >/dev/null 2>&1; then
    info "IAM role already exists — skipping creation"
  else
    aws iam create-role \
      --role-name "${ROLE_NAME}" \
      --assume-role-policy-document "${TRUST_POLICY}" \
      --description "WealthSeva EC2 role — Bedrock, ECR, Secrets Manager, S3, CloudWatch" \
      >/dev/null
    ok "IAM role created"
  fi

  # Inline policy — least-privilege
  POLICY_DOC=$(jq -n \
    --arg account "$ACCOUNT_ID" \
    --arg region "$AWS_REGION" \
    --arg ecr_repo "$ECR_REPO_NAME" \
    --arg secret_name "${APP_NAME}/production" \
    '{
      "Version": "2012-10-17",
      "Statement": [
        {
          "Sid": "BedrockAccess",
          "Effect": "Allow",
          "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
          "Resource": [
            "arn:aws:bedrock:*::foundation-model/*",
            "arn:aws:bedrock:*:\($account):inference-profile/*"
          ]
        },
        {
          "Sid": "ECRPull",
          "Effect": "Allow",
          "Action": [
            "ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage",
            "ecr:BatchCheckLayerAvailability", "ecr:GetAuthorizationToken"
          ],
          "Resource": "*"
        },
        {
          "Sid": "SecretsRead",
          "Effect": "Allow",
          "Action": "secretsmanager:GetSecretValue",
          "Resource": "arn:aws:secretsmanager:\($region):\($account):secret:\($secret_name)*"
        },
        {
          "Sid": "S3Access",
          "Effect": "Allow",
          "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"],
          "Resource": [
            "arn:aws:s3:::wealthseva-ai-assets",
            "arn:aws:s3:::wealthseva-ai-assets/*"
          ]
        },
        {
          "Sid": "CloudWatchLogs",
          "Effect": "Allow",
          "Action": [
            "logs:CreateLogGroup", "logs:CreateLogStream",
            "logs:PutLogEvents", "logs:DescribeLogStreams"
          ],
          "Resource": "arn:aws:logs:\($region):\($account):log-group:/wealthseva/*"
        }
      ]
    }')

  aws iam put-role-policy \
    --role-name "${ROLE_NAME}" \
    --policy-name "${APP_NAME}-ec2-policy" \
    --policy-document "${POLICY_DOC}" >/dev/null
  ok "IAM inline policy attached"

  # Instance profile
  PROFILE_NAME="${ROLE_NAME}-profile"
  if ! aws iam get-instance-profile --instance-profile-name "${PROFILE_NAME}" >/dev/null 2>&1; then
    aws iam create-instance-profile --instance-profile-name "${PROFILE_NAME}" >/dev/null
    aws iam add-role-to-instance-profile \
      --instance-profile-name "${PROFILE_NAME}" \
      --role-name "${ROLE_NAME}" >/dev/null
    ok "Instance profile created"
  else
    info "Instance profile already exists — skipping"
  fi

  # ── 1e. Attach IAM role to EC2 ────────────────────────────────────────────
  if [[ -n "$EC2_INSTANCE_ID" ]]; then
    step "1e. Attaching IAM profile to EC2 instance ${EC2_INSTANCE_ID}"
    CURRENT=$(aws ec2 describe-iam-instance-profile-associations \
      --filters "Name=instance-id,Values=${EC2_INSTANCE_ID}" \
      --region "${AWS_REGION}" \
      --query 'IamInstanceProfileAssociations[0].AssociationId' \
      --output text 2>/dev/null || echo "None")

    if [[ "$CURRENT" == "None" || -z "$CURRENT" ]]; then
      aws ec2 associate-iam-instance-profile \
        --instance-id "${EC2_INSTANCE_ID}" \
        --iam-instance-profile Name="${PROFILE_NAME}" \
        --region "${AWS_REGION}" >/dev/null
      ok "IAM role attached to EC2 instance"
    else
      info "EC2 already has an IAM profile (${CURRENT}) — skipping"
    fi
  else
    warn "EC2_INSTANCE_ID not set — skipping role attachment. Set it in this script and re-run."
  fi

  # ── 1f. Install Docker on EC2 (if needed) ────────────────────────────────
  if [[ -n "$EC2_INSTANCE_ID" ]]; then
    EC2_PUBLIC_IP=$(aws ec2 describe-instances \
      --instance-ids "${EC2_INSTANCE_ID}" \
      --region "${AWS_REGION}" \
      --query 'Reservations[0].Instances[0].PublicIpAddress' \
      --output text)
    info "EC2 public IP: ${EC2_PUBLIC_IP}"
    info "To install Docker on EC2, SSH in and run:"
    echo ""
    echo "  ssh ubuntu@${EC2_PUBLIC_IP} 'bash -s' << 'EOF'"
    echo "  sudo apt-get update -q"
    echo "  sudo apt-get install -y docker.io awscli"
    echo "  sudo systemctl enable docker"
    echo "  sudo usermod -aG docker ubuntu"
    echo "  EOF"
    echo ""
  fi

  # ── Print GitHub secrets to add ───────────────────────────────────────────
  step "GitHub Secrets — add these to your repo Settings → Secrets → Actions"
  echo ""
  echo "  AWS_ACCOUNT_ID      = ${ACCOUNT_ID}"
  echo "  AWS_ACCESS_KEY_ID   = <your GitHub-deploy IAM user access key>"
  echo "  AWS_SECRET_ACCESS_KEY = <your GitHub-deploy IAM user secret key>"
  echo "  EC2_HOST            = ${EC2_PUBLIC_IP:-<your-ec2-public-ip>}"
  echo "  EC2_USER            = ubuntu"
  echo "  EC2_SSH_KEY         = <paste contents of your .pem key file>"
  echo ""
  ok "Day 1 complete ✓"
}


# ═════════════════════════════ DAY 2 ══════════════════════════════════════════
day2() {
  step "DAY 2 — CloudFront + ACM  (WAF deferred → Demo Day Aug 13)"
  info "WAF skipped for Jul 9 prototype — saves \$7/month. Re-add before Demo Day by running: ./bootstrap-aws.sh add-waf"

  ACCOUNT_ID=$(get_account_id)

  # ── 2a. ACM Certificate ───────────────────────────────────────────────────
  # ACM certs used by CloudFront MUST be in us-east-1
  step "2a. Requesting ACM certificate (us-east-1 — required for CloudFront)"

  if [[ -z "$DOMAIN" ]]; then
    warn "DOMAIN not set — skipping ACM cert. Set DOMAIN=wealthseva.yourdomain.com in the script."
    info "You can still use the CloudFront *.cloudfront.net domain for the demo."
    CERT_ARN=""
  else
    EXISTING_CERT=$(aws acm list-certificates \
      --region us-east-1 \
      --query "CertificateSummaryList[?DomainName=='${DOMAIN}'].CertificateArn | [0]" \
      --output text 2>/dev/null || echo "None")

    if [[ "$EXISTING_CERT" != "None" && -n "$EXISTING_CERT" ]]; then
      CERT_ARN="$EXISTING_CERT"
      info "Certificate already exists: ${CERT_ARN}"
    else
      CERT_ARN=$(aws acm request-certificate \
        --domain-name "${DOMAIN}" \
        --subject-alternative-names "www.${DOMAIN}" \
        --validation-method DNS \
        --region us-east-1 \
        --query CertificateArn --output text)
      ok "Certificate requested: ${CERT_ARN}"
      warn "⚠️  DNS validation required! Go to ACM Console (us-east-1) → add the CNAME record to your DNS."
      warn "   CloudFront creation will fail until cert is ISSUED. Re-run day2 after validation."
    fi
  fi

  # ── 2b. WAF — DEFERRED to Demo Day (Aug 13) ──────────────────────────────
  # Saves $7/month for the Jul 9 prototype. The fastapi slowapi rate limiter
  # (30 req/min) provides basic protection. Re-add before Demo Day:
  #   ./bootstrap-aws.sh add-waf
  WAF_ACL_ARN=""

  # ── 2c. CloudFront Distribution ───────────────────────────────────────────
  step "2b. Creating CloudFront distribution (no WAF for prototype)"

  # Get EC2 public IP
  if [[ -n "$EC2_INSTANCE_ID" ]]; then
    EC2_PUBLIC_IP=$(aws ec2 describe-instances \
      --instance-ids "${EC2_INSTANCE_ID}" \
      --region "${AWS_REGION}" \
      --query 'Reservations[0].Instances[0].PublicIpAddress' \
      --output text)
  else
    warn "EC2_INSTANCE_ID not set — you'll need to add the EC2 origin manually in the console."
    EC2_PUBLIC_IP="YOUR_EC2_PUBLIC_IP"
  fi

  EXISTING_CF=$(aws cloudfront list-distributions \
    --query "DistributionList.Items[?Comment=='wealthseva-prototype'].Id | [0]" \
    --output text 2>/dev/null || echo "None")

  if [[ "$EXISTING_CF" != "None" && -n "$EXISTING_CF" ]]; then
    CF_DOMAIN=$(aws cloudfront get-distribution \
      --id "$EXISTING_CF" \
      --query 'Distribution.DomainName' --output text)
    info "CloudFront already exists (${EXISTING_CF}): https://${CF_DOMAIN}"
  else
    # Build distribution config — no WAF for Jul 9 prototype
    CF_CONFIG=$(jq -n \
      --arg ec2_ip "$EC2_PUBLIC_IP" \
      --arg cert_arn "${CERT_ARN:-}" \
      --arg domain "${DOMAIN:-}" \
      '{
        "Comment": "wealthseva-prototype",
        "DefaultCacheBehavior": {
          "TargetOriginId": "EC2Backend",
          "ViewerProtocolPolicy": "redirect-to-https",
          "CachePolicyId": "4135ea2d-6df8-44a3-9df3-4b5a84be39ad",
          "OriginRequestPolicyId": "b689b0a8-53d0-40ab-baf2-68738e2966ac",
          "AllowedMethods": {
            "Quantity": 7,
            "Items": ["GET","HEAD","OPTIONS","PUT","POST","PATCH","DELETE"],
            "CachedMethods": {"Quantity": 2, "Items": ["GET","HEAD"]}
          },
          "Compress": true
        },
        "Origins": {
          "Quantity": 1,
          "Items": [{
            "Id": "EC2Backend",
            "DomainName": $ec2_ip,
            "CustomOriginConfig": {
              "HTTPPort": 8000,
              "HTTPSPort": 443,
              "OriginProtocolPolicy": "http-only"
            }
          }]
        },
        "Enabled": true,
        "HttpVersion": "http2",
        "PriceClass": "PriceClass_200",
        "ViewerCertificate": (
          if $cert_arn != "" then {
            "ACMCertificateArn": $cert_arn,
            "SSLSupportMethod": "sni-only",
            "MinimumProtocolVersion": "TLSv1.2_2021"
          } else {
            "CloudFrontDefaultCertificate": true
          } end
        )
      }')

    CF_ID=$(aws cloudfront create-distribution \
      --distribution-config "${CF_CONFIG}" \
      --query 'Distribution.Id' --output text 2>/dev/null || echo "")

    if [[ -n "$CF_ID" ]]; then
      CF_DOMAIN=$(aws cloudfront get-distribution \
        --id "$CF_ID" \
        --query 'Distribution.DomainName' --output text)
      ok "CloudFront distribution created: ${CF_ID}"
      ok "CloudFront URL: https://${CF_DOMAIN}"
      echo ""
      info "Add this as a GitHub Actions variable (not secret):"
      echo "  CLOUDFRONT_URL = https://${CF_DOMAIN}"
    else
      warn "CloudFront creation requires more config — use the console for the initial setup."
      warn "See the Day 2 checklist in the README."
    fi
  fi

  ok "Day 2 complete ✓"
}


# ═════════════════════════════ DAY 3 ══════════════════════════════════════════
day3() {
  step "DAY 3 — AWS Amplify (Frontend — replaces Vercel)"

  info "Amplify is best connected via the console for initial GitHub OAuth setup."
  info "Follow these steps:"
  echo ""
  echo "  1. Open: https://ap-south-1.console.aws.amazon.com/amplify"
  echo "  2. Click 'New app' → 'Host web app'"
  echo "  3. Connect GitHub → select repo: ${GITHUB_REPO}"
  echo "  4. Branch: main  |  App root: frontend/"
  echo "  5. Build settings (auto-detected for Next.js 14):"
  echo "       Build command:  npm ci && npm run build"
  echo "       Output dir:     .next"
  echo "  6. Environment variables — add these in Amplify Console:"
  echo "       NEXT_PUBLIC_BACKEND_URL  = https://<your-cloudfront-domain>"
  echo "       NEXT_PUBLIC_SUPABASE_URL = <supabase project url>"
  echo "       NEXT_PUBLIC_SUPABASE_ANON_KEY = <supabase anon key>"
  echo ""

  # Create Amplify app via CLI (optional — GitHub OAuth token needed)
  AMPLIFY_APP_NAME="${APP_NAME}-frontend"
  EXISTING=$(aws amplify list-apps \
    --region "${AWS_REGION}" \
    --query "apps[?name=='${AMPLIFY_APP_NAME}'].appId | [0]" \
    --output text 2>/dev/null || echo "None")

  if [[ "$EXISTING" != "None" && -n "$EXISTING" ]]; then
    AMPLIFY_URL=$(aws amplify get-app \
      --app-id "$EXISTING" \
      --region "${AWS_REGION}" \
      --query 'app.defaultDomain' --output text)
    info "Amplify app already exists (${EXISTING}): https://main.${AMPLIFY_URL}"
  else
    info "Creating Amplify app skeleton (you still need to connect GitHub in the console)"
    AMPLIFY_APP_ID=$(aws amplify create-app \
      --name "${AMPLIFY_APP_NAME}" \
      --region "${AWS_REGION}" \
      --platform WEB_COMPUTE \
      --description "WealthSeva AI — Next.js 14 frontend" \
      --environment-variables "NEXT_PUBLIC_BACKEND_URL=https://PLACEHOLDER" \
      --query 'app.appId' --output text 2>/dev/null || echo "")

    if [[ -n "$AMPLIFY_APP_ID" ]]; then
      ok "Amplify app created: ${AMPLIFY_APP_ID}"
      info "Connect GitHub in the Amplify console → it will auto-deploy on every push."
    fi
  fi

  ok "Day 3 complete ✓"
}


# ═══════════════════ ADD-WAF (run before Demo Day Aug 13) ═════════════════════
add_waf() {
  step "ADD-WAF — attaching WAF to existing CloudFront distribution"
  info "Costs \$7/month once attached. Run this before Demo Day (Aug 13)."

  ACCOUNT_ID=$(get_account_id)
  WAF_ACL_NAME="${APP_NAME}-waf"

  # ── Create WAF Web ACL in us-east-1 (required for CloudFront scope)
  step "Creating WAF Web ACL (us-east-1)"
  EXISTING_WAF=$(aws wafv2 list-web-acls \
    --scope CLOUDFRONT \
    --region us-east-1 \
    --query "WebACLs[?Name=='${WAF_ACL_NAME}'].ARN | [0]" \
    --output text 2>/dev/null || echo "None")

  if [[ "$EXISTING_WAF" != "None" && -n "$EXISTING_WAF" ]]; then
    WAF_ACL_ARN="$EXISTING_WAF"
    info "WAF ACL already exists: ${WAF_ACL_ARN}"
  else
    WAF_ACL_ARN=$(aws wafv2 create-web-acl \
      --name "${WAF_ACL_NAME}" \
      --scope CLOUDFRONT \
      --region us-east-1 \
      --default-action Allow={} \
      --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName="${APP_NAME}WAF" \
      --rules '[
        {
          "Name": "AWSManagedRulesCommonRuleSet",
          "Priority": 1,
          "OverrideAction": {"None": {}},
          "Statement": {"ManagedRuleGroupStatement": {"VendorName": "AWS","Name": "AWSManagedRulesCommonRuleSet"}},
          "VisibilityConfig": {"SampledRequestsEnabled": true,"CloudWatchMetricsEnabled": true,"MetricName": "CommonRuleSet"}
        },
        {
          "Name": "RateLimitRule",
          "Priority": 2,
          "Action": {"Block": {}},
          "Statement": {"RateBasedStatement": {"Limit": 100,"AggregateKeyType": "IP"}},
          "VisibilityConfig": {"SampledRequestsEnabled": true,"CloudWatchMetricsEnabled": true,"MetricName": "RateLimit"}
        }
      ]' \
      --query 'Summary.ARN' --output text)
    ok "WAF ACL created: ${WAF_ACL_ARN}"
  fi

  # ── Find the CloudFront distribution
  CF_ID=$(aws cloudfront list-distributions \
    --query "DistributionList.Items[?Comment=='wealthseva-prototype'].Id | [0]" \
    --output text 2>/dev/null || echo "None")

  if [[ "$CF_ID" == "None" || -z "$CF_ID" ]]; then
    die "CloudFront distribution not found. Run day2 first."
  fi

  # ── Get current ETag (required for update)
  CF_ETAG=$(aws cloudfront get-distribution-config \
    --id "$CF_ID" \
    --query 'ETag' --output text)

  # ── Get current config, inject WebACLId, update
  aws cloudfront get-distribution-config --id "$CF_ID" \
    --query 'DistributionConfig' \
  | jq --arg waf "$WAF_ACL_ARN" '. + {"WebACLId": $waf}' \
  > /tmp/cf-config-with-waf.json

  aws cloudfront update-distribution \
    --id "$CF_ID" \
    --if-match "$CF_ETAG" \
    --distribution-config "file:///tmp/cf-config-with-waf.json" >/dev/null

  rm -f /tmp/cf-config-with-waf.json
  ok "WAF attached to CloudFront distribution ${CF_ID}"
  info "WAF takes ~5 minutes to propagate globally."
}


# ═════════════════════════════ MAIN ═══════════════════════════════════════════
main() {
  check_prereqs
  echo ""
  echo "╔══════════════════════════════════════════════════════════════╗"
  echo "║   WealthSeva AI — Prototype AWS Bootstrap  (Jul 9 deadline)  ║"
  echo "╚══════════════════════════════════════════════════════════════╝"

  case "${1:-all}" in
    day1) day1 ;;
    day2) day2 ;;
    day3) day3 ;;
    add-waf) add_waf ;;
    all)
      day1
      echo ""
      read -rp "  Ready to continue with Day 2? (CloudFront + ACM) [y/N] " CONT
      [[ "$CONT" =~ ^[Yy]$ ]] && day2
      echo ""
      read -rp "  Ready to continue with Day 3? (Amplify) [y/N] " CONT
      [[ "$CONT" =~ ^[Yy]$ ]] && day3
      ;;
    *)
      echo "Usage: $0 [day1|day2|day3|all|add-waf]"
      echo "  add-waf  — attach WAF to existing CloudFront distribution (run before Demo Day)"
      exit 1
      ;;
  esac

  echo ""
  echo "╔══════════════════════════════════════════════════════════════╗"
  echo "║   All done! Push to main to trigger the new CI/CD pipeline.  ║"
  echo "╚══════════════════════════════════════════════════════════════╝"
}

main "${@:-all}"
