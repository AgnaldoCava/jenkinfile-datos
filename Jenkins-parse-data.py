import sys
url = sys.argv[1]
path = sys.argv[2]
import json
import requests

url = sys.argv[1]
path = sys.argv[2]

def extract_jenkinsfile_data(url, path):
  jenkinsfile_url = f"{url}/raw/master/{path}/Jenkinsfile"
  response = requests.get(jenkinsfile_url)
  jenkinsfile_content = response.text

  # Extracting stage name
  stage_name = jenkinsfile_content.split("stage('")[1].split("'")[0]

  # Counting number of stages
  num_stages = jenkinsfile_content.count("stage(")

  # Extracting @Library name
  library_name = jenkinsfile_content.split("@Library('")[1].split("'")[0]

  # Counting number of @Library
  num_libraries = jenkinsfile_content.count("@Library")

  # Extracting Sh commands
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

  # Printing data in JSON format
  print(json.dumps(data, indent=4))

# Example usage
url = "https://github.com/agill17/Infrastructure-as-Code.git"
path = "path/to/jenkinsfile"
extract_jenkinsfile_data(url, path)


