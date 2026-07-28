#!/usr/bin/env bash

UYGULAMA_DIZINI="/opt/etap-ders-modu"
GUI_DOSYASI="${UYGULAMA_DIZINI}/src/etap_ders_modu_gui.py"
LOG_DOSYASI="${HOME}/.config/caliparduslab2-etap-ders-modu/baslatma.log"

mkdir -p "$(dirname "${LOG_DOSYASI}")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Python 3 bulunamadı." \
        >> "${LOG_DOSYASI}"

    command -v zenity >/dev/null 2>&1 && \
        zenity --error \
        --title="ETAP Ders Modu" \
        --text="Python 3 sistemde bulunamadı."

    exit 1
fi

if [ ! -f "${GUI_DOSYASI}" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - GUI dosyası bulunamadı." \
        >> "${LOG_DOSYASI}"

    command -v zenity >/dev/null 2>&1 && \
        zenity --error \
        --title="ETAP Ders Modu" \
        --text="Uygulama dosyası bulunamadı:\n${GUI_DOSYASI}"

    exit 1
fi

cd "${UYGULAMA_DIZINI}/src" || exit 1

exec python3 "${GUI_DOSYASI}" >> "${LOG_DOSYASI}" 2>&1
