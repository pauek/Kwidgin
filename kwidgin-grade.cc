
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

string& replace_char(string& s, char a, char b) {
   for (int i = 0; i < s.size(); i++) {
      if (s[i] == a) s[i] = b;
   }
   return s;
}

inline bool IsComment(string line) {
   return line.size() > 0 && line[0] == '#';
}

template<class T>
void Set(vector<T>& v, int i, T t) {
   if (v.size() <= i) {
      v.resize(i+1);
   }
   v[i] = t;
}

void ReadStudents(string filename, Students& students) {
   ifstream F(filename);   
   string line;
   int permutation;
   Student student;
   while (getline(F, line)) {
      if (IsComment(line)) {
         continue;
      }
      istringstream S(replace_char(line, ';', ' '));
      if (S >> permutation >> student.DNI >> student.answers) {
         Set(students, permutation, student);
      }
   }
}

void ReadSolutions(string filename, Solutions& solutions) {
   ifstream F(filename);
   string line, solution;
   int permutation;
   while (getline(F, line)) {
      if (IsComment(line)) {
         continue;
      }
      istringstream S(replace_char(line, ';', ' '));
      if (S >> permutation >> solution) {
         Set(solutions, permutation, solution);
      }
   }
}

double ComputeGrade(const string& solution, const string& x) {
   if (solution.size() != x.size()) {
      cerr << "Mismatch in sizes " 
           << "('" << solution << "' vs '" << x << "') !" 
           << endl;
      exit(1);
   }
   int count = 0;
   double grade = 0.0f;
   int good = 0, bad = 0, not_answered = 0;
   for (int i = 0; i < solution.size(); i++) {
      if (x[i] == 'X') {
         // pregunta anulada: no hay que incrementar contador
      } else if (x[i] == '_') { 
         // no contestada (no suma ni resta, pero es una más)
         not_answered++;
         count++;
      } else if (solution[i] == x[i]) {
         grade += 1.0f;
         good++;
         count++;
      } else if (solution[i] != x[i]) {
         grade -= 1.0/3.0;
         bad++;
         count++;
      }
   }
   /*
   cerr << endl << endl;
   cerr << "good = " << good << endl;
   cerr << "bad = " << bad << endl;
   cerr << "not_answered = " << not_answered << endl;
   */
   return grade / double(count) * 10.0;
}

int main(int argc, char *argv[]) {
   if (argc < 3) {
      fprintf(stderr, "usage: grade <solutions-file> <students-file>\n");
      exit(1);
   }

   Solutions solutions;
   Students students;
   ReadSolutions(argv[1], solutions);
   ReadStudents(argv[2], students);

   for (int i = 0; i < students.size(); i++) {
      if (students[i].DNI != "") {
         cout << i << ';' << students[i].DNI << ';';
         cout << setprecision(1) << fixed
              << ComputeGrade(solutions[i], students[i].answers);
         cout << endl;
      }
   }
}
