import sys
import json
import requests

# def extract_jenkinsfile_data(url, path):
#   jenkinsfile_url = f"{url}/raw/master/{path}/Jenkinsfile"
#   response = requests.get(jenkinsfile_url)
#   jenkinsfile_content = response.text

#   # Extracting stage name
#   stage_name = ""
#   if "stage('" in jenkinsfile_content:
#     stage_name = jenkinsfile_content.split("stage('")[1].split("'")[0]

#   # Counting number of stages
#   num_stages = jenkinsfile_content.count("stage(")

#   # Extracting @Library name
#   library_name = ""
#   if "@Library('" in jenkinsfile_content:
#     library_name = jenkinsfile_content.split("@Library('")[1].split("'")[0]

#   # Counting number of @Library
#   num_libraries = jenkinsfile_content.count("@Library")

#   # Extracting Sh commands
#   sh_commands = ""
#   if "sh '" in jenkinsfile_content:
#     sh_commands = jenkinsfile_content.split("sh '")[1].split("'")[0]

#   # Counting number of Sh commands
#   num_sh_commands = jenkinsfile_content.count("sh '")

#   # Creating dictionary with extracted data
#   data = {
#     "stage_name": stage_name,
#     "num_stages": num_stages,
#     "library_name": library_name,
#     "num_libraries": num_libraries,
#     "sh_commands": sh_commands,
#     "num_sh_commands": num_sh_commands
#   }

#   # Returning data instead of printing it
#   return data

# # Example usage
# url = "https://github.com/agill17/Infrastructure-as-Code.git"
# path = "Jenkinsfile/102/jenkinsfile"
# result = extract_jenkinsfile_data(url, path)
# print(json.dumps(result, indent=4))

def extract_jenkinsfile_data(jenkinsfile_content):
  # Extracting stage name
  stage_name = ""
  stages = []
  for line in jenkinsfile_content.splitlines():
    if "stage('" in line:
      stage_name = line.split("stage('")[1].split("'")[0]
      stages.append(stage_name)
  # Counting number of stages
  num_stages = jenkinsfile_content.count("stage(")
  # Extracting @Library name
  library_name = ""
  if "@Library('" in jenkinsfile_content:
    library_names = [library.split("'")[0] for library in jenkinsfile_content.split("@Library('")[1:]]
    library_name = ", ".join(library_names)
  # Counting number of @Library
  num_libraries = jenkinsfile_content.count("@Library")
  # Extracting Sh commands
  sh_commands = ""
  if "sh '" in jenkinsfile_content:
    sh_commands = jenkinsfile_content.split("sh '")[1].split("'")[0]
  # Counting number of Sh commands
  num_sh_commands = jenkinsfile_content.count("sh '")
  # Creating dictionary with extracted data
  data = {
    "stage_name": stage_name,
    "num_stages": num_stages,
    "library_name": library_name,
    "num_libraries": num_libraries,
    "sh_commands": sh_commands,
    "num_sh_commands": num_sh_commands
  }
  # Returning data instead of printing it
  return data

# Example usage
jenkinsfile_content = """
@Library('library') _
node {
  def appDir = "Jenkinsfile/202"
  currentBuild.setResult('SUCCESS')
  def mvnImage
  def commitId
  def appName = "grants"
  def branchName = "dev"
  def nexusRepoToUse
  def nexusRepoAddress = "172.31.2.11:8081"
  def masterIp = sh (returnStdout: true, script: 'hostname -I').split(" ")[1]
  def appVersion = mvnGetAppVersion { pomFile ="${workspace}/${appDir}/pom.xml" }
  println appVersion
  try {
    stage ('Clone'){
      def git = checkout scm
      commitId = git.COMMIT_ID
      println appVersion
    }
    dir(appDir) {
      mvnImage = docker.image("maven:latest").inside("-v /var/lib/jenkins/.grants:/root/.m2") {
        stage('Clean up') {
          sh "mvn clean"
        }
        stage ('Build'){
          sh "mvn package"
        }
      }
      stage('Publish to Nexus'){
        sh "ls -al"
        sh "pwd"
        nexusRepoToUse = "${branchName}-${appName}"
        nexusPublisher nexusInstanceId: "172.31.2.11:8081", nexusRepositoryId: "dev-grants", packages: [[$class: 'MavenPackage', mavenAssetList: [[classifier: '', extension: '', filePath: 'target/grants.war']], mavenCoordinate: [artifactId: 'grants', groupId: 'com.uts.grants', packaging: 'war', version: '1.1.0']]]    
      }
    }
  } catch (err) {
    currentBuild.setResult('FAILURE')
  } finally {
    def slackFailMessage = "BUILD ${currentBuild.result}\n JOB:${env.JOB_NAME}\n JOB_NUMBER: ${env.BUILD_NUMBER}\n URL: http://${masterIp}:8080/jenkins/job/${env.JOB_NAME}/${env.BUILD_NUMBER}/console"
    def colorStatus = "#008000" #green
    if (currentBuild.result.equalsIgnoreCase("failure")){
      colorStatus = "FF0000"
    }
    slackSend(channel: "alerts", message: slackFailMessage, color: colorStatus)
  }
}
"""

result = extract_jenkinsfile_data(jenkinsfile_content)
print(json.dumps(result, indent=4))