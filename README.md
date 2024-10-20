# Webiks Home Assignment

In this project I created terraform resources using API calls.
The main methods used here were:

GET - to retrieve all resources created with 'terraform' tag
POST - to create a new resouce using input variables with terraform
DELETE - to delete a specific resouce from terraform

I used python in this project and containerized it using docker.
I have created a terraform folder with each of the resouces sub folder for better readability


GET : http://127.0.0.1:5000/resources
POST : http://127.0.0.1:5000/resource/s3?bucket_names=myamazingbucket23
