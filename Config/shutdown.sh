# shutdown the service
echo "Shutting down"
ps -ef|grep 301_24/ |grep -v grep|awk '{print $2}'|xargs kill -9

# After the operation is done.
echo "Shut Down Complete."
