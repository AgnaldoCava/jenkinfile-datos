import os
import sys
import shutil
import re
import json
import git


# USERNAME=os.getenv('USERNAME')
# APP_PW=os.getenv('APP_PW')
# URL_GLOBAL_LIBRARY=f"https://{USERNAME}:{APP_PW}@bitbucket.org/corparchitecture/global-pipeline-library.git"
# REPO_LIBRARY_PATH="global-pipeline-library"
# URL_GLOBAL_TEMPLATES=f"https://{USERNAME}:{APP_PW}@bitbucket.org/corparchitecture/global-pipeline-templates.git"
# REPO_TEMPLATES_PATH="global-pipeline-templates"

WORKSPACE_DIR="WORKSPACE"
REPO_PATH = "jenkinsfile_repo"
URL_JENKINSFILE = sys.argv[2]
PATH_JENKINSFILE = sys.argv[3]

def show_help():
    print("")
    print("--url      Url del repositorio donde se encuentra el Jenkinsfile.")
    print("--path     Path del jenkinsfile.")
    print("")
    sys.exit(1)




def check_arguments():
    # Args from command line
    args = sys.argv[1:]


    # Mapping options
    options_mapping = {
        '-h': lambda: (show_help()),
        '--help': lambda: (show_help()),
        '--url': lambda: setattr(sys.modules[__name__], 'URL_JENKINSFILE', args.pop(0).strip()),
        '--path': lambda: setattr(sys.modules[__name__], 'PATH_JENKINSFILE', args.pop(0).strip()),
    }


    # Verifica si no hay argumentos y muestra la ayuda
    if not (args := sys.argv[1:]):
        show_help()
        raise ValueError("Argumentos no definidos.")


    while args:
        if (current_arg := args.pop(0)) not in options_mapping:
            raise ValueError(f"Opción no válida {current_arg}")


        options_mapping[current_arg]()


    # Verifica si URL_JENKINSFILE y PATH_JENKINSFILE están definidos
    if not hasattr(sys.modules[__name__], 'URL_JENKINSFILE') or not hasattr(sys.modules[__name__], 'PATH_JENKINSFILE') :
        raise ValueError("Los argumentos 'url', 'path' son obligatorios.")


    print("[INFO] URL JENKINSFILE:", getattr(sys.modules[__name__], 'URL_JENKINSFILE', None))
    print("[INFO] PATH JENKINSFILE:", getattr(sys.modules[__name__], 'PATH_JENKINSFILE', None))


# def download_libraries():
#     print("[INFO] Clonando global-pipeline-library")
#     git.Repo.clone_from(URL_GLOBAL_LIBRARY, REPO_LIBRARY_PATH, branch="master")
#     print("[INFO] Clonado global-pipeline-library")
#     print("[INFO] Clonando global-template-library")
#     git.Repo.clone_from(URL_GLOBAL_TEMPLATES, REPO_TEMPLATES_PATH, branch="master")
#     print("[INFO] Clonado global-template-library")


def download_jenkinsfile(branch:str):
    print(f"[INFO] Clonando {URL_JENKINSFILE}")
    url = URL_JENKINSFILE.replace("https://","{url}/raw/master/{path}")


    git.Repo.clone_from(url, REPO_PATH, branch=branch)
    print(f"[INFO] Clonado {URL_JENKINSFILE}")
    print(f"[INFO] Moviendo Jenkinsfile a {WORKSPACE_DIR}")
    os.rename(f"{REPO_PATH}/{PATH_JENKINSFILE}", f"{WORKSPACE_DIR}/Jenkinsfile_to_parse" )
    print(f"[INFO] Jenkinsfile movido a {WORKSPACE_DIR}")
    print(f"[INFO] Eliminando directorio {REPO_PATH}")
    shutil.rmtree(REPO_PATH)
    print(f"[INFO] Directorio {REPO_PATH} eliminado")


def get_libraries(parsed_data,jenkinsfile_content):
    if not (libraries := re.findall('@Library\\([\'\\"](.*?)[\'\\"]\\)', jenkinsfile_content)):
        # Busca bibliotecas en array
        libraries = re.findall(r"@Library\(\[('.*')\]\)", jenkinsfile_content, re.DOTALL)
        parsed_library = []
        for element in libraries:
            parsed_library.extend(re.findall(r"'(.*?)'", element))
            libraries=parsed_library
    parsed_data["libraries"] = libraries


def use_pod_template(parsed_data,jenkinsfile_content):
    parsed_data["useGetPodTemplate"] = "getPodTemplate" in jenkinsfile_content


def get_security(parsed_data,jenkinsfile_content):
    jenkinsfile_simple_comment = re.sub(r"\/\/.*?\n",'', jenkinsfile_content, re.DOTALL)
    jenkinsfile_content_cleaned=""
    dentro_comentario = False
    for line in jenkinsfile_simple_comment.split('\n'):
        if re.search(r'".*"|\'.*\'', line):
            continue
        if re.search(r'[^\w]/\*', line):
            dentro_comentario = True
        elif dentro_comentario:
            if '*/' in line or '"' in line or '"""' in line:
                dentro_comentario = False
        else:
            jenkinsfile_content_cleaned+=line


    security = re.findall(r"script{.*?(secPreBuild\(\)|secPostBuild\(\)|secPreDeploy\(\)|secPostDeploy\(\)|[}]).*?", jenkinsfile_content_cleaned, re.DOTALL)
    if 'secPreBuild()' in security and 'secPostBuild()' in security and 'secPreDeploy()' in security and 'secPostDeploy()' in security:
        parsed_data["security"] = True


