#!/usr/bin/env bash

set -u

# ---------------------------------------------------------
# UYGULAMA BİLGİLERİ
# ---------------------------------------------------------

UYGULAMA_ADI="ETAP Ders Modu"
UYGULAMA_KIMLIGI="caliparduslab2-etap-ders-modu"

KAYNAK_DIZINI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HEDEF_DIZIN="/opt/etap-ders-modu"

MASAUSTU_DOSYASI="${UYGULAMA_KIMLIGI}.desktop"
UYGULAMALAR_DIZINI="/usr/share/applications"

BASLATMA_DOSYASI="baslat.sh"
GUI_DOSYASI="src/etap_ders_modu_gui.py"
TERMINAL_DOSYASI="src/project.py"

SIMGE_DOSYASI="assets/etap-ders-modu.png"


# ---------------------------------------------------------
# YARDIMCI FONKSİYONLAR
# ---------------------------------------------------------

hata_mesaji() {
    echo
    echo "HATA: $1"
    echo
}

bilgi_mesaji() {
    echo ">> $1"
}

basari_mesaji() {
    echo
    echo "=============================================="
    echo "$1"
    echo "=============================================="
    echo
}

komut_var_mi() {
    command -v "$1" >/dev/null 2>&1
}

dosya_var_mi() {
    [ -f "$1" ]
}

dizin_var_mi() {
    [ -d "$1" ]
}


# ---------------------------------------------------------
# BAŞLANGIÇ
# ---------------------------------------------------------

echo
echo "=============================================="
echo "${UYGULAMA_ADI} Kurulumu"
echo "=============================================="
echo


# ---------------------------------------------------------
# YÖNETİCİ YETKİSİ KONTROLÜ
# ---------------------------------------------------------

if [ "${EUID}" -ne 0 ]; then
    hata_mesaji "Bu kurulum yönetici yetkisi gerektirir."

    echo "Kurulumu şu komutla tekrar çalıştırın:"
    echo
    echo "sudo bash install.sh"
    echo

    exit 1
fi


# ---------------------------------------------------------
# GERÇEK KULLANICIYI BELİRLEME
# ---------------------------------------------------------

GERCEK_KULLANICI="${SUDO_USER:-}"

if [ -z "${GERCEK_KULLANICI}" ]; then
    GERCEK_KULLANICI="$(logname 2>/dev/null || true)"
fi

if [ -z "${GERCEK_KULLANICI}" ] || \
   [ "${GERCEK_KULLANICI}" = "root" ]; then

    hata_mesaji "Kurulumu başlatan normal kullanıcı belirlenemedi."

    echo "Kurulumu masaüstü oturumundaki kullanıcıyla şu şekilde başlatın:"
    echo
    echo "sudo bash install.sh"
    echo

    exit 1
fi

KULLANICI_KIMLIGI="$(id -u "${GERCEK_KULLANICI}")"
KULLANICI_GRUBU="$(id -gn "${GERCEK_KULLANICI}")"

KULLANICI_EVI="$(
    getent passwd "${GERCEK_KULLANICI}" |
    cut -d: -f6
)"

if [ -z "${KULLANICI_EVI}" ] || \
   [ ! -d "${KULLANICI_EVI}" ]; then

    hata_mesaji "Kullanıcı ev dizini belirlenemedi."
    exit 1
fi


# ---------------------------------------------------------
# MASAÜSTÜ KLASÖRÜNÜ BELİRLEME
# ---------------------------------------------------------

KULLANICI_MASAUSTU=""

if komut_var_mi xdg-user-dir; then
    KULLANICI_MASAUSTU="$(
        sudo -u "${GERCEK_KULLANICI}" \
        HOME="${KULLANICI_EVI}" \
        xdg-user-dir DESKTOP 2>/dev/null || true
    )"
fi

if [ -z "${KULLANICI_MASAUSTU}" ]; then
    if [ -d "${KULLANICI_EVI}/Masaüstü" ]; then
        KULLANICI_MASAUSTU="${KULLANICI_EVI}/Masaüstü"

    elif [ -d "${KULLANICI_EVI}/Desktop" ]; then
        KULLANICI_MASAUSTU="${KULLANICI_EVI}/Desktop"
    fi
fi


# ---------------------------------------------------------
# KAYNAK DOSYA KONTROLLERİ
# ---------------------------------------------------------

bilgi_mesaji "Kurulum dosyaları kontrol ediliyor..."

