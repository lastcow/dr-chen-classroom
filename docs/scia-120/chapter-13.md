---
title: "Cloud Computing Security"
week: 13
chapter: 13
course: SCIA-120
---

# Chapter 13: Cloud Computing Security

## Introduction

Cloud computing has fundamentally transformed how organizations build, deploy, and manage information systems. What once required months of procurement, physical hardware installation, and data center operations now takes minutes — and can be provisioned, scaled, or decommissioned through an API call or a web console. Amazon Web Services (AWS), Microsoft Azure, and Google Cloud Platform (GCP) collectively host the workloads of the world's most critical organizations: governments, hospitals, financial institutions, and the applications used by billions of people daily.

This shift in infrastructure brings enormous operational benefits but also introduces new and subtle security risks. The attack surface changes in fundamental ways: instead of physical servers in locked data centers managed entirely by the organization, cloud resources exist in shared environments, configured through self-service APIs, accessible from anywhere on the internet, and billed per use. Security mistakes that would have been noticed when ordering hardware now manifest silently — a single misconfiguration can expose millions of records to the public internet within seconds.

This chapter examines cloud security from the ground up: the service and deployment models, the division of security responsibility, the most significant risks and real-world breaches, and the technical controls that enable secure cloud operations.

---

## 13.1 Cloud Service Models

Cloud services are typically classified into three models, which differ in what the cloud provider manages versus what the customer is responsible for:

### 13.1.1 Infrastructure as a Service (IaaS)

IaaS provides virtualized computing infrastructure: virtual machines, block storage volumes, virtual networks, and load balancers. The customer provisions and manages operating systems, middleware, applications, and data. The provider manages the physical hardware, hypervisor, and data center infrastructure.

Examples: AWS EC2, Azure Virtual Machines, Google Compute Engine, AWS S3 (object storage), Azure Blob Storage.

In IaaS, the customer has the most control and the most security responsibility. They are responsible for patching the OS, securing the network configuration, managing identities and access, and protecting their applications.

### 13.1.2 Platform as a Service (PaaS)

PaaS provides a managed platform for deploying applications, abstracting away OS management, runtime maintenance, and infrastructure scaling. The customer deploys their application code and data; the provider manages everything below: the OS, runtime, middleware, and infrastructure.

Examples: AWS Elastic Beanstalk, Azure App Service, Google App Engine, AWS RDS (managed database), Heroku.

PaaS shifts significant security responsibility to the provider — the customer no longer patches the OS or manages the runtime. However, the customer remains responsible for application code security, data protection, and access management.

### 13.1.3 Software as a Service (SaaS)

SaaS delivers complete applications over the internet. The customer simply uses the application; the provider manages everything: infrastructure, platform, application, and runtime.

Examples: Microsoft 365, Google Workspace, Salesforce, Workday, Slack, Zoom.

In SaaS, the provider manages nearly all security. The customer's responsibilities narrow to: user identity management (who has accounts, what permissions they have), data governance (what data is stored and shared), and configuration security (ensuring secure application settings).

---

## 13.2 The Shared Responsibility Model

The *shared responsibility model* is the most important concept in cloud security. It defines the boundary between what the cloud provider secures and what the customer must secure. This boundary shifts depending on the service model.

> **Key Concept — Shared Responsibility**: The cloud provider is responsible for the *security of* the cloud (physical infrastructure, hardware, hypervisors, managed service platforms). The customer is responsible for *security in* the cloud (what they deploy, how they configure it, who they give access to).

A common — and dangerous — misconception is that migrating to the cloud transfers security responsibility to the provider. It does not. The provider secures the foundation; the customer is still responsible for everything they build on it.

