# CC-Project-DBaaS

<h1> Instructions to run the code</h1>
<h1> Rides Instance </h1><br>
1. Start the AWS Rides Instance<br>
2. <code>cd rides-test/rides</code><br>
3. <code>sudo docker system prune --volumes</code><br>
4. <code>sudo docker-compose up --build</code><br>

<h1> Users Instance</h1><br>
1. Start the AWS Users Instance<br>
2. <code>cd users-test/users</code><br>
3. <code>sudo docker system prune --volumes</code><br>
4. <code>sudo docker-compose up --build</code><br>

<h1> DBaaS Instance</h1><br>
1. Start the AWS DBaaS Instance<br>
2. <code>cd project-test/project</code><br>
3. <code>sudo docker rm -f $(sudo docker ps -aq)</code><br>
4. <code><code>sudo docker system prune --volumes</code><br>
5. <code>sudo docker-compose up --build</code><br>