GEREKLI_DOSYALAR=(
    "${KAYNAK_DIZINI}/${BASLATMA_DOSYASI}"
    "${KAYNAK_DIZINI}/${MASAUSTU_DOSYASI}"
    "${KAYNAK_DIZINI}/${GUI_DOSYASI}"
    "${KAYNAK_DIZINI}/${TERMINAL_DOSYASI}"
    "${KAYNAK_DIZINI}/${SIMGE_DOSYASI}"
)

for DOSYA in "${GEREKLI_DOSYALAR[@]}"; do
    if ! dosya_var_mi "${DOSYA}"; then
        hata_mesaji "Gerekli dosya bulunamadı: ${DOSYA}"
        exit 1
    fi
done


# ---------------------------------------------------------
# PAKET YÖNETİCİSİ KONTROLÜ
# ---------------------------------------------------------

if ! komut_var_mi apt-get; then
    hata_mesaji "apt-get paket yöneticisi bulunamadı."
    echo "Bu kurulum Pardus ve Debian tabanlı sistemler için hazırlanmıştır."
    exit 1
fi


# ---------------------------------------------------------
# BAĞIMLILIK KONTROLLERİ
# ---------------------------------------------------------

bilgi_mesaji "Sistem bağımlılıkları kontrol ediliyor..."

EKSIK_PAKETLER=()


# Python 3

if ! komut_var_mi python3; then
    EKSIK_PAKETLER+=("python3")
fi


# Tkinter

if komut_var_mi python3; then
    if ! python3 -c "import tkinter" >/dev/null 2>&1; then
        EKSIK_PAKETLER+=("python3-tk")
    fi
else
    EKSIK_PAKETLER+=("python3-tk")
fi


# xset

if ! komut_var_mi xset; then
    EKSIK_PAKETLER+=("x11-xserver-utils")
fi


# Masaüstü veritabanı güncellemesi

if ! komut_var_mi update-desktop-database; then
    EKSIK_PAKETLER+=("desktop-file-utils")
fi


# xdg-user-dir desteği

if ! komut_var_mi xdg-user-dir; then
    EKSIK_PAKETLER+=("xdg-user-dirs")
fi


# gio çoğunlukla GLib ile gelir

if ! komut_var_mi gio; then
    EKSIK_PAKETLER+=("libglib2.0-bin")
fi


# Zenity hata pencereleri için önerilir

if ! komut_var_mi zenity; then
    EKSIK_PAKETLER+=("zenity")
fi


# Aynı paketin iki kez eklenmesini engelle

if [ "${#EKSIK_PAKETLER[@]}" -gt 0 ]; then
    TEKIL_PAKETLER=()

    for PAKET in "${EKSIK_PAKETLER[@]}"; do
        PAKET_VAR=false

        for EKLENMIS_PAKET in "${TEKIL_PAKETLER[@]}"; do
            if [ "${PAKET}" = "${EKLENMIS_PAKET}" ]; then
                PAKET_VAR=true
                break
            fi
        done

        if [ "${PAKET_VAR}" = false ]; then
            TEKIL_PAKETLER+=("${PAKET}")
        fi
    done

    echo
    echo "Aşağıdaki eksik paketler kurulacak:"
    printf ' - %s\n' "${TEKIL_PAKETLER[@]}"
    echo

    bilgi_mesaji "Paket listesi güncelleniyor..."

    if ! apt-get update; then
        hata_mesaji "Paket listesi güncellenemedi."
        exit 1
    fi

    bilgi_mesaji "Eksik paketler kuruluyor..."

    if ! apt-get install -y "${TEKIL_PAKETLER[@]}"; then
        hata_mesaji "Gerekli paketlerden biri veya birkaçı kurulamadı."
        exit 1
    fi
else
    bilgi_mesaji "Gerekli tüm paketler sistemde mevcut."
fi


# ---------------------------------------------------------
# BAĞIMLILIK SON KONTROLÜ
# ---------------------------------------------------------

bilgi_mesaji "Bağımlılıklar doğrulanıyor..."

if ! komut_var_mi python3; then
    hata_mesaji "Python 3 kurulumu doğrulanamadı."
    exit 1
fi

if ! python3 -c "import tkinter" >/dev/null 2>&1; then
    hata_mesaji "Tkinter kurulumu doğrulanamadı."
    exit 1
fi

if ! komut_var_mi xset; then
    hata_mesaji "xset kurulumu doğrulanamadı."
    exit 1
fi


# ---------------------------------------------------------
# ESKİ KURULUMU TEMİZLEME
# ---------------------------------------------------------

bilgi_mesaji "Eski kurulum kontrol ediliyor..."

