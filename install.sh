#!/usr/bin/env bash

set -Eeuo pipefail

# ---------------------------------------------------------
# UYGULAMA BİLGİLERİ
# ---------------------------------------------------------

UYGULAMA_ADI="ETAP Ders Modu"
UYGULAMA_KIMLIGI="caliparduslab2-etap-ders-modu"

KAYNAK_DIZINI="$(
    cd "$(dirname "${BASH_SOURCE[0]}")" &&
    pwd
)"

HEDEF_DIZIN="/opt/etap-ders-modu"
UYGULAMALAR_DIZINI="/usr/share/applications"

MASAUSTU_DOSYASI="${UYGULAMA_KIMLIGI}.desktop"
SIMGE_DOSYASI="assets/etap-ders-modu.png"

MOTOR_DOSYASI="src/etap_ders_modu.py"
GUI_DOSYASI="src/etap_ders_modu_gui.py"

BASLATMA_DOSYASI="baslat.sh"


# ---------------------------------------------------------
# YARDIMCI FONKSİYONLAR
# ---------------------------------------------------------

bilgi() {
    echo ">> $1"
}

uyari() {
    echo
    echo "UYARI: $1"
    echo
}

hata() {
    echo
    echo "HATA: $1"
    echo
    exit 1
}

basarili() {
    echo
    echo "=============================================="
    echo "$1"
    echo "=============================================="
    echo
}

komut_var_mi() {
    command -v "$1" >/dev/null 2>&1
}

hata_yakala() {
    local cikis_kodu=$?
    local satir_no=$1

    echo
    echo "Kurulum sırasında beklenmeyen bir hata oluştu."
    echo "Satır: ${satir_no}"
    echo "Çıkış kodu: ${cikis_kodu}"
    echo

    exit "${cikis_kodu}"
}

trap 'hata_yakala ${LINENO}' ERR


# ---------------------------------------------------------
# BAŞLANGIÇ
# ---------------------------------------------------------

echo
echo "=============================================="
echo "${UYGULAMA_ADI} Kurulumu"
echo "=============================================="
echo


# ---------------------------------------------------------
# ROOT KONTROLÜ
# ---------------------------------------------------------

if [ "${EUID}" -ne 0 ]; then
    hata \
        "Bu kurulum yönetici yetkisi gerektirir.

Şu komutla tekrar çalıştırın:

sudo bash install.sh"
fi


# ---------------------------------------------------------
# GERÇEK KULLANICIYI BULMA
# ---------------------------------------------------------

GERCEK_KULLANICI="${SUDO_USER:-}"

if [ -z "${GERCEK_KULLANICI}" ]; then
    GERCEK_KULLANICI="$(
        logname 2>/dev/null || true
    )"
fi

if [ -z "${GERCEK_KULLANICI}" ] || \
   [ "${GERCEK_KULLANICI}" = "root" ]; then

    hata \
        "Kurulumu başlatan normal kullanıcı belirlenemedi.

Kurulumu masaüstü oturumundaki kullanıcı ile çalıştırın:

sudo bash install.sh"
fi

if ! id "${GERCEK_KULLANICI}" >/dev/null 2>&1; then
    hata "Kullanıcı bulunamadı: ${GERCEK_KULLANICI}"
fi

KULLANICI_GRUBU="$(
    id -gn "${GERCEK_KULLANICI}"
)"

KULLANICI_EVI="$(
    getent passwd "${GERCEK_KULLANICI}" |
    cut -d: -f6
)"

if [ -z "${KULLANICI_EVI}" ] || \
   [ ! -d "${KULLANICI_EVI}" ]; then

    hata "Kullanıcının ev dizini belirlenemedi."
fi


# ---------------------------------------------------------
# MASAÜSTÜ KLASÖRÜ
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

    else
        KULLANICI_MASAUSTU="${KULLANICI_EVI}/Masaüstü"
    fi
fi


# ---------------------------------------------------------
# KAYNAK DOSYALAR
# ---------------------------------------------------------

bilgi "Kurulum dosyaları kontrol ediliyor..."

GEREKLI_DOSYALAR=(
    "${KAYNAK_DIZINI}/${MOTOR_DOSYASI}"
    "${KAYNAK_DIZINI}/${GUI_DOSYASI}"
    "${KAYNAK_DIZINI}/${SIMGE_DOSYASI}"
)

for DOSYA in "${GEREKLI_DOSYALAR[@]}"; do
    if [ ! -f "${DOSYA}" ]; then
        hata "Gerekli dosya bulunamadı: ${DOSYA}"
    fi
