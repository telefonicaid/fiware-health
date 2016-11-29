export OS_IDENTITY_API_VERSION=3
openstack --os-interface public project create test
openstack --os-interface public user create test --password test --project test
openstack --os-interface public role add --user test --project test owner
openstack --os-interface public project show test > project
openstack --os-interface public user show test > user
glance image-list |grep cirros > images
export image=`cat images | awk 'NR==1{print $2}'`
glance image-update $image --name base_centos_6
export OS_TENANT_ID=`grep "| id" project | awk 'NR==1{print $4}'`
export OS_USER_ID=`grep "| id" name | awk 'NR==1{print $4}'`
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
export TEST_PHONEHOME_ENDPOINT=http://${VM_IP}:8081
echo ${KEY} >> key.pem
chmod 0600 key.pem
ssh -i key.pem -o "StrictHostKeyChecking no" centos@{VM_IP} -fnN -R0:8081:0:8081 &
./resources/docker/start.sh &
git checkout origin/$BRANCH
git pull origin $BRANCH
pip2.7 install -r requirements.txt
sed -i "s|OS_AUTH_URL|$OS_AUTH_URL|g" etc/settings.json
./sanity_checks $OS_REGION_NAME
