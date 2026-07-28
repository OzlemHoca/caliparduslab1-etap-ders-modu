#!/usr/bin/env bash

set -u

UYGULAMA_ADI="ETAP Ders Modu"
KAYNAK_DIZINI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HEDEF_DIZIN="/opt/etap-ders-modu"

MASAUSTU_DOSYASI="caliparduslab2-etap-ders-modu.desktop"
UYGULAMALAR_DIZINI="/usr/share/applications"

GERCEK_KULLANICI="${SUDO_USER:-$USER}"
KULLANICI_EVI="$(getent passwd "${GERCEK_KULLANICI}" | cut -d: -f6)"
KULLANICI_MASAUSTU="${KULLANICI_EVI}/Masaüstü"

echo "=============================================="
echo "${UYGULAMA_ADI} Kurulumu"
echo "=============================================="

if [ "${EUID}" -ne 0 ]; then
    echo "Bu kurulum yönetici yetkisi gerektirir."
    echo
    echo "Şu komutla tekrar çalıştırın:"
    echo "sudo bash install.sh"
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "Hata: Python 3 bulunamadı."
    echo "Kurulum:"
    echo "sudo apt install python3"
    exit 1
fi

if ! command -v xset >/dev/null 2>&1; then
    echo "xset bulunamadı."
    echo "x11-xserver-utils paketi kuruluyor..."

    apt-get update

    if ! apt-get install -y x11-xserver-utils; then
        echo "Hata: x11-xserver-utils kurulamadı."
        exit 1
    fi
fi

echo "Uygulama dosyaları kopyalanıyor..."

rm -rf "${HEDEF_DIZIN}"
mkdir -p "${HEDEF_DIZIN}"

cp -R "${KAYNAK_DIZINI}/src" "${HEDEF_DIZIN}/"
cp "${KAYNAK_DIZINI}/baslat.sh" "${HEDEF_DIZIN}/"

if [ -d "${KAYNAK_DIZINI}/assets" ]; then
    cp -R "${KAYNAK_DIZINI}/assets" "${HEDEF_DIZIN}/"
fi

chmod +x "${HEDEF_DIZIN}/baslat.sh"
chmod +x "${HEDEF_DIZIN}/src/project.py"

echo "Uygulama menüsü kısayolu oluşturuluyor..."

install \
    -m 644 \
    "${KAYNAK_DIZINI}/${MASAUSTU_DOSYASI}" \
    "${UYGULAMALAR_DIZINI}/${MASAUSTU_DOSYASI}"

if [ -d "${KULLANICI_MASAUSTU}" ]; then
    echo "Masaüstü kısayolu oluşturuluyor..."

    install \
        -o "${GERCEK_KULLANICI}" \
        -g "${GERCEK_KULLANICI}" \
        -m 755 \
        "${KAYNAK_DIZINI}/${MASAUSTU_DOSYASI}" \
        "${KULLANICI_MASAUSTU}/ETAP Ders Modu.desktop"

    gio set \
        "${KULLANICI_MASAUSTU}/ETAP Ders Modu.desktop" \
        metadata::trusted true \
        >/dev/null 2>&1 || true
else
    echo "Bilgi: Masaüstü klasörü bulunamadı."
    echo "Kısayol uygulama menüsüne eklendi."
fi

command -v update-desktop-database >/dev/null 2>&1 && \
    update-desktop-database "${UYGULAMALAR_DIZINI}" || true

echo
echo "=============================================="
echo "Kurulum başarıyla tamamlandı."
echo "=============================================="
echo
echo "Uygulama konumu:"
echo "${HEDEF_DIZIN}"
echo
echo "ETAP Ders Modu artık uygulama menüsünden"
echo "ve masaüstü simgesinden çalıştırılabilir."
