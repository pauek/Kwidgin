#!/bin/bash

if [ $# -lt 3 ]; then
   echo "usage: control.sh [options...] <Tema> <Date YYYY-MM-DD> <Problems>..."
   echo "   --two-column"
   echo "   --show-topics"
   echo "   --temps <temps>"
   echo
   exit 1
fi

show_topics='no'
two_column=''
temps='50 minuts'
while true ; do
   case "$1" in 
      --show-topics)
         show_topics='yes'
         shift 1
         ;;
      
      --two-column)
         two_column='[twocolumn]'
         shift 1
         ;;

      --temps)
         shift 1
         temps=$1
         shift 1
         ;;

      *) break ;;
   esac
done

subject=$1
date=$2
shift 1 # OJO, debería ser 2 pero dejamos 1 para el bucle!!!!

cat > /tmp/template.tex <<EOF
\$body
EOF

if [ -z $MINIDOSIS_ROOT ]; then
    echo "MINIDOSIS_ROOT not set"
    exit 1
fi

# Preamble
cat <<EOF
\documentclass${two_column}{control}
\usepackage[defaultmono,scale=.8]{droidmono}
\usepackage{multicol}
\usepackage{longtable,ltcaption,array}
\newlength{\DUtablewidth}
\usepackage{hyperref}
\usepackage{t1enc}
\usepackage{alltt}

\Assignatura{EDOO}
\Especialitat{Grau d'Audiovisuals}
\Examen{$subject}
\TempsMaxim{$temps}
\chead{$date}

\begin{document}
EOF


pushd $MINIDOSIS_ROOT &> /dev/null
while true; do
   shift 1
   if [ $# == 0 ]; then
      break
   fi
   file="$1"
   if [ "$file" == "[pagebreak]" ]; then
      echo "\vfill\pagebreak"
      continue
   elif [ ${file:0:1} == '\' ]; then
      echo $file
      continue
   elif [ ${file:0:1} == '+' ]; then
      punts=${file:1}
      echo "[$punts]" > /dev/stderr
      continue
   fi

   path=$(find -path '*'$file'*.minidosis' -type f | head -n 1 | cut -c3-)
   echo $path > /dev/stderr

   title=$(title $path)
   if ! [ -z "$punts" ]; then
      title="$title [$punts]"
      punts=""
   fi
   topics=''
   if [ $show_topics == 'yes' ]; then
       topics=$(targets $path)
       echo $topics > /dev/stderr
   fi
   echo "\problema[$topics]{$title}"
   echo

   if [ -z $path ]; then
      echo "Problem \"${path}\" not found" > /dev/stderr
      continue
   fi
   rstfile=$(mktemp --suffix=.rst minidosis-XXXXXX) || (
      echo "Couldn't create temp file for ${file}" > /dev/stderr
      exit 1;
   )
   sed '/^{/,/^}/d' $path | title_refs > $rstfile
   cp $rstfile /tmp/pauek.rst
   rst2latex --template=/tmp/template.tex $rstfile

   rm -f $rstfile
done
popd &> /dev/null

cat <<EOF
\end{document}
EOF

rm -f /tmp/template.tex
