1. The python script should be wrapped into a docker container with python3.
2. Clone the Git repo.
3. Run the following command to build the docker image.

   docker build -t ericsson/nmaas/alert-awx-integration .

4. Prepare the awx.conf with relevant configuration to be mounted to /etc/awx.conf.
5. Run the following command to start the docker container. 

   docker run -p 9099:9099 -v <awx.conf file path on host>:/etc/awx.conf ericsson/nmaas/alert-awx-integration

