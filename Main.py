from libsrc.Scraper import GradeScraper
from pprint import pprint
import time

import csv
import re
with open('file.csv', 'r') as f:
    reader = csv.reader(f)
    alumnos = list(reader)
alumnos[0][0] = re.sub('[^0-9]', '', alumnos[0][0])

#id = ''
#pwd = ''
term = '201760'
alumnosfallidos = []
start_time = time.time()

for alumno in alumnos:
    student_start_time = time.time()

    id = alumno[0]
    pwd = alumno[1]

    try: 
        SCRAPER = GradeScraper(id, pwd)
        SCRAPER.print_subject_full_detail(term)
    except KeyboardInterrupt:
        break
    except:
        print("\nHubo un error con el alumno de matrícula {0}, continuando al siguiente... ".format(id))
        alumnosfallidos.append([id, pwd])
        continue
    print("El programa se tardo {0} segundos en obtener la información de este alumno\n".format(time.time() - student_start_time))

final_time = time.time() - start_time
print("\nEl tiempo de ejecución fue de {0} segundos y fallaron {1} alumnos: ".format(final_time, len(alumnosfallidos)))
pprint(alumnosfallidos)