| Responsibility | IaaS | PaaS | SaaS |
|---|---|---|---|
| Physical security | Provider | Provider | Provider |
| Hardware / hypervisor | Provider | Provider | Provider |
| Network infrastructure | Provider | Provider | Provider |
| Operating system | **Customer** | Provider | Provider |
| Runtime / middleware | **Customer** | Provider | Provider |
| Application | **Customer** | **Customer** | Provider |
| Data encryption | **Customer** | **Customer** | Shared |
| Identity & access management | **Customer** | **Customer** | **Customer** |
| Network configuration (VPC, firewall rules) | **Customer** | **Customer** | N/A |

Real-world breaches frequently result from customers failing to understand or fulfill their responsibilities. The Capital One breach (2019) exploited a misconfigured WAF and overly permissive IAM role — both customer-side responsibilities — not a failure of AWS's underlying infrastructure security.

---

## 13.3 Cloud Deployment Models

Organizations deploy cloud resources in several ways:

**Public Cloud**: Resources are provisioned on infrastructure shared with other cloud tenants (logical isolation, not physical). This is the model offered by AWS, Azure, and GCP. Cost-efficient and highly scalable, but subject to the shared responsibility model.

**Private Cloud**: Cloud infrastructure dedicated exclusively to one organization, either hosted on-premises (using platforms like OpenStack or VMware vSphere) or dedicated-tenancy resources leased from a public cloud provider. Provides greater control and isolation but at significantly higher cost and operational complexity.

**Hybrid Cloud**: A combination of on-premises or private cloud resources connected to public cloud services. Organizations often use hybrid cloud for regulatory compliance (keeping sensitive data on-premises), disaster recovery, or to extend existing investments. Security in hybrid environments must address connectivity security (VPN or dedicated links like AWS Direct Connect), consistent identity management, and security policy consistency.

**Multi-Cloud**: Using services from multiple public cloud providers to avoid vendor lock-in, improve resilience, or optimize cost. Multi-cloud introduces operational complexity: each provider has different security services, IAM models, and network configurations. Consistent security posture across providers requires abstraction layers and strong governance.

---

## 13.4 Cloud Security Risks

### 13.4.1 Misconfiguration

Misconfiguration is the leading cause of cloud data breaches. The most notorious example is publicly accessible Amazon S3 buckets. By default, S3 buckets are private, but a single misconfigured access control policy or a "Block Public Access" setting being disabled can expose all bucket contents to the entire internet — with no authentication required.

Between 2017 and 2020, hundreds of organizations inadvertently exposed billions of records through misconfigured S3 buckets, including government agencies, major corporations, and healthcare providers. Beyond S3, common misconfigurations include:

- Security groups with overly permissive inbound rules (e.g., `0.0.0.0/0` on port 22 or 3389, allowing SSH/RDP from anywhere)
- Database instances with public endpoints and no network access controls
- Cloud storage buckets with public access enabled
- APIs deployed without authentication
- Logging and monitoring disabled
- Default credentials left unchanged on managed services

**Infrastructure as Code (IaC) security** addresses misconfiguration by treating infrastructure configuration (Terraform, CloudFormation, Pulumi) as code subject to security scanning and review. Tools like Checkov, tfsec, and AWS Config detect misconfigurations before or after deployment.

### 13.4.2 Insecure APIs

Cloud management APIs (AWS API, Azure ARM, GCP API) are powerful attack surfaces. Every action that can be performed in a cloud console can also be performed via API, with no security control beyond valid credentials. API keys and access tokens that are leaked — in source code, in log files, in GitHub repositories — grant full access to cloud resources.

### 13.4.3 Account Hijacking

Cloud accounts represent the highest-value credential in modern attack campaigns. Compromising cloud credentials (IAM user access keys, federated identity credentials, or management console passwords) can grant access to all resources in an account. Phishing campaigns specifically targeting DevOps engineers and cloud administrators are common. MFA is essential for all cloud console access.

### 13.4.4 Data Breaches and Insider Threats

Sensitive data stored in cloud environments — customer PII, intellectual property, regulated data — can be exfiltrated by external attackers who compromise access credentials or by malicious or negligent insiders who abuse their legitimate access. Encryption, data loss prevention (DLP) controls, and detailed access logging are essential countermeasures.