if dizin_var_mi "${HEDEF_DIZIN}"; then
    bilgi_mesaji "Mevcut kurulum kaldırılıyor..."
    rm -rf "${HEDEF_DIZIN}"
fi


# ---------------------------------------------------------
# UYGULAMA DİZİNİNİ OLUŞTURMA
# ---------------------------------------------------------

bilgi_mesaji "Uygulama dizini oluşturuluyor..."

mkdir -p "${HEDEF_DIZIN}"

if [ ! -d "${HEDEF_DIZIN}" ]; then
    hata_mesaji "Uygulama dizini oluşturulamadı."
    exit 1
fi


# ---------------------------------------------------------
# UYGULAMA DOSYALARINI KOPYALAMA
# ---------------------------------------------------------

bilgi_mesaji "Uygulama dosyaları kopyalanıyor..."

cp -R "${KAYNAK_DIZINI}/src" "${HEDEF_DIZIN}/"
cp -R "${KAYNAK_DIZINI}/assets" "${HEDEF_DIZIN}/"
cp "${KAYNAK_DIZINI}/${BASLATMA_DOSYASI}" "${HEDEF_DIZIN}/"

if [ -d "${KAYNAK_DIZINI}/docs" ]; then
    cp -R "${KAYNAK_DIZINI}/docs" "${HEDEF_DIZIN}/"
fi

if [ -f "${KAYNAK_DIZINI}/README.md" ]; then
    cp "${KAYNAK_DIZINI}/README.md" "${HEDEF_DIZIN}/"
fi

if [ -f "${KAYNAK_DIZINI}/LICENSE" ]; then
    cp "${KAYNAK_DIZINI}/LICENSE" "${HEDEF_DIZIN}/"
fi


# ---------------------------------------------------------
# DOSYA İZİNLERİ
# ---------------------------------------------------------

bilgi_mesaji "Dosya izinleri düzenleniyor..."

chmod 755 "${HEDEF_DIZIN}/${BASLATMA_DOSYASI}"
chmod 755 "${HEDEF_DIZIN}/${GUI_DOSYASI}"
chmod 755 "${HEDEF_DIZIN}/${TERMINAL_DOSYASI}"

find "${HEDEF_DIZIN}" -type d -exec chmod 755 {} \;
find "${HEDEF_DIZIN}" -type f -exec chmod 644 {} \;

chmod 755 "${HEDEF_DIZIN}/${BASLATMA_DOSYASI}"
chmod 755 "${HEDEF_DIZIN}/${GUI_DOSYASI}"
chmod 755 "${HEDEF_DIZIN}/${TERMINAL_DOSYASI}"

chown -R root:root "${HEDEF_DIZIN}"


# ---------------------------------------------------------
# UYGULAMA MENÜSÜ KISAYOLU
# ---------------------------------------------------------

bilgi_mesaji "Uygulama menüsü kısayolu oluşturuluyor..."

install \
    -m 644 \
    "${KAYNAK_DIZINI}/${MASAUSTU_DOSYASI}" \
    "${UYGULAMALAR_DIZINI}/${MASAUSTU_DOSYASI}"

if [ ! -f "${UYGULAMALAR_DIZINI}/${MASAUSTU_DOSYASI}" ]; then
    hata_mesaji "Uygulama menüsü kısayolu oluşturulamadı."
    exit 1
fi


# ---------------------------------------------------------
# DESKTOP DOSYASINI DOĞRULAMA
# ---------------------------------------------------------

if komut_var_mi desktop-file-validate; then
    bilgi_mesaji "Masaüstü kısayolu doğrulanıyor..."

    if ! desktop-file-validate \
        "${UYGULAMALAR_DIZINI}/${MASAUSTU_DOSYASI}"; then

        hata_mesaji "Masaüstü kısayol dosyası geçerli değil."
        exit 1
    fi
fi


# ---------------------------------------------------------
# MASAÜSTÜ KISAYOLU
# ---------------------------------------------------------

