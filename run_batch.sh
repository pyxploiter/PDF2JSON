#!/bin/bash
if [ $# -gt 0 ]
then
  DIR="$1"
  # save and change IFS
  OLDIFS=$IFS
  IFS=$'\n'
  # read all file name into an array
  fileArray=($(find $DIR -type f))
  # restore it
  IFS=$OLDIFS
  # get length of an array
  tLen=${#fileArray[@]}
  # use for loop read all filenames
  for (( i=0; i<${tLen}; i++ ));
  do
  	# run script on each pdf file
    python pdf2json.py -i "${fileArray[$i]}" "${@:2}"
  done

else
  echo "[Error] Folder path is not provided."
fi