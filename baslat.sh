#!/usr/bin/env bash

UYGULAMA_DIZINI="/opt/etap-ders-modu"
PYTHON_DOSYASI="${UYGULAMA_DIZINI}/src/project.py"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Hata: Python 3 sistemde bulunamadı."
    read -r -p "Kapatmak için Enter tuşuna basın..."
    exit 1
fi

if [ ! -f "${PYTHON_DOSYASI}" ]; then
    echo "Hata: ETAP Ders Modu uygulama dosyası bulunamadı."
    echo "Beklenen dosya: ${PYTHON_DOSYASI}"
    read -r -p "Kapatmak için Enter tuşuna basın..."
    exit 1
fi

cd "${UYGULAMA_DIZINI}" || {
    echo "Hata: Uygulama klasörüne geçilemedi."
    read -r -p "Kapatmak için Enter tuşuna basın..."
    exit 1
}

exec python3 "${PYTHON_DOSYASI}"