if [ -n "${KULLANICI_MASAUSTU}" ]; then
    bilgi_mesaji "Masaüstü kısayolu oluşturuluyor..."

    mkdir -p "${KULLANICI_MASAUSTU}"

    MASAUSTU_HEDEF_DOSYASI="${
        KULLANICI_MASAUSTU
    }/ETAP Ders Modu.desktop"

    install \
        -o "${GERCEK_KULLANICI}" \
        -g "${KULLANICI_GRUBU}" \
        -m 755 \
        "${KAYNAK_DIZINI}/${MASAUSTU_DOSYASI}" \
        "${MASAUSTU_HEDEF_DOSYASI}"

    if komut_var_mi gio; then
        sudo -u "${GERCEK_KULLANICI}" \
            HOME="${KULLANICI_EVI}" \
            gio set \
            "${MASAUSTU_HEDEF_DOSYASI}" \
            metadata::trusted true \
            >/dev/null 2>&1 || true
    fi

    chown \
        "${GERCEK_KULLANICI}:${KULLANICI_GRUBU}" \
        "${MASAUSTU_HEDEF_DOSYASI}"
else
    echo
    echo "Bilgi: Kullanıcının masaüstü klasörü bulunamadı."
    echo "Uygulama yalnızca uygulama menüsüne eklendi."
    echo
fi


# ---------------------------------------------------------
# UYGULAMA VERİ KLASÖRÜ
# ---------------------------------------------------------

KULLANICI_AYAR_DIZINI="${
    KULLANICI_EVI
}/.config/${UYGULAMA_KIMLIGI}"

bilgi_mesaji "Kullanıcı ayar dizini hazırlanıyor..."

mkdir -p "${KULLANICI_AYAR_DIZINI}"

chown -R \
    "${GERCEK_KULLANICI}:${KULLANICI_GRUBU}" \
    "${KULLANICI_AYAR_DIZINI}"

chmod 700 "${KULLANICI_AYAR_DIZINI}"


# ---------------------------------------------------------
# MASAÜSTÜ VERİTABANINI GÜNCELLEME
# ---------------------------------------------------------

if komut_var_mi update-desktop-database; then
    bilgi_mesaji "Uygulama menüsü veritabanı güncelleniyor..."

    update-desktop-database \
        "${UYGULAMALAR_DIZINI}" \
        >/dev/null 2>&1 || true
fi


# ---------------------------------------------------------
# SİMGE ÖNBELLEĞİNİ GÜNCELLEME
# ---------------------------------------------------------

if komut_var_mi gtk-update-icon-cache; then
    gtk-update-icon-cache \
        -f \
        -t \
        /usr/share/icons/hicolor \
        >/dev/null 2>&1 || true
fi


# ---------------------------------------------------------
# KURULUM SONRASI DOSYA KONTROLLERİ
# ---------------------------------------------------------

bilgi_mesaji "Kurulum doğrulanıyor..."

KURULAN_DOSYALAR=(
    "${HEDEF_DIZIN}/${BASLATMA_DOSYASI}"
    "${HEDEF_DIZIN}/${GUI_DOSYASI}"
    "${HEDEF_DIZIN}/${TERMINAL_DOSYASI}"
    "${HEDEF_DIZIN}/${SIMGE_DOSYASI}"
    "${UYGULAMALAR_DIZINI}/${MASAUSTU_DOSYASI}"
)

for DOSYA in "${KURULAN_DOSYALAR[@]}"; do
    if ! dosya_var_mi "${DOSYA}"; then
        hata_mesaji "Kurulum doğrulaması başarısız: ${DOSYA}"
        exit 1
    fi
done


# ---------------------------------------------------------
# PYTHON DOSYALARINI SÖZDİZİMİ KONTROLÜ
# ---------------------------------------------------------

bilgi_mesaji "Python dosyaları kontrol ediliyor..."

if ! python3 -m py_compile \
    "${HEDEF_DIZIN}/${TERMINAL_DOSYASI}" \
    "${HEDEF_DIZIN}/${GUI_DOSYASI}"; then

    hata_mesaji "Python dosyalarında sözdizimi hatası bulundu."
    exit 1
fi


# ---------------------------------------------------------
# TAMAMLAMA
# ---------------------------------------------------------

basari_mesaji "${UYGULAMA_ADI} başarıyla kuruldu."

echo "Kurulum bilgileri:"
echo
echo "Uygulama dizini:"
echo "${HEDEF_DIZIN}"
echo
echo "Uygulama menüsü kısayolu:"
echo "${UYGULAMALAR_DIZINI}/${MASAUSTU_DOSYASI}"
echo

if [ -n "${KULLANICI_MASAUSTU}" ]; then
    echo "Masaüstü kısayolu:"
    echo "${KULLANICI_MASAUSTU}/ETAP Ders Modu.desktop"
    echo
fi

echo "Uygulamayı:"
echo
echo "• Masaüstündeki ETAP Ders Modu simgesinden"
echo "• Pardus uygulama menüsünden"
echo
echo "çalıştırabilirsiniz."
echo

exit 0
