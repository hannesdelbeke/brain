# AWS Fargate
AWS Fargate is a compute engine for Amazon ECS that allows you to run containers without having to
manage servers or clusters. With AWS Fargate, you no longer have to provision, configure, and scale
clusters of virtual machines to run containers. This removes the need to choose server types, decide
when to scale your clusters, or optimize cluster packing. AWS Fargate removes the need for you to
interact with or think about servers or clusters. Fargate lets you focus on designing and building your
applications instead of managing the infrastructure that runs them.
Amazon ECS has two modes: Fargate launch type and EC2 launch type. With Fargate launch type, all
you have to do is package your application in containers, specify the CPU and memory requirements, define networking and IAM policies, and launch the application. EC2 launch type allows you to have
server-level, more granular control over the infrastructure that runs your container applications. With
EC2 launch type, you can use Amazon ECS to manage a cluster of servers and schedule placement
of containers on the servers. Amazon ECS keeps track of all the CPU, memory and other resources in
your cluster, and also finds the best server for a container to run on based on your specified resource
requirements. You are responsible for provisioning, patching, and scaling clusters of servers. You can
decide which type of server to use, which applications and how many containers to run in a cluster
to optimize utilization, and when you should add or remove servers from a cluster. EC2 launch type
gives you more control of your server clusters and provides a broader range of customization options,
which might be required to support some specific applications or possible compliance and government
requirements.