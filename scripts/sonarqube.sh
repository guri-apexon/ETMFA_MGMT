MODE=$1
read -r -d '' BASE_COMMAND << EOM
sonar-scanner \
  -Dsonar.host.url=$SONAR_URL \
  -Dsonar.login=$SONAR_USER_TOKEN \
  -Dsonar.projectKey=$SONAR_PROJECT_KEY \
  -Dsonar.sources=. \
  -Dsonar.sourceEncoding=UTF-8 \
  -Dsonar.branch.name=$CI_COMMIT_REF_NAME \
  -Dsonar.coverage.exclusions=main.py,setup.py,manage.py,etmfa/tests/** \
  -Dsonar.python.coverage.reportPaths=coverage.xml \
  -Dsonar.python.xunit.reportPath=test_results.xml \
  -Dsonar.gitlab.ref_name=$CI_COMMIT_REF_NAME \
  -Dsonar.gitlab.url=https://$CI_SERVER_HOST \
  -Dsonar.gitlab.user_token=$SONAR_USER_TOKEN \
  -Dsonar.gitlab.project_id=$CI_PROJECT_URL
EOM
if [ "$MODE" == "merge_request" ]; then
  eval "$BASE_COMMAND \
  -Dsonar.gitlab.commit_sha=$(git log --pretty=format:%H "origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME..$CI_COMMIT_SHA" | tr '\n' ',') \
  -Dsonar.gitlab.unique_issue_per_inline=true \
  -Dsonar.gitlab.ci_merge_request_iid=$CI_MERGE_REQUEST_IID \
  -Dsonar.gitlab.merge_request_discussion=true"
elif [ "$MODE" == "branch" ]; then
  eval "$BASE_COMMAND -Dsonar.gitlab.commit_sha=$CI_COMMIT_SHA"
fi
