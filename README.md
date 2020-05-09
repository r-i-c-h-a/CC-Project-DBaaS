# CC-Project-DBaaS

<h1> Instructions to run the code</h1>
<h1> Rides Instance </h1><br>
1. Start the AWS Rides Instance<br>
2. cd rides-test/rides
<br>
3. sudo docker system prune --volumes
<br>
4. sudo docker-compose up --build<br>

<h1> Users Instance</h1><br>
1. Start the AWS Users Instance<br>
2. cd users-test/users<br>
3. sudo docker system prune --volumes<br>
4. sudo docker-compose up --build<br>

<h1> DBaaS Instance</h1><br>
1. Start the AWS DBaaS Instance<br>
2. cd project-test/project<br>
3. sudo docker rm -f $(sudo docker ps -aq)<br>
4. sudo docker system prune --volumes<br>
5. sudo docker-compose up --build<br>
