# AWS Cloud Map
AWS Cloud Map is a cloud resource discovery service. With Cloud Map, you can define custom names
for your application resources, and it maintains the updated location of these dynamically changing
resources. This increases your application availability because your web service always discovers the most
up-to-date locations of its resources.
Modern applications are typically composed of multiple services that are accessible over an API and
perform a specific function. Each service interacts with a variety of other resources such as databases,
queues, object stores, and customer-defined microservices, and they also need to be able to find the
location of all the infrastructure resources on which it depends, in order to function. You typically
manually manage all these resource names and their locations within the application code. However,
manual resource management becomes time consuming and error-prone as the number of dependent
infrastructure resources increases or the number of microservices dynamically scale up and down
based on traffic. You can also use third-party service discovery products, but this requires installing and
managing additional software and infrastructure.
Cloud Map allows you to register any application resources such as databases, queues, microservices, and
other cloud resources with custom names. Cloud Map then constantly checks the health of resources to
make sure the location is up-to-date. The application can then query the registry for the location of the
resources needed based on the application version and deployment environment.