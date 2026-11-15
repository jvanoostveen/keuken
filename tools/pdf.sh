#!/bin/zsh
# HTML-document naar PDF (A4 liggend via @page in de HTML) en controle met poppler in een container.
#   tools/pdf.sh ideeen/index.html "Keuken ideeën.pdf"            -> PDF + paginaoverzicht
#   tools/pdf.sh ideeen/index.html "Keuken ideeën.pdf" png <map>  -> ook elke pagina als PNG (60 dpi)
set -e
cd "$(dirname "$0")/.."
html="$1"; pdf="$2"
chrome="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$chrome" --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf="${pdf:A}" "file://$PWD/$html" 2>/dev/null
dir="$(cd "$(dirname "$pdf")" && pwd)"; naam="$(basename "$pdf")"
cmd="pdfinfo '$naam' | grep -E 'Pages|Page size|File size'"
if [[ "$3" == "png" ]]; then
  mkdir -p "$4"
  docker run --rm -v "$dir":/w -v "$(cd "$4" && pwd)":/uit -w /w alpine:3.20 \
    sh -c "apk add -q poppler-utils >/dev/null && $cmd && pdftoppm -r 60 -png '$naam' /uit/p"
else
  docker run --rm -v "$dir":/w -w /w alpine:3.20 sh -c "apk add -q poppler-utils >/dev/null && $cmd"
fi
