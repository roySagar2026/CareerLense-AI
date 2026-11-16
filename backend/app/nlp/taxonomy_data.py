"""Skill taxonomy source data.

One entry per line:  Canonical | category | aliases (comma separated) | family | implies
- A leading "!" on the canonical name makes ALL its matches case-sensitive.
- `family` groups related-but-NOT-equivalent skills (Flask/Django). Family members never
  merge by normalisation or fuzzy matching; they can only produce a "related, not verified"
  semantic match.
- `implies` lists canonical skills that this skill evidences (Docker -> Containerization).
Edit this file to extend the taxonomy; `taxonomy.py` parses it at import time.
"""

TAXONOMY_TEXT = """
Python | language | py, python3, python 3, cpython | |
Java | language | java se, java ee, j2ee, core java | jvm |
JavaScript | language | js, es6, es2015, ecmascript, vanilla js | |
TypeScript | language | | |
C++ | language | cpp, c plus plus, c/c++ | |
C# | language | csharp, c sharp | |
C | language | c programming, c language, ansi c | |
Go | language | golang, go lang, go programming language | |
Rust | language | | |
!Swift | language | SwiftUI | |
Kotlin | language | | jvm |
Scala | language | | jvm |
!Ruby | language | | |
PHP | language | | |
R | language | r programming, r language, rstats | |
MATLAB | language | | |
Bash | language | shell scripting, shell script, bash scripting | |
PowerShell | language | | |
SQL | language | structured query language | |
HTML | language | html5 | |
CSS | language | css3 | |
Sass | language | scss | |
Dart | language | | |
Solidity | language | | |
Assembly | language | assembly language | |
Perl | language | | |
Lua | language | | |
!React | framework | React.js, ReactJS, React JS | frontend-fw |
Angular | framework | angularjs, angular.js | frontend-fw |
Vue.js | framework | vue, vuejs, vue js, vue 3 | frontend-fw |
Svelte | framework | sveltekit | frontend-fw |
Next.js | framework | nextjs, next js | |
Redux | library | redux toolkit | |
Tailwind CSS | framework | tailwind, tailwindcss | |
Bootstrap | framework | | |
jQuery | library | | |
Node.js | framework | nodejs, node js | |
Express.js | framework | expressjs, express js | js-backend |
NestJS | framework | nest.js | js-backend |
Django | framework | django rest framework, drf | py-web |
Flask | framework | | py-web |
FastAPI | framework | fast api | py-web |
Spring Boot | framework | springboot, spring framework, spring mvc, spring data, spring security | java-web |
Hibernate | library | jpa | orm |
SQLAlchemy | library | | orm |
.NET | framework | dotnet, .net core, asp.net, asp.net core, .net framework | |
Ruby on Rails | framework | rails, ror | |
Laravel | framework | | |
GraphQL | framework | graphql api, apollo | api-style |
REST API | concept | restful, restful api, restful apis, rest apis, restful services, restful web services, rest services, web apis | api-style |
gRPC | framework | grpc, protocol buffers, protobuf | api-style |
WebSockets | concept | websocket, web sockets | |
React Native | framework | | mobile |
Flutter | framework | | mobile |
Android | framework | android sdk, android development | mobile |
iOS | framework | ios development, ios sdk | mobile |
PostgreSQL | database | postgres, postgre sql, psql, postgresql database | sql-db |
MySQL | database | | sql-db |
MariaDB | database | | sql-db |
SQL Server | database | mssql, ms sql, microsoft sql server, t-sql, tsql | sql-db |
Oracle Database | database | oracle db, oracle sql, pl/sql, plsql | sql-db |
SQLite | database | | sql-db |
MongoDB | database | mongo, mongo db | nosql-doc |
DynamoDB | database | dynamo db, amazon dynamodb | nosql-doc |
Firestore | database | cloud firestore, firebase firestore | nosql-doc |
Cassandra | database | apache cassandra | nosql-wide |
Redis | database | | kv-cache |
Memcached | database | | kv-cache |
Elasticsearch | database | elastic search, opensearch, elk, elk stack | search |
Solr | database | apache solr | search |
Neo4j | database | graph database | |
Snowflake | database | | warehouse |
BigQuery | database | big query, google bigquery | warehouse |
Redshift | database | amazon redshift | warehouse |
NoSQL | concept | non-relational databases | |
AWS | cloud | amazon web services, aws cloud, ec2, amazon ec2, amazon s3, aws s3, aws lambda, cloudwatch | cloud |
Azure | cloud | microsoft azure, azure devops, azure functions | cloud |
GCP | cloud | google cloud, google cloud platform | cloud |
Firebase | cloud | | |
Heroku | cloud | | |
Vercel | cloud | | |
Docker | devops | docker compose, dockerfile, docker-compose, dockerized, dockerised | containers | Containerization
Kubernetes | devops | k8s, kubernetes cluster, eks, aks, gke | container-orch | Containerization, Container Orchestration
Containerization | concept | containerisation, containerized, containerised, containers | containers |
Container Orchestration | concept | | container-orch |
Helm | devops | helm charts | |
Terraform | devops | | iac | Infrastructure as Code
CloudFormation | devops | aws cloudformation | iac | Infrastructure as Code
Pulumi | devops | | iac | Infrastructure as Code
Infrastructure as Code | concept | iac | iac |
Ansible | devops | | config-mgmt |
!Chef | devops | | config-mgmt |
!Puppet | devops | | config-mgmt |
Jenkins | devops | | ci-cd | CI/CD
GitHub Actions | devops | github workflows | ci-cd | CI/CD
GitLab CI | devops | gitlab ci/cd, gitlab pipelines, gitlab-ci | ci-cd | CI/CD
CircleCI | devops | circle ci | ci-cd | CI/CD
CI/CD | concept | ci cd, cicd, continuous integration, continuous delivery, continuous deployment, continuous integration / continuous delivery, ci/cd pipelines, ci/cd pipeline | |
Nginx | devops | | web-server |
Apache HTTP Server | devops | apache httpd | web-server |
Prometheus | devops | | monitoring |
Grafana | devops | | monitoring |
Datadog | devops | | monitoring |
New Relic | devops | newrelic | monitoring |
Splunk | devops | | monitoring |
Linux | os | unix, ubuntu, centos, debian, rhel | |
Git | tool | github, gitlab, bitbucket, git flow | |
Version Control | concept | source control, source code management, scm | |
Jira | tool | | project-tools |
Confluence | tool | | project-tools |
Postman | tool | | |
Swagger | tool | openapi, swagger ui | |
Kafka | tool | apache kafka, kafka streams | msg-queue |
RabbitMQ | tool | rabbit mq | msg-queue |
Amazon SQS | tool | sqs | msg-queue |
Celery | library | | task-queue |
Apache Spark | data | !PySpark, !Spark, spark streaming | big-data |
Hadoop | data | hdfs, mapreduce, map reduce | big-data |
Apache Flink | data | flink | big-data |
Hive | data | apache hive | big-data |
Apache Airflow | data | airflow | workflow |
dbt | data | data build tool | workflow |
Prefect | data | | workflow |
Dagster | data | | workflow |
ETL | concept | etl pipelines, etl pipeline, elt, data pipelines, data pipeline | |
Data Warehousing | concept | data warehouse, data warehouses | |
Data Modeling | concept | data modelling, database design, schema design | |
Data Analysis | concept | data analytics, analytics, exploratory data analysis, eda | |
Pandas | library | | | Data Analysis
NumPy | library | numpy | |
SciPy | library | | |
Matplotlib | library | seaborn | viz |
Plotly | library | | viz |
Tableau | tool | | bi |
Power BI | tool | powerbi | bi |
Looker | tool | looker studio, data studio | bi |
Excel | tool | microsoft excel, ms excel, advanced excel, vlookup, pivot tables | |
Jupyter | tool | jupyter notebook, jupyter notebooks, jupyterlab | |
Machine Learning | ai_ml | ml, machine-learning, supervised learning, unsupervised learning, predictive modeling, predictive modelling | |
Deep Learning | ai_ml | neural networks, neural network, cnn, rnn, lstm | |
Natural Language Processing | ai_ml | nlp, text mining, text classification | |
Computer Vision | ai_ml | image processing, object detection, image segmentation | |
scikit-learn | library | sklearn, scikit learn | ml-lib | Machine Learning
TensorFlow | library | tensorflow 2 | dl-fw | Machine Learning, Deep Learning
PyTorch | library | pytorch lightning | dl-fw | Machine Learning, Deep Learning
Keras | library | | dl-fw | Machine Learning, Deep Learning
XGBoost | library | lightgbm, gradient boosting | ml-lib | Machine Learning
OpenCV | library | opencv-python, cv2 | | Computer Vision
spaCy | library | | nlp-lib | Natural Language Processing
NLTK | library | | nlp-lib | Natural Language Processing
Hugging Face | library | huggingface, transformers, hugging face transformers | nlp-lib | Natural Language Processing
LLM | ai_ml | llms, large language models, large language model, generative ai, genai, gpt | |
LangChain | library | langgraph, llamaindex, llama index | |
RAG | ai_ml | retrieval augmented generation, retrieval-augmented generation | |
Prompt Engineering | ai_ml | prompt design | |
MLOps | ai_ml | ml ops, mlflow, model deployment, model serving | |
Reinforcement Learning | ai_ml | | |
Statistics | concept | statistical analysis, statistical modeling, hypothesis testing, a/b testing, ab testing | |
Pytest | testing | py.test | test-py | Unit Testing
unittest | testing | python unittest | test-py | Unit Testing
JUnit | testing | junit5, junit 5, testng, mockito | test-java | Unit Testing
Jest | testing | vitest, mocha, jasmine | test-js | Unit Testing
Cypress | testing | | e2e |
Playwright | testing | | e2e |
Selenium | testing | webdriver | e2e |
Unit Testing | testing | unit tests, unit test, test-driven development, tdd | |
Integration Testing | testing | integration tests | |
Test Automation | testing | automated testing, automation testing, qa automation | |
Microservices | concept | microservice, micro-services, microservice architecture, service-oriented architecture, soa | |
System Design | concept | systems design, software architecture, architecture design, high-level design, low-level design, scalable systems, scalable architecture | |
Distributed Systems | concept | distributed computing, distributed architecture | |
Data Structures | concept | data structures and algorithms, dsa | |
Algorithms | concept | algorithm design, algorithmic problem solving | |
Object-Oriented Programming | concept | oop, oops, object oriented programming, object-oriented design, object oriented design | |
Design Patterns | concept | solid principles, gof patterns | |
Concurrency | concept | multithreading, multi-threading, multithreaded, parallel programming, async programming, asyncio | |
Caching | concept | cache, cache invalidation | |
Message Queues | concept | message queue, messaging systems, event-driven architecture, event driven architecture, pub/sub, pubsub | |
Load Balancing | concept | load balancer, load balancers | |
API Design | concept | api development, api design and development, designing apis | api-style |
Backend Development | concept | backend development, back-end development, backend developer, back-end developer, backend engineer, backend services, server-side development | |
Authentication | security | oauth, oauth2, oauth 2.0, jwt, json web tokens, sso, single sign-on, saml, openid connect, oidc | |
Application Security | security | owasp, secure coding, secure development, penetration testing, vulnerability management | |
Cybersecurity | security | information security, infosec, network security | |
Networking | concept | tcp/ip, tcp ip, dns, networking concepts, computer networks | |
Operating Systems | concept | os concepts, operating system concepts | |
Databases | concept | database management, dbms, rdbms, relational databases, relational database | |
Query Optimization | concept | query tuning, performance tuning, database optimization, database performance | |
Performance Optimization | concept | performance optimisation, profiling, latency optimization | |
Code Review | concept | code reviews, peer review, pull requests | |
Agile | methodology | agile methodology, agile methodologies, agile development, agile/scrum | agile-fw |
Scrum | methodology | scrum master, sprint planning, sprints | agile-fw |
Kanban | methodology | | agile-fw |
Technical Documentation | concept | documentation, technical writing | |
Debugging | concept | troubleshooting, root cause analysis, rca, incident response | |
Site Reliability | devops | sre, site reliability engineering, observability, on-call | |
Serverless | concept | lambda functions, serverless architecture, cloud functions | |
!Unity | tool | Unity3D, Unity 3D, Unity Engine | game-engine |
Unreal Engine | tool | unreal | game-engine |
Figma | tool | | design-tools |
UI/UX Design | concept | ui design, ux design, ui/ux, user experience, user interface design, wireframing | |
Responsive Design | concept | responsive web design, mobile-first, mobile first | |
Accessibility | concept | wcag, a11y, web accessibility | |
Webpack | tool | vite, babel, bundlers | |
npm | tool | yarn, pnpm | |
Maven | tool | gradle | java-build |
CMake | tool | makefile, makefiles | |
Embedded Systems | concept | embedded c, firmware, rtos, microcontrollers, microcontroller, arduino, raspberry pi | |
IoT | concept | internet of things | |
Blockchain | concept | smart contracts, web3, ethereum | |
SAP | tool | sap erp, sap hana, sap abap, abap | erp |
Salesforce | tool | apex, salesforce crm | erp |
Project Management | concept | project planning, program management, delivery management | |
Stakeholder Management | soft_skill | stakeholder communication, stakeholder engagement | |
Communication | soft_skill | communication skills, verbal communication, written communication, excellent communication, strong communication | |
Leadership | soft_skill | team leadership, technical leadership, team lead, tech lead | |
Teamwork | soft_skill | team player, collaboration, collaborative, cross-functional collaboration, cross-functional teams, cross functional | |
Problem Solving | soft_skill | problem-solving, analytical skills, analytical thinking, critical thinking | |
Mentoring | soft_skill | mentorship, coaching, mentor | |
Time Management | soft_skill | prioritization, prioritisation, deadline-driven | |
AWS Certified Solutions Architect | certification | aws solutions architect, aws certified solutions architect - associate, saa-c03 | |
AWS Certified Developer | certification | aws certified developer - associate, aws developer associate | |
AWS Certified Cloud Practitioner | certification | aws cloud practitioner, clf-c02 | |
Azure Fundamentals | certification | az-900, microsoft azure fundamentals, azure administrator, az-104 | |
Google Cloud Certified | certification | google cloud associate cloud engineer, gcp certified, professional cloud architect | |
PMP | certification | project management professional | |
CISSP | certification | | |
CCNA | certification | cisco certified network associate | |
CKA | certification | certified kubernetes administrator | |
CKAD | certification | certified kubernetes application developer | |
Terraform Associate | certification | hashicorp certified terraform associate | |
Certified Scrum Master | certification | csm, psm, professional scrum master | |
"""
