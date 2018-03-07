
package main

import (
   "fmt"
   "html/template"
   "net/http"
)

/*

Respetar el directorio de carpetas, usarlas en el servidor web
- Cada test es una carpeta con estructura:
   
      Makefile
      solution.inf
      solution.cls
      normal.cls
      tex/
         exam_XXXX.tex
         ...

- Luego debe haber un fichero con los DNIs de cada alumno
  (directamente el formato Atenea?) = students.csv



1. Leer el directorio y comprobar que hay 'students.csv' y 
   que tiene las columnas que tocan. 
   Leer la lista de estudiantes.

2. Catalogar cada carpeta y mirar que cada una tiene
   'solutions.inf'. Leer los datos en memoria.

3. Al recibir un request para '/<test>' situarse en la carpeta
   con nombre <test> y mostrar el form. Si no, error.

4. Al recibi un post para '/<test>/answer' añadir a la lista de 
   respuestas el DNI y calcular la nota según la permutación
   Mostrar el nombre completo y la nota (+ las notas anteriores?).

5. Debe haber un gorutina que recibe las actualizaciones de la tabla
   (y tiene un timeout en el select que graba la lista si ha cambiado)

*/

type Student struct {
   Nom     string
   Cognoms string
   DNI     string
   Grup    string
   Email   string
}

func ReadStudents() []Student {
   list = []Student{}
   file := open("students.csv") 
}


var formPage = template.Must(template.ParseFiles("form.html"))

func hExamForm(w http.ResponseWriter, r *http.Request) {
   err := formPage.ExecuteTemplate(w, "form.html", nil)
   if err != nil {
      http.Error(w, err.Error(), http.StatusInternalServerError)
   }
}

func hPutAnswer(w http.ResponseWriter, r *http.Request) {
   dni     := r.FormValue("dni")
   answers := r.FormValue("answers")
   // Calcular la nota
   // Escribir las respuestas en un fichero (con la nota)
   fmt.Fprintf(w, "You said: %s, %s\n", dni, answers)
}


func main() {
   http.HandleFunc("/put", hPutAnswer)
   http.HandleFunc("/", hExamForm)
   http.ListenAndServe(":8080", nil)
}