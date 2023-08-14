# Amazon EC2
Amazon Elastic Compute Cloud (Amazon EC2) is a web service that provides secure, resizable compute capacity in the cloud. It is designed to make web-scale computing easier for developers.
The simple web interface of Amazon EC2 allows you to obtain and configure capacity with minimal
friction. It provides you with complete control of your computing resources and lets you run on Amazon’s proven computing environment. Amazon EC2 reduces the time required to obtain and boot new server instances (called Amazon EC2 instances) to minutes, allowing you to quickly scale capacity, both up and down, as your computing requirements change. Amazon EC2 changes the economics of computing by allowing you to pay only for capacity that you actually use. Amazon EC2 provides developers and system administrators the tools to build failure resilient applications and isolate themselves from common failure scenarios.

[source](https://d0.awsstatic.com/whitepapers/aws-overview.pdf)

# Instance Types
Amazon EC2 passes on to you the financial benefits of Amazon’s scale. You pay a very low rate for the
compute capacity you actually consume. See Amazon EC2 Instance Purchasing Options for a more
detailed description.
• On-Demand Instances— With On-Demand instances, you pay for compute capacity by the hour or
the second depending on which instances you run. No longer-term commitments or upfront payments
are needed. You can increase or decrease your compute capacity depending on the demands of your
application and only pay the specified per hourly rates for the instance you use. On-Demand instances
are recommended for:
• Users that prefer the low cost and flexibility of Amazon EC2 without any up-front payment or longterm commitment
• Applications with short-term, spiky, or unpredictable workloads that cannot be interrupted
• Applications being developed or tested on Amazon EC2 for the first time
• Spot Instances—Spot Instances are available at up to a 90% discount compared to On-Demand
prices and let you take advantage of unused Amazon EC2 capacity in the AWS Cloud. You can
significantly reduce the cost of running your applications, grow your application’s compute capacity
and throughput for the same budget, and enable new types of cloud computing applications. Spot
instances are recommended for:
• Applications that have flexible start and end times
• Applications that are only feasible at very low compute prices
• Users with urgent computing needs for large amounts of additional capacity
• Reserved Instances—Reserved Instances provide you with a significant discount (up to 72%)
compared to On-Demand instance pricing. You have the flexibility to change families, operating
system types, and tenancies while benefitting from Reserved Instance pricing when you use
Convertible Reserved Instances.
• Savings Plans—Savings Plans are a flexible pricing model that offer low prices on EC2 and Fargate
usage, in exchange for a commitment to a consistent amount of usage (measured in $/hour) for a 1 or
3 year term.
• Dedicated Hosts—A Dedicated Host is a physical EC2 server dedicated for your use. Dedicated Hosts
can help you reduce costs by allowing you to use your existing server-bound software licenses,
including Windows Server, SQL Server, and SUSE Linux Enterprise Server (subject to your license
terms), and can also help you meet compliance requirements.


# Amazon EC2 Auto Scaling
Amazon EC2 Auto Scaling helps you maintain application availability and allows you to automatically
add or remove EC2 instances according to conditions you define. You can use the fleet management
features of Amazon EC2 Auto Scaling to maintain the health and availability of your fleet. You can also
use the dynamic and predictive scaling features of Amazon EC2 Auto Scaling to add or remove EC2
instances. Dynamic scaling responds to changing demand and predictive scaling automatically schedules
the right number of EC2 instances based on predicted demand. Dynamic scaling and predictive scaling
can be used together to scale faster.


# Amazon EC2 Image Builder
EC2 Image Builder simplifies the building, testing, and deployment of Virtual Machine and container
images for use on AWS or on-premises.
Keeping Virtual Machine and container images up-to-date can be time consuming, resource intensive,
and error-prone. Currently, customers either manually update and snapshot VMs or have teams that
build automation scripts to maintain images.


Image Builder significantly reduces the effort of keeping images up-to-date and secure by providing
a simple graphical interface, built-in automation, and AWS-provided security settings. With Image
Builder, there are no manual steps for updating an image nor do you have to build your own automation
pipeline.
Image Builder is offered at no cost, other than the cost of the underlying AWS resources used to create,
store, and share the images.
