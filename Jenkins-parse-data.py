import sys

url = sys.argv[1]
path = sys.argv[2]

def recibir_variables(url, path):
  print("Valor de 'url':", url)
  print("Valor de 'path':", path)


# Ejemplo de uso
recibir_variables(url, path)
print("Valores recibidos:")
print("url:", url)
print("path:", path)