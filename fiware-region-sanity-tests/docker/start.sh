openstack project create test
openstack user create test --password test --project test
openstack role add --user test --project test owner
openstack project show test > project
openstack user show test > user
export OS_TENANT_ID=`grep "| id" project | awk 'NR==1{print $4}'`
export OS_USER_ID=`grep "| id" user | awk 'NR==1{print $4}'`
echo $OS_USER_ID
echo $OS_TENANT_ID
export OS_USERNAME=test
export OS_PASSWORD=test
export OS_TENANT_NAME=test
export JOB_URL=.
export JENKINS_HOME=.
export JENKINS_URL=.
export JENKINS_JOB=.
export FIHEALTH_WORKSPACE=.
export FIHEALTH_HTDOCS=.
export FIHEALTH_ADAPTER_URL=.
export FIHEALTH_CB_URL=.
export JENKINS_USER=.
export JENKINS_PASSWORD=.
export TEST_PHONEHOME_ENDPOINT=http://${VMIP}:8081
echo ${KEY} >> key.pem
chmod 0600 key.pem
ssh -i key.pem -o "StrictHostKeyChecking no" centos@${VMIP} -fnN -R0:8081:0:8081 &
./resources/docker/start.sh &
git checkout origin/$BRANCH
git pull origin $BRANCH
pip install -r requirements.txt
./sanity_checks $OS_REGION_NAME