### 13.4.5 Shadow IT

Shadow IT refers to cloud resources provisioned by employees or teams without the knowledge or approval of IT and security teams. When individual developers spin up EC2 instances, S3 buckets, or SaaS subscriptions outside formal procurement processes, those resources may bypass security controls, not be inventoried, and not be monitored. Cloud Access Security Brokers (CASBs) and cloud security posture management (CSPM) tools help detect and govern shadow IT.

---

## 13.5 Cloud Identity and Access Management

### 13.5.1 AWS IAM

AWS Identity and Access Management (IAM) is the access control system for all AWS services. Key components:

- **Users**: Long-term identities for humans or applications. Best practice: minimize IAM users; use roles instead.
- **Groups**: Collections of users sharing the same policies.
- **Roles**: Identities assumed temporarily by services, applications, or federated users. Roles have no long-term credentials; they issue temporary access tokens via the Security Token Service (STS). Using roles for EC2 instances and Lambda functions (instead of embedding access keys) is a fundamental security best practice.
- **Policies**: JSON documents defining allowed or denied actions on specific resources. Policies follow an explicit deny, implicit deny, then allow evaluation logic: all requests are denied by default; an allow must be explicitly granted; an explicit deny always overrides allows.

The *principle of least privilege* is critical in AWS IAM: policies should grant only the specific actions on specific resources needed for a function, not broad wildcards (`*`). Overly permissive policies are a root cause of many cloud breaches.

### 13.5.2 Azure Active Directory

Azure Active Directory (Azure AD, now called Microsoft Entra ID) serves as the identity foundation for Azure, Microsoft 365, and integrated third-party SaaS applications. It provides:

- User and group management
- Conditional Access policies (grant access based on user, device, location, and risk signals)
- Privileged Identity Management (PIM) for just-in-time role elevation
- Identity Protection (detecting risky sign-ins and compromised credentials)
- SAML/OIDC/OAuth2 federation with thousands of third-party applications

---

## 13.6 Encryption in the Cloud

**Encryption at Rest**: Data stored in cloud services (S3, RDS, EBS volumes, Azure Blob Storage) should be encrypted at rest. AWS, Azure, and GCP all offer default encryption with provider-managed keys, but organizations requiring greater control use customer-managed keys (CMKs) via Key Management Services.

**Encryption in Transit**: All data transmitted between clients and cloud services, and between cloud services internally, should use TLS 1.2 or 1.3. Most cloud services enforce this by default, but it must be explicitly required for legacy protocols and internal service communication.

**Key Management Services (KMS)**: AWS KMS, Azure Key Vault, and GCP Cloud KMS provide centralized, audited management of cryptographic keys. Keys stored in KMS never leave the service in plaintext — all cryptographic operations are performed inside the KMS hardware security modules (HSMs). Key policies control which identities can use which keys, providing an additional layer of access control for encrypted data.

> **Warning**: Encryption at rest protects data from physical media theft or unauthorized data center access. It does *not* protect against a compromised application with legitimate decryption access, or against an IAM misconfiguration that grants excessive access. Encryption is one layer of a defense-in-depth strategy.

---

## 13.7 Cloud Network Security

### 13.7.1 Virtual Private Cloud (VPC)

A *Virtual Private Cloud* (VPC) is an isolated virtual network within a cloud provider's infrastructure. Organizations deploy their cloud resources within VPCs, controlling IP address ranges (CIDR blocks), subnets, route tables, and network gateways. Proper VPC design involves:

- **Public subnets**: For resources that need direct internet access (load balancers, NAT gateways, bastion hosts).
- **Private subnets**: For resources that should not be directly accessible from the internet (application servers, databases, internal services).
- **Multiple availability zones**: Distributing resources across AZs for resilience.

### 13.7.2 Security Groups and NACLs

