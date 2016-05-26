export OS_IDENTITY_API_VERSION=3
openstack --os-interface public project show $OS_TENANT_NAME > project
openstack --os-interface public  user show $OS_USERNAME > user
export OS_TENANT_ID=`grep "| id" project | awk 'NR==1{print $4}'`
export OS_USER_ID=`grep "| id" user | awk 'NR==1{print $4}'`
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
source /root/venv/fiware-region-sanity-tests/bin/activate; pip2.7 install -r requirements.txt
source /root/venv/fiware-region-sanity-tests/bin/activate; ./sanity_checks $OS_REGION_NAME