def get_containers(parsed_data,jenkinsfile_content):
    if (agent_block := re.search(r"agent\s*{.*?}", jenkinsfile_content, re.DOTALL)):
        container_definitions = re.findall(r"\[\s*['\"](.*?)['\"]\s*,\s*(.*?)\s*,\s*(.*?)\s*\]", agent_block.group(), re.DOTALL)
        for container in container_definitions:
            containername = container[0]
            containertype = container[1]
            containersize = container[2]
            parsed_data["containers"].append({"name": containername, "type": containertype, "size": containersize})


def get_env_vars(parsed_data,jenkinsfile_content):
    environment_blocks = re.findall(r"pipeline\s*{.*?environment\s*{(.*?)[^\w)]\}", jenkinsfile_content, re.DOTALL)
    for block in environment_blocks:
        environment_vars = re.findall(r"(?P<key>\w+)\s+=\s+(?P<value>.+)\n", block)
        for key, value in environment_vars:
            if value.startswith('"') and value.endswith('"'):
                value=value[1:-1]
            parsed_data["environment"][key.strip()] = value.strip()


def get_stages(parsed_data,jenkinsfile_content):
    stages = re.findall(r"stage\s*\(['\"](.*?)['\"]\)\s*\{(.*?.\{.*?[^\w]\})", jenkinsfile_content, re.DOTALL)
    parsed_data["stages"]["count"] = len(stages)


    for stage_name, stage_content in stages:
        parsed_data["stages"]["stages"].append({"name": stage_name})
        stage_content=re.findall(r"environment.{(.*)}", stage_content, re.DOTALL)
        processed_data = ['"' + elemento.strip()[0:-1].replace('\n', ',').replace(' ', '').replace('=', '":') + '"' for elemento in stage_content]
        for element in processed_data:
            cadena_dict = {key.strip('"'): value.strip('"${}') for key, value in (pair.split(':') for pair in element.split(','))}
            parsed_data["stages"]["stages"][-1]["environment"] = cadena_dict


def parse_jenkinsfile(jenkinsfile):
    print("[INFO] Parseando Jenkinsfile")
    parsed_data = {
        "libraries": [],
        "security": False,
        "useGetPodTemplate": False,
        "containers": [],
        "environment": {},
        "stages": {
            "count": 0,
            "stages": []
        }
    }
   


    with open(jenkinsfile, 'r', encoding="utf-8") as file:
        jenkinsfile_content = file.read()
        # Busca bibliotecas
        print("[INFO] Buscando bibliotecas")
        get_libraries(parsed_data,jenkinsfile_content)


        # Verifica si se utiliza getPodTemplate
        print("[INFO] Buscando si se utiliza getPodTemplate")
        use_pod_template(parsed_data,jenkinsfile_content)


        # Verifica si se utiliza seguridad
        print("[INFO] Buscando stages de seguridad")
        get_security(parsed_data,jenkinsfile_content)


        # Busca contenedores
        print("[INFO] Buscando contenedores")
        get_containers(parsed_data,jenkinsfile_content)


        # Busca definiciones de environment a nivel raíz del pipeline
        print("[INFO] Buscando variables de entorno")
        get_env_vars(parsed_data,jenkinsfile_content)


        # Busca información de los stages
        print("[INFO] Buscando informacion de los stages")
        get_stages(parsed_data,jenkinsfile_content)


    file.close()
    return parsed_data


check_arguments()


if os.path.isdir(WORKSPACE_DIR):
    shutil.rmtree(WORKSPACE_DIR)
if os.path.isdir(REPO_PATH):
    shutil.rmtree(REPO_PATH)
#if os.path.isdir(REPO_LIBRARY_PATH):
#    shutil.rmtree(REPO_LIBRARY_PATH)
#if os.path.isdir(REPO_TEMPLATES_PATH):
#    shutil.rmtree(REPO_TEMPLATES_PATH)


os.mkdir(WORKSPACE_DIR)
#####download_libraries() #SOON
download_jenkinsfile("main")


jenkinsfile_path = f"{WORKSPACE_DIR}/Jenkinsfile_to_parse"
# Llama a la función para analizar el Jenkinsfile
parsed_jenkinsfile = parse_jenkinsfile(jenkinsfile_path)


# Convierte el resultado a formato JSON
json_data = json.dumps(parsed_jenkinsfile, indent=4)


# Imprime el JSON resultante
print(json_data)
#DELETE DIRS
#shutil.rmtree(REPO_LIBRARY_PATH)
#shutil.rmtree(REPO_TEMPLATES_PATH)
shutil.rmtree(WORKSPACE_DIR)
