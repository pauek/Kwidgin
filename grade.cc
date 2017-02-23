
#include <cstdlib>
#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <vector>
using namespace std;

struct Student {
   string DNI;
   string answers;
};

typedef vector<string> Solutions;
typedef vector<Student> Students;

void replace_char(string& s, char a, char b) {
   for (int i = 0; i < s.size(); i++) {
      if (s[i] == a) s[i] = b;
   }
}

template<class T>
void set(vector<T>& v, int i, T t) {
   if (v.size() <= i) {
      v.resize(i+1);
   }
   v[i] = t;
}

void read_students(const char *filename, Students& students) {
   ifstream F(filename);   
   string line;
   while (getline(F, line)) {
      char semicolon;
      int permutation;
      Student student;
      replace_char(line, ';', ' ');
      istringstream S(line);
      if (S >> permutation >> student.DNI >> student.answers) {
         set(students, permutation, student);
      }
   }
}

void read_solutions(const char *filename, Solutions& solutions) {
   ifstream F(filename);
   string line;
   while (getline(F, line)) {
      char semicolon;
      int permutation;
      string solution;
      replace_char(line, ';', ' ');
      istringstream S(line);
      if (S >> permutation >> solution) {
         set(solutions, permutation, solution);
      }
   }
}

float compute_grade(const string& solution, const string& x) {
   if (solution.size() != x.size()) {
      cerr << "Mismatch in sizes ('" << solution << "' vs '" << x << "') !" << endl;
      exit(1);
   }
   int count = 0;
   float grade = 0.0f;
   for (int i = 0; i < solution.size(); i++) {
      if (solution[i] == x[i]) {
         grade += 1.0f;
         count++;
      } else if (x[i] == 'X') { // pregunta anulada
         // do not increment count!
      } else if (x[i] != '_' and solution[i] != x[i]) {
         grade -= 0.3333f;
         count++;
      }
   }
   return grade / float(count) * 10.0;
}

int main(int argc, char *argv[]) {
   if (argc < 3) {
      fprintf(stderr, "usage: grade <solutions-file> <students-file>\n");
      exit(1);
   }

   Solutions solutions;
   Students students;
   read_solutions(argv[1], solutions);
   read_students(argv[2], students);

   for (int i = 0; i < students.size(); i++) {
      if (students[i].DNI != "") {
         cout << i << ';' << students[i].DNI << ';';
         cout << setprecision(2) << compute_grade(solutions[i], students[i].answers);
         cout << endl;
      }
   }
}
