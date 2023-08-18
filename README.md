# flask-authentication-task demo
This repository contains the solution for the task assignment to create a backend-only prototype for a social media site
and demonstrate its functionality. The server must support the ability to create new accounts, log into them, implement 
JWT user authentication and allow users to create posts and be able to like and dislike them.   

The solution utilises Flask framework and MongoDB database with `mongoengine` library. The list of libraries used in the
task include:
* `Flask`: web server and REST API endpoints
* `mongoengine`: easy-to-use and intuitive ORM around MongoDB. It provides simple and straightforward way to create
mappings around the data models and query results from the database
* `bcrypt`: hashing, salting and checking passwords
* `PyJWT`: implementation of JSON Web Tokens

The user activity script (called `client`) uses the following libraries:
* `httpx`: robust support for sending requests to server endpoints asynchronously and handles cookies
* Other standard library modules like `secrets`, `string`, etc. are thouroughly used for generating content.

# Security
Security is the top concern for the server-side applications, and it must be handled juridically. In a real-world service, 
security would be much higher than the one in this demo. As far as the test assignment is concerned, this repository acts
as a demo and prioritises ease of deployment for the end reviewer. Hence, it does the following security antipattern:
* Storing secrets (such as JWT sign key and database credentials) as plan-text in the `.env`file. 

In production, secrets are handled either with external management tool, such as HashiCorp Vault or AWS Secrets Manager
or with separation of modules into microservices. The solution uses environmental variables solely for demonstration 
purposes and reviewer convenience. 

# Run
Clone the repository:
```commandline

cd fat/server
```
Define the credentials. The server needs 2 crucial pieces of data: database password and JWT authentication key. Define 
these either as an .env file stored in the server/ directory or export them in your terminal session. Here is an example:
```commandline
export DB_PASSWORD=qddPOdPejfKeTqOszeLTaxexjaZTqdLbZmeXALXPrdrlBUEQPcllAPMsQWsImpXXReqZvzEVboJOHaXHpLgIdfzRhzEPCSLLsJmP
export JWT_SIGN_KEY=FaMPsLteTHyuILThqRAAALVdbSufUkaciliJWTFxDxSQhisZnMMPZRMYhTVxKlsyXudXSoYhzORydJHjQhBtGCieZCsZzHpBqrxM
```
Build the Docker image:
```commandline
docker build -t fat . 
```
Start the server:
```commandline
docker-compose up
```
From this point, the server is up and running, and requests can be made to `http://127.0.0.1:5000`. To run the bot:
```commandline
cd ..
python3 -m client
```
Then switch to the terminal tab running the server and observe the requests incoming. 