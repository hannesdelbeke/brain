[Snowflake](https://www.snowflake.com/en/) is a cloud-native data platform used to store, clean, and analyze massive amounts of company data. It handles everything a traditional relational database does, but scales infinitely across public clouds like AWS, Azure, and Google Cloud. [1, 2, 3] 

## The Core Architecture
Snowflake's primary engineering breakthrough is the decoupling of storage and compute. It separates its system into three independent layers: [4, 5, 6, 7] 

* **Storage Layer**: A massive database graveyard. It compresses and permanently saves your flat SQL tables, raw logs, or semi-structured JSON text. [5, 8] 
* **Compute Layer** (Virtual Warehouses): Independent muscle clusters. You can boot up ten separate server clusters to read that storage simultaneously—one for your data science team, one for your dashboard apps—without slowing each other down. [4, 5, 9, 10, 11] 
* **Cloud Services Layer**: The traffic cop. It handles user authentication, metadata management, optimization, and security permissions