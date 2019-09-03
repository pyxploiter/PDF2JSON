if [ $# -gt 0 ]
then
  FILES="${1}/*.pdf"

  for f in $FILES
  do
    python pdf2json.py -i $f "${@:2}"
  done

else
  echo "[Error] Folder path is not provided."
fi


