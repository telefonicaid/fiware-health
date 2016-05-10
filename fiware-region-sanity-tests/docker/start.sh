export JOB_URL=.
export OS_PROJECT_DOMAIN_NAME=default
export OS_USER_DOMAIN_NAME=default
export OS_IDENTITY_API_VERSION=3
export JENKINS_HOME=.
export JENKINS_URL=.
export JENKINS_JOB=.
export FIHEALTH_WORKSPACE=.
export FIHEALTH_HTDOCS=.
export FIHEALTH_ADAPTER_URL=.
export FIHEALTH_CB_URL=.
export JENKINS_USER=.
export JENKINS_PASSWORD=.
echo ${KEY} >> key.pem
chmod 0600 key.pem
ssh -i key.pem -o "StrictHostKeyChecking no" ubuntu@${VMIP} -fnN -R0:8081:0:8081 &
./resources/docker/start.sh &
./resources/scripts/jenkins.sh exec