**Security Groups** are stateful virtual firewalls attached to individual resources (EC2 instances, RDS databases, Lambda functions). They filter traffic based on protocol, port, and source/destination IP or security group. Because security groups are stateful, return traffic is automatically allowed for permitted inbound connections.

**Network Access Control Lists (NACLs)** are stateless firewall rules applied at the subnet level. Unlike security groups, NACLs must explicitly allow return traffic. NACLs are evaluated before security groups and are useful for broad network-level blocking (e.g., blocking known malicious IP ranges).

---

## 13.8 Cloud Security Monitoring

### 13.8.1 AWS CloudTrail and CloudWatch

**AWS CloudTrail** records all API calls made in an AWS account — who made the call, from where, at what time, and what was the result. CloudTrail is the essential audit log for AWS and must be enabled in all regions, with logs protected from tampering (S3 bucket with Object Lock or delivered to a separate security account). CloudTrail enables detection of: unauthorized access attempts, privilege escalation, IAM changes, data exfiltration via unusual data transfer, and cryptomining via unauthorized EC2 instance launches.

**Amazon CloudWatch** monitors resource metrics and application logs, and can trigger alarms and automated responses. CloudWatch Logs Insights allows querying log data at scale. AWS Security Hub aggregates findings from multiple AWS security services (GuardDuty, Macie, Config, Inspector) into a unified view.

**Amazon GuardDuty** is a managed threat detection service that analyzes CloudTrail, VPC Flow Logs, and DNS logs using ML and threat intelligence to detect suspicious activity: cryptocurrency mining, credential exfiltration, communication with known command-and-control servers, and unusual API activity.

### 13.8.2 Azure Monitor and Microsoft Defender for Cloud

Azure Monitor collects metrics and logs from Azure resources and applications. Microsoft Defender for Cloud (formerly Azure Security Center) provides continuous security assessment, threat detection, and recommendations for Azure resources. Azure Sentinel (Microsoft Sentinel) is a SIEM and SOAR platform natively integrated with Azure and Microsoft 365.

---

## 13.9 Cloud Compliance

Organizations in regulated industries must ensure their cloud deployments meet applicable compliance requirements:

- **SOC 2 (Service Organization Control 2)**: An auditing standard for service organizations, assessing security, availability, processing integrity, confidentiality, and privacy controls. Cloud providers publish SOC 2 Type II reports; customers must also achieve their own SOC 2 compliance for their cloud-hosted services.

- **FedRAMP (Federal Risk and Authorization Management Program)**: A U.S. government program standardizing security assessment and authorization for cloud services used by federal agencies. AWS GovCloud, Azure Government, and GCP Government Cloud offer FedRAMP-authorized environments.

- **GDPR (General Data Protection Regulation)**: The EU's comprehensive data protection regulation requires careful attention to data residency (where personal data is stored and processed), data transfer mechanisms (for data leaving the EU), processor agreements (cloud providers are data processors), and breach notification (72-hour notification to supervisory authorities).

- **HIPAA (Health Insurance Portability and Accountability Act)**: Requires that protected health information (PHI) be secured. AWS, Azure, and GCP offer HIPAA-eligible services and will sign Business Associate Agreements (BAAs). However, HIPAA compliance remains the customer's responsibility in the shared responsibility model.

- **PCI-DSS (Payment Card Industry Data Security Standard)**: Governs how cardholder data is stored, processed, and transmitted. Cloud deployments handling payment data must achieve PCI-DSS compliance and carefully scope the cardholder data environment (CDE) within their cloud architecture.

---

## 13.10 Cloud Access Security Broker (CASB)

A *Cloud Access Security Broker* (CASB) is a security policy enforcement point between users and cloud services, providing visibility and control over cloud usage. CASBs address:

- **Shadow IT discovery**: Identifying what cloud services employees are using, even outside officially approved applications.
- **Data loss prevention**: Preventing sensitive data from being uploaded to unauthorized cloud services or shared publicly.
- **Threat protection**: Detecting compromised accounts and insider threats in cloud applications.
- **Compliance**: Enforcing data governance policies across cloud services.