done


# ---------------------------------------------------------
# PAKET YÖNETİCİSİ
# ---------------------------------------------------------

if ! komut_var_mi apt-get; then
    hata \
        "apt-get paket yöneticisi bulunamadı.

Bu kurulum Pardus ve Debian tabanlı sistemler için hazırlanmıştır."
fi


# ---------------------------------------------------------
# BAĞIMLILIKLAR
# ---------------------------------------------------------

bilgi "Sistem bağımlılıkları kontrol ediliyor..."

EKSIK_PAKETLER=()

if ! komut_var_mi python3; then
    EKSIK_PAKETLER+=("python3")
fi

if komut_var_mi python3; then
    if ! python3 -c "import tkinter" >/dev/null 2>&1; then
        EKSIK_PAKETLER+=("python3-tk")
    fi
else
    EKSIK_PAKETLER+=("python3-tk")
fi

if ! komut_var_mi xset; then
    EKSIK_PAKETLER+=("x11-xserver-utils")
fi

if ! komut_var_mi xfconf-query; then
    EKSIK_PAKETLER+=("xfconf")
fi

if ! komut_var_mi update-desktop-database; then
    EKSIK_PAKETLER+=("desktop-file-utils")
fi

if ! komut_var_mi xdg-user-dir; then
    EKSIK_PAKETLER+=("xdg-user-dirs")
fi

if ! komut_var_mi gio; then
    EKSIK_PAKETLER+=("libglib2.0-bin")
fi

if ! komut_var_mi zenity; then
    EKSIK_PAKETLER+=("zenity")
fi

if ! komut_var_mi notify-send; then
    EKSIK_PAKETLER+=("libnotify-bin")
fi


# ---------------------------------------------------------
# TEKRAR EDEN PAKETLERİ TEMİZLE
# ---------------------------------------------------------

if [ "${#EKSIK_PAKETLER[@]}" -gt 0 ]; then
    TEKIL_PAKETLER=()

    for PAKET in "${EKSIK_PAKETLER[@]}"; do
        PAKET_EKLENDI=false

        for MEVCUT_PAKET in "${TEKIL_PAKETLER[@]}"; do
            if [ "${PAKET}" = "${MEVCUT_PAKET}" ]; then
                PAKET_EKLENDI=true
                break
            fi
        done

        if [ "${PAKET_EKLENDI}" = false ]; then
            TEKIL_PAKETLER+=("${PAKET}")
        fi
    done

    echo
    echo "Aşağıdaki eksik paketler kurulacak:"
    printf ' - %s\n' "${TEKIL_PAKETLER[@]}"
    echo

    bilgi "Paket listesi güncelleniyor..."
    apt-get update

    bilgi "Eksik paketler kuruluyor..."
    apt-get install -y "${TEKIL_PAKETLER[@]}"

else
    bilgi "Gerekli tüm paketler sistemde mevcut."
fi


# ---------------------------------------------------------
# BAĞIMLILIK DOĞRULAMASI
# ---------------------------------------------------------

bilgi "Bağımlılıklar doğrulanıyor..."

komut_var_mi python3 || \
    hata "Python 3 kurulumu doğrulanamadı."

python3 -c "import tkinter" >/dev/null 2>&1 || \
    hata "Tkinter kurulumu doğrulanamadı."

komut_var_mi xset || \
    hata "xset kurulumu doğrulanamadı."

komut_var_mi xfconf-query || \
    hata "xfconf-query kurulumu doğrulanamadı."


# ---------------------------------------------------------
# PYTHON SÖZDİZİMİ KONTROLÜ
# ---------------------------------------------------------

bilgi "Python kaynak kodları kontrol ediliyor..."

python3 -m py_compile \
    "${KAYNAK_DIZINI}/${MOTOR_DOSYASI}" \
    "${KAYNAK_DIZINI}/${GUI_DOSYASI}"


# ---------------------------------------------------------
# ESKİ KURULUM
# ---------------------------------------------------------

if [ -d "${HEDEF_DIZIN}" ]; then
    bilgi "Eski kurulum kaldırılıyor..."
    rm -rf "${HEDEF_DIZIN}"
fi


# ---------------------------------------------------------
# UYGULAMA DOSYALARINI KOPYALA
# ---------------------------------------------------------

bilgi "Uygulama dizini oluşturuluyor..."

mkdir -p \
    "${HEDEF_DIZIN}/src" \
    "${HEDEF_DIZIN}/assets"

