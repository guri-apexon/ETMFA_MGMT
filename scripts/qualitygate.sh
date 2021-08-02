#!/usr/bin/env sh

apk add curl
apk add jq

SONAR_RESULT="/tmp/sonar.log"

if [ ! -f $SONAR_RESULT ]
then
  echo "Sonar result does not exist"
  exit 1
fi

CE_TASK_ID=`sed -n -e 's/^.*task?id=//p' < $SONAR_RESULT`

echo "CE_TASK_ID: $CE_TASK_ID"

#While report is processed ANALYSIS_ID is not availabe and jq returns null

ANALYSIS_ID=$(curl -XGET -u $SONAR_LOGIN:$SONAR_PASSWORD -H 'Accept:application/json' $SONAR_SERVER/api/ce/task?id=$CE_TASK_ID -k | jq -r .task.analysisId)

echo "ANALYSIS_ID: $ANALYSIS_ID"

I=1
TIMEOUT=0
while [ $ANALYSIS_ID = "null" ]
do
  if [ "$TIMEOUT" -gt 30 ]
  then
    echo "Timeout of " + $TIMEOUT + " seconds exceeded for getting ANALYSIS_ID"
    exit 1
  fi
  sleep $I
  TIMEOUT=$((TIMEOUT+I))
  I=$((I+1))
  ANALYSIS_ID=$(curl -XGET -u $SONAR_LOGIN:$SONAR_PASSWORD -H 'Accept:application/json' $SONAR_SERVER/api/ce/task?id=$CE_TASK_ID -k | jq -r .task.analysisId)
done

echo "ANALYSIS_ID after while loop: $ANALYSIS_ID"

curl -XGET -u $SONAR_LOGIN:$SONAR_PASSWORD -H 'Accept:application/json' $SONAR_SERVER/api/qualitygates/project_status?analysisId=$ANALYSIS_ID -k | jq . > sonarreport.json
cat sonarreport.json

STATUS=$(curl -XGET -u $SONAR_LOGIN:$SONAR_PASSWORD -H 'Accept:application/json' $SONAR_SERVER/api/qualitygates/project_status?analysisId=$ANALYSIS_ID -k | jq -r .projectStatus.status)
echo "sonar quality gate status : $STATUS"

if [ $STATUS = "ERROR" ]
then
  echo "Qualitygate failed."
  exit 1
fi

echo "Sonar Qualitygate is OK"
exit 0
