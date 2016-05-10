echo ${KEY} >> key.pem
chmod 0600 key.pem
ssh -i key.pem ubuntu@${VMIP} -fnN -R0:8081:0:8081 &