bilgi "Uygulama kaynak kodları kopyalanıyor..."

install \
    -m 755 \
    "${KAYNAK_DIZINI}/${MOTOR_DOSYASI}" \
    "${HEDEF_DIZIN}/${MOTOR_DOSYASI}"

install \
    -m 755 \
    "${KAYNAK_DIZINI}/${GUI_DOSYASI}" \
    "${HEDEF_DIZIN}/${GUI_DOSYASI}"

install \
    -m 644 \
    "${KAYNAK_DIZINI}/${SIMGE_DOSYASI}" \
    "${HEDEF_DIZIN}/${SIMGE_DOSYASI}"

if [ -f "${KAYNAK_DIZINI}/README.md" ]; then
    install \
        -m 644 \
        "${KAYNAK_DIZINI}/README.md" \
        "${HEDEF_DIZIN}/README.md"
fi

if [ -f "${KAYNAK_DIZINI}/LICENSE" ]; then
    install \
        -m 644 \
        "${KAYNAK_DIZINI}/LICENSE" \
        "${HEDEF_DIZIN}/LICENSE"
fi

if [ -f "${KAYNAK_DIZINI}/durum.json" ]; then
    install \
        -m 644 \
        "${KAYNAK_DIZINI}/durum.json" \
        "${HEDEF_DIZIN}/durum-ornek.json"
fi

chown -R root:root "${HEDEF_DIZIN}"


# ---------------------------------------------------------
# BAŞLATMA BETİĞİNİ OLUŞTUR
# ---------------------------------------------------------

bilgi "Başlatma betiği oluşturuluyor..."

cat > "${HEDEF_DIZIN}/${BASLATMA_DOSYASI}" <<'BASLAT_EOF'
#!/usr/bin/env bash

set -u

UYGULAMA_DIZINI="/opt/etap-ders-modu"
GUI_DOSYASI="${UYGULAMA_DIZINI}/src/etap_ders_modu_gui.py"

LOG_DIZINI="${HOME}/.config/caliparduslab2-etap-ders-modu"
LOG_DOSYASI="${LOG_DIZINI}/baslatma.log"

mkdir -p "${LOG_DIZINI}"

tarih_yaz() {
    date '+%Y-%m-%d %H:%M:%S'
}

hata_penceresi() {
    local mesaj="$1"

    echo "$(tarih_yaz) - HATA: ${mesaj}" \
        >> "${LOG_DOSYASI}"

    if command -v zenity >/dev/null 2>&1; then
        zenity \
            --error \
            --title="ETAP Ders Modu" \
            --width=450 \
            --text="${mesaj}"
    fi
}

if ! command -v python3 >/dev/null 2>&1; then
    hata_penceresi "Python 3 sistemde bulunamadı."
    exit 1
fi

if ! python3 -c "import tkinter" >/dev/null 2>&1; then
    hata_penceresi "Tkinter bileşeni sistemde bulunamadı."
    exit 1
fi

if [ ! -f "${GUI_DOSYASI}" ]; then
    hata_penceresi \
        "ETAP Ders Modu grafik arayüz dosyası bulunamadı:

${GUI_DOSYASI}"

    exit 1
fi

if [ -z "${DISPLAY:-}" ]; then
    hata_penceresi \
        "Grafik masaüstü oturumuna erişilemiyor.

ETAP Ders Modu masaüstü simgesinden çalıştırılmalıdır."

    exit 1
fi

cd "${UYGULAMA_DIZINI}/src" || {
    hata_penceresi "Uygulama klasörüne erişilemedi."
    exit 1
}

echo "$(tarih_yaz) - Uygulama başlatıldı." \
    >> "${LOG_DOSYASI}"

exec python3 "${GUI_DOSYASI}" \
    >> "${LOG_DOSYASI}" 2>&1
BASLAT_EOF

chmod 755 "${HEDEF_DIZIN}/${BASLATMA_DOSYASI}"


# ---------------------------------------------------------
# DESKTOP DOSYASINI OLUŞTUR
# ---------------------------------------------------------

bilgi "Uygulama menüsü kısayolu oluşturuluyor..."

cat > "${UYGULAMALAR_DIZINI}/${MASAUSTU_DOSYASI}" <<DESKTOP_EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=ETAP Ders Modu
GenericName=Ders Modu Yöneticisi
Comment=Ekranı açık tutun ve ders sırasında bildirimleri susturun
Exec=${HEDEF_DIZIN}/${BASLATMA_DOSYASI}
Icon=${HEDEF_DIZIN}/${SIMGE_DOSYASI}
Terminal=false
Categories=Education;Utility;
Keywords=ETAP;Pardus;Ders;Öğretmen;Ekran;Bildirim;
StartupNotify=true
StartupWMClass=ETAP Ders Modu
DESKTOP_EOF

