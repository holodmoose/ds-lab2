set -x

URL="http://127.0.0.1:8080"

echo 
curl $URL/flights
echo 

curl --header "X-user-name: moose" $URL/me
echo 

curl -X POST --header "X-user-name: moose" $URL/tickets -H "Content-Type: application/json" -d '{"flightNumber": "AFL031", "price": 1500, "paidFromBalance": true}'
echo 

curl -X POST --header "X-user-name: moose" $URL/tickets -H "Content-Type: application/json" -d '{"flightNumber": "AFL031", "price": 1500, "paidFromBalance": false}'
echo 

curl -X POST --header "X-user-name: moose" $URL/tickets -H "Content-Type: application/json" -d '{"flightNumber": "AFL031", "price": 1500, "paidFromBalance": true}'
echo 

curl --header "X-user-name: moose" $URL/tickets


curl -X POST --header "X-user-name: moose" $URL/tickets -H "Content-Type: application/json" -d '{"flightNumber": "AFL031", "price": 1500, "paidFromBalance": true}'


tickets=$(curl --header "X-user-name: moose" http://127.0.0.1:8080/tickets | jq -r ".[].ticketUid")
for ticket in $tickets; do 
    curl -X DELETE --header "X-user-name: moose" $URL/tickets/${ticket}    
done

curl --header "X-user-name: moose" $URL/me
echo 
