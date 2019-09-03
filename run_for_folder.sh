FILES="${1}/*.pdf"

for f in $FILES
do
  python pdf2json.py -i $f "${@:2}"
done