chmod 644 \
    "${UYGULAMALAR_DIZINI}/${MASAUSTU_DOSYASI}"


# ---------------------------------------------------------
# DESKTOP DOSYASINI DOĞRULA
# ---------------------------------------------------------

if komut_var_mi desktop-file-validate; then
    bilgi "Masaüstü kısayolu doğrulanıyor..."

    desktop-file-validate \
        "${UYGULAMALAR_DIZINI}/${MASAUSTU_DOSYASI}"
fi


# ---------------------------------------------------------
# MASAÜSTÜ KISAYOLU
# ---------------------------------------------------------

bilgi "Masaüstü kısayolu hazırlanıyor..."

mkdir -p "${KULLANICI_MASAUSTU}"

MASAUSTU_HEDEF_DOSYASI="${
    KULLANICI_MASAUSTU
}/ETAP Ders Modu.desktop"

install \
    -o "${GERCEK_KULLANICI}" \
    -g "${KULLANICI_GRUBU}" \
    -m 755 \
    "${UYGULAMALAR_DIZINI}/${MASAUSTU_DOSYASI}" \
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


# ---------------------------------------------------------
# KULLANICI AYAR DİZİNİ
# ---------------------------------------------------------

KULLANICI_AYAR_DIZINI="${
    KULLANICI_EVI
}/.config/${UYGULAMA_KIMLIGI}"

bilgi "Kullanıcı ayar dizini hazırlanıyor..."

mkdir -p "${KULLANICI_AYAR_DIZINI}"

touch "${KULLANICI_AYAR_DIZINI}/baslatma.log"

chown -R \
    "${GERCEK_KULLANICI}:${KULLANICI_GRUBU}" \
    "${KULLANICI_AYAR_DIZINI}"

chmod 700 "${KULLANICI_AYAR_DIZINI}"
chmod 600 "${KULLANICI_AYAR_DIZINI}/baslatma.log"


# ---------------------------------------------------------
# UYGULAMA MENÜSÜ VERİTABANI
# ---------------------------------------------------------

if komut_var_mi update-desktop-database; then
    bilgi "Uygulama menüsü veritabanı güncelleniyor..."

    update-desktop-database \
        "${UYGULAMALAR_DIZINI}" \
        >/dev/null 2>&1 || true
fi


# ---------------------------------------------------------
# KURULUM DOĞRULAMASI
# ---------------------------------------------------------

bilgi "Kurulum doğrulanıyor..."

KURULAN_DOSYALAR=(
    "${HEDEF_DIZIN}/${MOTOR_DOSYASI}"
    "${HEDEF_DIZIN}/${GUI_DOSYASI}"
    "${HEDEF_DIZIN}/${SIMGE_DOSYASI}"
    "${HEDEF_DIZIN}/${BASLATMA_DOSYASI}"
    "${UYGULAMALAR_DIZINI}/${MASAUSTU_DOSYASI}"
    "${MASAUSTU_HEDEF_DOSYASI}"
)

for DOSYA in "${KURULAN_DOSYALAR[@]}"; do
    if [ ! -f "${DOSYA}" ]; then
        hata "Kurulum doğrulaması başarısız: ${DOSYA}"
    fi
done

python3 -m py_compile \
    "${HEDEF_DIZIN}/${MOTOR_DOSYASI}" \
    "${HEDEF_DIZIN}/${GUI_DOSYASI}"


# ---------------------------------------------------------
# TAMAMLAMA
# ---------------------------------------------------------

basarili "${UYGULAMA_ADI} başarıyla kuruldu."

echo "Uygulama dizini:"
echo "${HEDEF_DIZIN}"
echo

echo "Uygulama menüsü kısayolu:"
echo "${UYGULAMALAR_DIZINI}/${MASAUSTU_DOSYASI}"
echo

echo "Masaüstü kısayolu:"
echo "${MASAUSTU_HEDEF_DOSYASI}"
echo

echo "Kullanıcı ayar dizini:"
echo "${KULLANICI_AYAR_DIZINI}"
echo

echo "Uygulamayı masaüstündeki ETAP Ders Modu"
echo "simgesine çift tıklayarak çalıştırabilirsiniz."
echo

exit 0
