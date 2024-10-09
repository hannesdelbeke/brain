# AWS App Mesh
AWS App Mesh makes it easy to monitor and control microservices running on AWS. App Mesh
standardizes how your microservices communicate, giving you end-to-end visibility and helping to
ensure high-availability for your applications.
Modern applications are often composed of multiple microservices that each perform a specific function.
This architecture helps to increase the availability and scalability of the application by allowing each
component to scale independently based on demand, and automatically degrading functionality when
a component fails instead of going offline. Each microservice interacts with all the other microservices
through an API. As the number of microservices grows within an application, it becomes increasingly
difficult to pinpoint the exact location of errors, re-route traffic after failures, and safely deploy code
changes. Previously, this has required you to build monitoring and control logic directly into your code
and redeploy your microservices every time there are changes.
AWS App Mesh makes it easy to run microservices by providing consistent visibility and network traffic
controls for every microservice in an application. App Mesh removes the need to update application
code to change how monitoring data is collected or traffic is routed between microservices. App Mesh
configures each microservice to export monitoring data and implements consistent communications control logic across your application. This makes it easy to quickly pinpoint the exact location of errors and automatically re-route network traffic when there are failures or when code changes need to be deployed.
You can use App Mesh with [[Amazon Elastic Container Service|Amazon ECS]] and [[Amazon Elastic Kubernetes Service|Amazon EKS]] to better run containerized microservices at scale. App Mesh uses the open source Envoy proxy, making it compatible with a wide range of AWS partner and open source tools for monitoring microservices.