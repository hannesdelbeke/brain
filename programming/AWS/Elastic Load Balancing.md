# Elastic Load Balancing
Elastic Load Balancing (ELB) automatically distributes incoming application traffic across multiple
targets, such as Amazon EC2 instances, containers, and IP addresses. It can handle the varying load of
your application traffic in a single Availability Zone or across multiple Availability Zones. Elastic Load
Balancing offers four types of load balancers that all feature the high availability, automatic scaling, and
robust security necessary to make your applications fault tolerant.
• Application Load Balancer is best suited for load balancing of HTTP and HTTPS traffic and provides
advanced request routing targeted at the delivery of modern application architectures, including microservices and containers. Operating at the individual request level (Layer 7), Application Load
Balancer routes traffic to targets within Amazon Virtual Private Cloud (Amazon VPC) based on the
content of the request.
• Network Load Balancer is best suited for load balancing of TCP traffic where extreme performance is
required. Operating at the connection level (Layer 4), Network Load Balancer routes traffic to targets
within Amazon Virtual Private Cloud (Amazon VPC) and is capable of handling millions of requests
per second while maintaining ultra-low latencies. Network Load Balancer is also optimized to handle
sudden and volatile traffic patterns.
• Gateway Load Balancer makes it easy to deploy, scale, and run third-party virtual networking
appliances. Providing load balancing and auto scaling for fleets of third-party appliances, Gateway
Load Balancer is transparent to the source and destination of traffic. This capability makes it well
suited for working with third-party appliances for security, network analytics, and other use cases.
• Classic Load Balancer provides basic load balancing across multiple Amazon EC2 instances and
operates at both the request level and connection level. Classic Load Balancer is intended for
applications that were built within the EC2-Classic network.