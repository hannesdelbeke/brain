# AWS Transit Gateway
AWS Transit Gateway is a service that enables customers to connect their Amazon Virtual Private Clouds
(VPCs) and their on-premises networks to a single gateway. As you grow the number of workloads
running on AWS, you need to be able to scale your networks across multiple accounts and Amazon VPCs
to keep up with the growth. Today, you can connect pairs of Amazon VPCs using peering. However,
managing point-to-point connectivity across many Amazon VPCs, without the ability to centrally
manage the connectivity policies, can be operationally costly and cumbersome. For on-premises
connectivity, you need to attach your AWS VPN to each individual Amazon VPC. This solution can be time
consuming to build and hard to manage when the number of VPCs grows into the hundreds.
With AWS Transit Gateway, you only have to create and manage a single connection from the central
gateway in to each Amazon VPC, on-premises data center, or remote office across your network. Transit
Gateway acts as a hub that controls how traffic is routed among all the connected networks which act
like spokes. This hub and spoke model significantly simplifies management and reduces operational costs
because each network only has to connect to the Transit Gateway and not to every other network. Any
new VPC is simply connected to the Transit Gateway and is then automatically available to every other
network that is connected to the Transit Gateway. This ease of connectivity makes it easy to scale your
network as you grow.