CASB solutions (Microsoft Defender for Cloud Apps, Netskope, Zscaler) deploy either as API-based integrations (connecting directly to cloud service APIs) or as inline proxies (routing cloud traffic through the CASB for inspection).

---

## 13.11 Serverless Security

*Serverless* computing (AWS Lambda, Azure Functions, GCP Cloud Functions) allows running code without managing servers. Functions are triggered by events and execute in ephemeral, provider-managed environments. Serverless shifts even more security responsibility to the provider, but introduces new concerns:

- **Function permissions**: Each function needs an IAM role; over-permissive roles are a common issue. Functions should follow least privilege — a Lambda processing S3 events should only have permissions to read from that specific bucket.
- **Event injection**: Functions that process untrusted event data (from API Gateway, SQS, SNS, S3 events) must validate and sanitize inputs, as event data may contain injection payloads.
- **Dependency vulnerabilities**: Serverless functions package application code and dependencies; vulnerable packages in function packages create risk. Regular dependency scanning is essential.
- **Logging and monitoring**: Serverless functions can be difficult to monitor due to their ephemeral nature. AWS X-Ray and CloudWatch Logs are essential for observability.

---

## 13.12 Cloud Penetration Testing

Cloud penetration testing differs significantly from traditional penetration testing:

- **Permission requirements**: Major cloud providers (AWS, Azure, GCP) require customers to notify them before conducting penetration tests against their cloud environments, and testing is restricted to the customer's own resources.
- **Attack surface**: Cloud pen tests focus on IAM misconfiguration, exposed APIs, S3 bucket enumeration, metadata service exploitation (IMDS), privilege escalation through IAM roles, and network configuration weaknesses.
- **Instance metadata service (IMDS) exploitation**: EC2 instances have access to a metadata service (at `169.254.169.254`) that can return IAM credentials for the attached role. SSRF vulnerabilities in applications on EC2 can be exploited to steal these credentials. IMDSv2, which requires a token exchange before accessing metadata, mitigates this risk.

---

## 13.13 Real-World Cloud Breaches

### Capital One Data Breach (2019)

In July 2019, Capital One disclosed that approximately 100 million customer records were stolen from its AWS environment. The attacker, a former AWS employee, exploited a misconfigured Web Application Firewall (WAF) running on an EC2 instance to perform a Server-Side Request Forgery (SSRF) attack. The SSRF request was directed to the EC2 instance metadata service (IMDS), which returned temporary AWS credentials for the overly permissive IAM role attached to the WAF instance. Using those credentials, the attacker listed and exfiltrated data from over 700 S3 buckets containing Capital One customer data.

Key lessons: WAF configuration errors are security-critical. IAM roles should follow least privilege — the WAF role should not have had S3 read access across 700 buckets. IMDSv2 should be enforced to require token-based IMDS access, blocking simple SSRF exploitation. CloudTrail should have alerted on the massive S3 `GetObject` activity.

### Twitch Data Breach (2021)

In October 2021, an anonymous actor leaked over 125 GB of Twitch data, including source code, internal tools, creator payout information, and proprietary cryptographic secrets. The breach reportedly resulted from a server misconfiguration that allowed unauthorized access to internal Git repositories. The incident highlighted risks around internal access controls, least privilege for internal systems, and the exposure of cryptographic material in source code and build systems.

---

## Key Terms

- **IaaS (Infrastructure as a Service)**: Cloud model providing virtualized compute, storage, and networking; customer manages OS and above.
- **PaaS (Platform as a Service)**: Cloud model providing a managed application platform; customer manages application and data.
- **SaaS (Software as a Service)**: Cloud model delivering complete applications; provider manages everything.
- **Shared Responsibility Model**: Framework defining security responsibilities between cloud provider and customer.
- **VPC (Virtual Private Cloud)**: An isolated virtual network within a cloud provider's infrastructure.
- **Security Group**: A stateful virtual firewall controlling traffic to individual cloud resources.
- **NACL (Network Access Control List)**: A stateless firewall applied at the subnet level in a cloud VPC.
- **AWS IAM**: AWS's identity and access management service for controlling access to AWS resources.
- **IAM Role**: A temporary identity in AWS that can be assumed by services or applications, issuing short-lived credentials.
- **KMS (Key Management Service)**: A cloud service for creating, managing, and auditing cryptographic keys.
- **S3 (Simple Storage Service)**: AWS's object storage service; a common source of cloud misconfiguration breaches.
- **CloudTrail**: AWS service recording all API calls in an account for auditing and security analysis.
- **GuardDuty**: AWS managed threat detection service using ML to analyze CloudTrail, VPC Flow Logs, and DNS logs.
- **CASB (Cloud Access Security Broker)**: A security enforcement point providing visibility and control over cloud service usage.
- **Shadow IT**: Cloud resources or services provisioned by employees outside formal IT governance processes.
- **Serverless**: A cloud execution model where provider manages server infrastructure; code runs in ephemeral functions.
- **IMDS (Instance Metadata Service)**: An EC2 service providing instance configuration and temporary credentials; exploitable via SSRF.
- **SSRF (Server-Side Request Forgery)**: A vulnerability where an application can be tricked into making HTTP requests to unintended targets.
- **FedRAMP**: A U.S. government program authorizing cloud services for federal agency use.
- **SOC 2**: An auditing standard for service organization security controls.

---

## Review Questions

1. Explain the shared responsibility model in cloud computing. Using a specific example (e.g., a web application running on AWS EC2), describe which security responsibilities belong to the cloud provider and which belong to the customer.

2. A developer accidentally enables public access on an S3 bucket containing customer records. Describe the specific AWS configuration steps that would have prevented this, and what monitoring controls would detect it.

3. Compare IaaS, PaaS, and SaaS in terms of the customer's security responsibilities. Why might an organization choose PaaS over IaaS for a new application, and what security risks might they need to accept or manage differently?

4. The Capital One breach exploited a combination of an SSRF vulnerability and an overly permissive IAM role. Explain the attack chain step by step and identify at least three points where better security controls could have prevented or limited the breach.

5. What is an IAM role in AWS, and why is it considered more secure than using IAM user access keys for EC2 applications? What is the risk if the IAM role is over-permissive?

6. Explain what a CASB is and describe two specific use cases where a CASB provides security value that cannot be achieved with endpoint or network controls alone.

7. An organization is deploying a healthcare application on Azure that processes Protected Health Information (PHI). What HIPAA compliance responsibilities remain with the customer in a PaaS deployment model? What Azure-specific controls should be implemented?

8. Describe how AWS CloudTrail and Amazon GuardDuty work together to detect a potential account compromise. What specific indicators might GuardDuty surface, and how would a security analyst use CloudTrail to investigate?

9. What is the EC2 Instance Metadata Service (IMDS), and how does an SSRF vulnerability enable its exploitation? How does IMDSv2 mitigate this risk?

10. What is "shadow IT" in the cloud context, and why is it a security concern? What technical and organizational controls can an organization use to manage it?

---

## Further Reading

- Amazon Web Services. (2023). *AWS Security Documentation*. https://docs.aws.amazon.com/security/

- Cloud Security Alliance. (2022). *Cloud Controls Matrix v4*. https://cloudsecurityalliance.org/research/cloud-controls-matrix/

- Policymakers' Guide to Cloud Security. (2021). National Cybersecurity Alliance. https://staysafeonline.org/

- Krebs, B. (2019). *What We Can Learn from the Capital One Hack*. KrebsOnSecurity. https://krebsonsecurity.com/2019/08/what-we-can-learn-from-the-capital-one-hack/

- Raza, T., & Al-Shaer, E. (2021). Cloud security posture management and misconfiguration remediation. *IEEE Security & Privacy*, 19(5), 60–67.
