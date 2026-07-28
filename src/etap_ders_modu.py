#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------
# UYGULAMA BİLGİLERİ
# ---------------------------------------------------------

UYGULAMA_ADI = "ETAP Ders Modu"
UYGULAMA_SURUMU = "0.3.0"
UYGULAMA_KIMLIGI = "caliparduslab2-etap-ders-modu"

AYAR_KLASORU = Path.home() / ".config" / UYGULAMA_KIMLIGI
DURUM_DOSYASI = AYAR_KLASORU / "durum.json"


# ---------------------------------------------------------
# GENEL YARDIMCI FONKSİYONLAR
# ---------------------------------------------------------

def komut_var_mi(komut: str) -> bool:
    """Bir sistem komutunun kurulu olup olmadığını kontrol eder."""

    return shutil.which(komut) is not None


def komut_calistir(
    komut: List[str],
    zaman_asimi: int = 10
) -> Tuple[bool, str]:
    """
    Verilen sistem komutunu çalıştırır.

    Dönüş:
        başarılı mı,
        çıktı veya hata mesajı
    """

    try:
        sonuc = subprocess.run(
            komut,
            capture_output=True,
            text=True,
            check=False,
            timeout=zaman_asimi,
            env=os.environ.copy()
        )

        standart_cikti = sonuc.stdout.strip()
        hata_ciktisi = sonuc.stderr.strip()

        if sonuc.returncode == 0:
            return True, standart_cikti

        mesaj = hata_ciktisi or standart_cikti

        if not mesaj:
            mesaj = (
                f"Komut başarısız oldu. "
                f"Çıkış kodu: {sonuc.returncode}"
            )

        return False, mesaj

    except FileNotFoundError:
        return False, f"{komut[0]} komutu bulunamadı."

    except subprocess.TimeoutExpired:
        return False, "Komut zaman aşımına uğradı."

    except PermissionError:
        return False, "Komutu çalıştırmak için izin bulunamadı."

    except OSError as hata:
        return False, str(hata)


def ayar_klasorunu_hazirla() -> Tuple[bool, str]:
    """Kullanıcıya ait uygulama ayar klasörünü oluşturur."""

    try:
        AYAR_KLASORU.mkdir(
            parents=True,
            exist_ok=True
        )

        AYAR_KLASORU.chmod(0o700)

        return True, "Ayar klasörü hazırlandı."

    except PermissionError:
        return (
            False,
            "Uygulama ayar klasörünü oluşturmak için izin bulunamadı."
        )

    except OSError as hata:
        return False, f"Ayar klasörü oluşturulamadı: {hata}"


def durum_dosyasini_oku() -> Optional[Dict[str, Any]]:
    """Ders modu durum dosyasını okur."""

    if not DURUM_DOSYASI.exists():
        return None

    try:
        with DURUM_DOSYASI.open(
            "r",
            encoding="utf-8"
        ) as dosya:
            veri = json.load(dosya)

        if not isinstance(veri, dict):
            return None

        return veri

    except (json.JSONDecodeError, OSError):
        return None


def durum_dosyasini_yaz(
    durum: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Durum bilgisini güvenli ve atomik biçimde kaydeder.

    Önce geçici dosyaya yazılır, daha sonra gerçek durum
    dosyasının üzerine taşınır.
    """

    basarili, mesaj = ayar_klasorunu_hazirla()

    if not basarili:
        return False, mesaj

    gecici_dosya_yolu: Optional[str] = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(AYAR_KLASORU),
            prefix="durum_",
            suffix=".json",
            delete=False
        ) as gecici_dosya:

            gecici_dosya_yolu = gecici_dosya.name

            json.dump(
                durum,
                gecici_dosya,
                ensure_ascii=False,
                indent=4
            )

            gecici_dosya.flush()
            os.fsync(gecici_dosya.fileno())

        os.replace(
            gecici_dosya_yolu,
            DURUM_DOSYASI
        )

        DURUM_DOSYASI.chmod(0o600)

        return True, "Durum dosyası kaydedildi."

    except OSError as hata:
        if gecici_dosya_yolu:
            try:
                Path(gecici_dosya_yolu).unlink(
                    missing_ok=True
                )
            except OSError:
                pass

        return False, f"Durum dosyası kaydedilemedi: {hata}"


def durum_dosyasini_sil() -> Tuple[bool, str]:
    """Ders modu durum dosyasını siler."""

    if not DURUM_DOSYASI.exists():
        return True, "Durum dosyası zaten bulunmuyor."

    try:
        DURUM_DOSYASI.unlink()
        return True, "Durum dosyası silindi."

    except OSError as hata:
        return False, f"Durum dosyası silinemedi: {hata}"


def ders_modu_aktif_mi() -> bool:
    """Kayıtlı duruma göre ders modunun aktifliğini döndürür."""

    durum = durum_dosyasini_oku()

    if not durum:
        return False

    return durum.get("ders_modu_aktif") is True


def baslangic_zamanini_al() -> Optional[datetime]:
    """Kayıtlı ders başlangıç zamanını döndürür."""

    durum = durum_dosyasini_oku()

    if not durum:
        return None

    baslangic_metni = durum.get("baslangic_zamani")

    if not isinstance(baslangic_metni, str):
        return None

    try:
        return datetime.fromisoformat(baslangic_metni)

    except ValueError:
        return None


# ---------------------------------------------------------
# EKRAN VE XSET İŞLEMLERİ
# ---------------------------------------------------------

def grafik_oturumu_var_mi() -> bool:
    """X11 grafik oturumunun erişilebilirliğini kontrol eder."""

    return bool(os.environ.get("DISPLAY"))


def xset_bilgisi_al() -> Tuple[bool, str]:
    """Mevcut ekran koruyucu ve DPMS ayarlarını okur."""

    if not komut_var_mi("xset"):
        return False, "xset komutu sistemde bulunamadı."

    if not grafik_oturumu_var_mi():
        return (
            False,
            (
                "Grafik masaüstü oturumuna erişilemiyor. "
                "DISPLAY ortam değişkeni bulunamadı."
            )
        )

    return komut_calistir(["xset", "q"])


def xset_ayarlarini_ayristir(
    xset_ciktisi: str
) -> Dict[str, Any]:
    """xset q çıktısından ekran ayarlarını ayrıştırır."""

    ayarlar: Dict[str, Any] = {
        "ekran_koruyucu_zaman_asimi": 0,
        "ekran_koruyucu_dongu": 0,
        "ekran_koruyucu_prefer_blank": True,
        "ekran_koruyucu_allow_exposures": True,
        "dpms_destekleniyor": False,
        "dpms_etkin": False,
        "dpms_bekleme": 0,
        "dpms_askiya_alma": 0,
        "dpms_kapanma": 0
    }

    ekran_eslesmesi = re.search(
        r"timeout:\s*(\d+)\s+cycle:\s*(\d+)",
        xset_ciktisi,
        re.IGNORECASE
    )

    if ekran_eslesmesi:
        ayarlar["ekran_koruyucu_zaman_asimi"] = int(
            ekran_eslesmesi.group(1)
        )

        ayarlar["ekran_koruyucu_dongu"] = int(
            ekran_eslesmesi.group(2)
        )

    ayarlar["ekran_koruyucu_prefer_blank"] = bool(
        re.search(
            r"prefer blanking:\s*yes",
            xset_ciktisi,
            re.IGNORECASE
        )
    )

    ayarlar["ekran_koruyucu_allow_exposures"] = bool(
        re.search(
            r"allow exposures:\s*yes",
            xset_ciktisi,
            re.IGNORECASE
        )
    )

    ayarlar["dpms_destekleniyor"] = bool(
        re.search(
            r"DPMS \(Energy Star\):",
            xset_ciktisi,
            re.IGNORECASE
        )
    )

    ayarlar["dpms_etkin"] = bool(
        re.search(
            r"DPMS is Enabled",
            xset_ciktisi,
            re.IGNORECASE
        )
    )

    dpms_eslesmesi = re.search(
        (
            r"Standby:\s*(\d+)\s+"
            r"Suspend:\s*(\d+)\s+"
            r"Off:\s*(\d+)"
        ),
        xset_ciktisi,
        re.IGNORECASE
    )

    if dpms_eslesmesi:
        ayarlar["dpms_bekleme"] = int(
            dpms_eslesmesi.group(1)
        )

        ayarlar["dpms_askiya_alma"] = int(
            dpms_eslesmesi.group(2)
        )

        ayarlar["dpms_kapanma"] = int(
            dpms_eslesmesi.group(3)
        )

    return ayarlar


def ekran_uyku_modunu_kapat() -> Tuple[bool, str]:
    """
    Ekran koruyucuyu ve DPMS güç yönetimini geçici olarak kapatır.
    """

    komutlar = [
        ["xset", "s", "off"],
        ["xset", "s", "noblank"]
    ]

    basarili, xset_ciktisi = xset_bilgisi_al()

    if not basarili:
        return False, xset_ciktisi

    mevcut_ayarlar = xset_ayarlarini_ayristir(
        xset_ciktisi
    )

    if mevcut_ayarlar.get("dpms_destekleniyor"):
        komutlar.append(["xset", "-dpms"])

    hatalar: List[str] = []

    for komut in komutlar:
        komut_basarili, mesaj = komut_calistir(komut)

        if not komut_basarili:
            hatalar.append(
                f"{' '.join(komut)}: {mesaj}"
            )

    if hatalar:
        return False, "\n".join(hatalar)

    return (
        True,
        (
            "Ekran koruyucu ve ekran güç yönetimi "
            "geçici olarak kapatıldı."
        )
    )


def ekran_ayarlarini_geri_yukle(
    onceki_ayarlar: Dict[str, Any]
) -> Tuple[bool, str]:
    """Ders modu öncesindeki ekran ayarlarını geri yükler."""

    zaman_asimi = int(
        onceki_ayarlar.get(
            "ekran_koruyucu_zaman_asimi",
            0
        )
    )

    dongu = int(
        onceki_ayarlar.get(
            "ekran_koruyucu_dongu",
            0
        )
    )

    prefer_blank = bool(
        onceki_ayarlar.get(
            "ekran_koruyucu_prefer_blank",
            True
        )
    )

    allow_exposures = bool(
        onceki_ayarlar.get(
            "ekran_koruyucu_allow_exposures",
            True
        )
    )

    dpms_destekleniyor = bool(
        onceki_ayarlar.get(
            "dpms_destekleniyor",
            False
        )
    )

    dpms_etkin = bool(
        onceki_ayarlar.get(
            "dpms_etkin",
            False
        )
    )

    dpms_bekleme = int(
        onceki_ayarlar.get(
            "dpms_bekleme",
            0
        )
    )

    dpms_askiya_alma = int(
        onceki_ayarlar.get(
            "dpms_askiya_alma",
            0
        )
    )

    dpms_kapanma = int(
        onceki_ayarlar.get(
            "dpms_kapanma",
            0
        )
    )

    komutlar: List[List[str]] = [
        [
            "xset",
            "s",
            str(zaman_asimi),
            str(dongu)
        ]
    ]

    if prefer_blank:
        komutlar.append(["xset", "s", "blank"])
    else:
        komutlar.append(["xset", "s", "noblank"])

    if allow_exposures:
        komutlar.append(["xset", "s", "expose"])
    else:
        komutlar.append(["xset", "s", "noexpose"])

    if dpms_destekleniyor:
        if dpms_etkin:
            komutlar.extend(
                [
                    ["xset", "+dpms"],
                    [
                        "xset",
                        "dpms",
                        str(dpms_bekleme),
                        str(dpms_askiya_alma),
                        str(dpms_kapanma)
                    ]
                ]
            )
        else:
            komutlar.append(["xset", "-dpms"])

    hatalar: List[str] = []

    for komut in komutlar:
        basarili, mesaj = komut_calistir(komut)

        if not basarili:
            hatalar.append(
                f"{' '.join(komut)}: {mesaj}"
            )

    if hatalar:
        return False, "\n".join(hatalar)

    return True, "Önceki ekran ayarları geri yüklendi."


# ---------------------------------------------------------
# BİLDİRİM SİSTEMİ
# ---------------------------------------------------------

def masaustu_ortamini_al() -> str:
    """Kullanılan masaüstü ortamını belirlemeye çalışır."""

    ortam_degerleri = [
        os.environ.get("XDG_CURRENT_DESKTOP", ""),
        os.environ.get("XDG_SESSION_DESKTOP", ""),
        os.environ.get("DESKTOP_SESSION", ""),
        os.environ.get("GDMSESSION", "")
    ]

    masaustu_metni = " ".join(
        ortam_degerleri
    ).lower()

    if "xfce" in masaustu_metni:
        return "xfce"

    if "gnome" in masaustu_metni:
        return "gnome"

    if "cinnamon" in masaustu_metni:
        return "cinnamon"

    if "mate" in masaustu_metni:
        return "mate"

    if "kde" in masaustu_metni or "plasma" in masaustu_metni:
        return "kde"

    return "bilinmiyor"


def metni_bool_degerine_cevir(
    deger: str
) -> Optional[bool]:
    """true ve false metinlerini boolean değere dönüştürür."""

    temiz_deger = deger.strip().lower()

    temiz_deger = temiz_deger.replace(
        "'",
        ""
    )

    if temiz_deger == "true":
        return True

    if temiz_deger == "false":
        return False

    return None


# ---------------------------------------------------------
# XFCE BİLDİRİM SİSTEMİ
# ---------------------------------------------------------

def xfce_bildirim_ozelligi_var_mi() -> bool:
    """Xfce Rahatsız Etmeyin özelliğini kontrol eder."""

    if not komut_var_mi("xfconf-query"):
        return False

    basarili, _ = komut_calistir(
        [
            "xfconf-query",
            "-c",
            "xfce4-notifyd",
            "-p",
            "/do-not-disturb"
        ]
    )

    return basarili


def xfce_bildirim_durumunu_al(
) -> Tuple[bool, Optional[bool], str]:
    """
    Xfce Rahatsız Etmeyin durumunu okur.

    true:
        Rahatsız Etmeyin açık

    false:
        Bildirimler normal
    """

    if not komut_var_mi("xfconf-query"):
        return (
            False,
            None,
            "xfconf-query komutu bulunamadı."
        )

    basarili, cikti = komut_calistir(
        [
            "xfconf-query",
            "-c",
            "xfce4-notifyd",
            "-p",
            "/do-not-disturb"
        ]
    )

    if basarili:
        deger = metni_bool_degerine_cevir(cikti)

        if deger is None:
            return (
                False,
                None,
                f"Xfce bildirim değeri anlaşılamadı: {cikti}"
            )

        return (
            True,
            deger,
            "Xfce bildirim durumu okundu."
        )

    hata_metni = cikti.lower()

    ozellik_yok_ifadeleri = [
        "does not exist",
        "property",
        "mevcut değil",
        "bulunamadı",
        "no property"
    ]

    if any(
        ifade in hata_metni
        for ifade in ozellik_yok_ifadeleri
    ):
        return (
            True,
            False,
            (
                "Xfce Rahatsız Etmeyin özelliği henüz "
                "oluşturulmamış; kapalı kabul edildi."
            )
        )

    return (
        False,
        None,
        f"Xfce bildirim durumu okunamadı: {cikti}"
    )


def xfce_bildirim_durumunu_ayarla(
    rahatsiz_etmeyin: bool
) -> Tuple[bool, str]:
    """Xfce Rahatsız Etmeyin özelliğini değiştirir."""

    if not komut_var_mi("xfconf-query"):
        return False, "xfconf-query komutu bulunamadı."

    deger = (
        "true"
        if rahatsiz_etmeyin
        else "false"
    )

    if xfce_bildirim_ozelligi_var_mi():
        komut = [
            "xfconf-query",
            "-c",
            "xfce4-notifyd",
            "-p",
            "/do-not-disturb",
            "-s",
            deger
        ]

    else:
        komut = [
            "xfconf-query",
            "-c",
            "xfce4-notifyd",
            "-p",
            "/do-not-disturb",
            "-n",
            "-t",
            "bool",
            "-s",
            deger
        ]

    basarili, mesaj = komut_calistir(komut)

    if not basarili:
        return (
            False,
            f"Xfce bildirim ayarı değiştirilemedi: {mesaj}"
        )

    if rahatsiz_etmeyin:
        return True, "Masaüstü bildirimleri susturuldu."

    return True, "Masaüstü bildirimleri önceki durumuna getirildi."


# ---------------------------------------------------------
# GNOME BİLDİRİM SİSTEMİ
# ---------------------------------------------------------

def gnome_bildirim_destegi_var_mi() -> bool:
    """GNOME bildirim şemasının bulunup bulunmadığını kontrol eder."""

    if not komut_var_mi("gsettings"):
        return False

    basarili, cikti = komut_calistir(
        ["gsettings", "list-schemas"]
    )

    if not basarili:
        return False

    return (
        "org.gnome.desktop.notifications"
        in cikti.splitlines()
    )


def gnome_bildirim_durumunu_al(
) -> Tuple[bool, Optional[bool], str]:
    """
    GNOME bildirim durumunu okur.

    show-banners false ise Rahatsız Etmeyin açık kabul edilir.
    """

    if not gnome_bildirim_destegi_var_mi():
        return (
            False,
            None,
            "GNOME bildirim sistemi bulunamadı."
        )

    basarili, cikti = komut_calistir(
        [
            "gsettings",
            "get",
            "org.gnome.desktop.notifications",
            "show-banners"
        ]
    )

    if not basarili:
        return (
            False,
            None,
            f"GNOME bildirim durumu okunamadı: {cikti}"
        )

    bildirimler_gosteriliyor = metni_bool_degerine_cevir(
        cikti
    )

    if bildirimler_gosteriliyor is None:
        return (
            False,
            None,
            f"GNOME bildirim değeri anlaşılamadı: {cikti}"
        )

    rahatsiz_etmeyin = not bildirimler_gosteriliyor

    return (
        True,
        rahatsiz_etmeyin,
        "GNOME bildirim durumu okundu."
    )


def gnome_bildirim_durumunu_ayarla(
    rahatsiz_etmeyin: bool
) -> Tuple[bool, str]:
    """GNOME bildirim başlıklarını açar veya kapatır."""

    if not gnome_bildirim_destegi_var_mi():
        return False, "GNOME bildirim sistemi bulunamadı."

    show_banners = (
        "false"
        if rahatsiz_etmeyin
        else "true"
    )

    basarili, mesaj = komut_calistir(
        [
            "gsettings",
            "set",
            "org.gnome.desktop.notifications",
            "show-banners",
            show_banners
        ]
    )

    if not basarili:
        return (
            False,
            f"GNOME bildirim ayarı değiştirilemedi: {mesaj}"
        )

    if rahatsiz_etmeyin:
        return True, "Masaüstü bildirimleri susturuldu."

    return True, "Masaüstü bildirimleri önceki durumuna getirildi."


# ---------------------------------------------------------
# ORTAK BİLDİRİM YÖNETİMİ
# ---------------------------------------------------------

def bildirim_sistemini_belirle() -> Optional[str]:
    """Kullanılabilir bildirim yönetim sistemini belirler."""

    masaustu = masaustu_ortamini_al()

    if masaustu == "xfce" and komut_var_mi("xfconf-query"):
        return "xfce"

    if masaustu == "gnome" and gnome_bildirim_destegi_var_mi():
        return "gnome"

    if komut_var_mi("xfconf-query"):
        basarili, _, _ = xfce_bildirim_durumunu_al()

        if basarili:
            return "xfce"

    if gnome_bildirim_destegi_var_mi():
        return "gnome"

    return None


def bildirim_durumunu_al(
) -> Tuple[bool, Dict[str, Any], str]:
    """
    Mevcut bildirim durumunu geri yüklenebilir biçimde okur.
    """

    bildirim_sistemi = bildirim_sistemini_belirle()

    if bildirim_sistemi == "xfce":
        basarili, rahatsiz_etmeyin, mesaj = (
            xfce_bildirim_durumunu_al()
        )

    elif bildirim_sistemi == "gnome":
        basarili, rahatsiz_etmeyin, mesaj = (
            gnome_bildirim_durumunu_al()
        )

    else:
        return (
            False,
            {},
            (
                "Desteklenen bir masaüstü bildirim sistemi "
                "bulunamadı."
            )
        )

    if not basarili or rahatsiz_etmeyin is None:
        return False, {}, mesaj

    durum = {
        "bildirim_sistemi": bildirim_sistemi,
        "rahatsiz_etmeyin": rahatsiz_etmeyin
    }

    return True, durum, mesaj


def bildirimleri_sustur(
    bildirim_sistemi: Optional[str] = None
) -> Tuple[bool, str]:
    """Masaüstü bildirimlerini geçici olarak susturur."""

    sistem = (
        bildirim_sistemi
        or bildirim_sistemini_belirle()
    )

    if sistem == "xfce":
        return xfce_bildirim_durumunu_ayarla(True)

    if sistem == "gnome":
        return gnome_bildirim_durumunu_ayarla(True)

    return (
        False,
        "Desteklenen bir bildirim sistemi bulunamadı."
    )


def bildirim_ayarlarini_geri_yukle(
    onceki_bildirim_ayarlari: Dict[str, Any]
) -> Tuple[bool, str]:
    """Ders modu öncesindeki bildirim durumunu geri yükler."""

    bildirim_sistemi = onceki_bildirim_ayarlari.get(
        "bildirim_sistemi"
    )

    onceki_rahatsiz_etmeyin = (
        onceki_bildirim_ayarlari.get(
            "rahatsiz_etmeyin"
        )
    )

    if not isinstance(onceki_rahatsiz_etmeyin, bool):
        return False, "Kayıtlı bildirim ayarı geçerli değil."

    if bildirim_sistemi == "xfce":
        return xfce_bildirim_durumunu_ayarla(
            onceki_rahatsiz_etmeyin
        )

    if bildirim_sistemi == "gnome":
        return gnome_bildirim_durumunu_ayarla(
            onceki_rahatsiz_etmeyin
        )

    return (
        False,
        "Kayıtlı bildirim sistemi desteklenmiyor."
    )


# ---------------------------------------------------------
# DERS MODU BAŞLATMA VE BİTİRME
# ---------------------------------------------------------

def ders_modunu_baslat_islemi() -> Tuple[bool, str]:
    """
    Ders modunu başlatır.

    İşlem sırası:
    1. Mevcut ekran ayarlarını oku.
    2. Mevcut bildirim durumunu oku.
    3. Ayarları durum dosyasına kaydet.
    4. Ekran kapanmasını engelle.
    5. Bildirimleri sustur.
    """

    if ders_modu_aktif_mi():
        return False, "Ders modu zaten aktif."

    ekran_basarili, xset_ciktisi = xset_bilgisi_al()

    if not ekran_basarili:
        return (
            False,
            (
                "Mevcut ekran ayarları okunamadı.\n\n"
                f"{xset_ciktisi}"
            )
        )

    onceki_ekran_ayarlari = xset_ayarlarini_ayristir(
        xset_ciktisi
    )

    (
        bildirim_basarili,
        onceki_bildirim_ayarlari,
        bildirim_mesaji
    ) = bildirim_durumunu_al()

    if not bildirim_basarili:
        return (
            False,
            (
                "Masaüstü bildirim durumu okunamadı.\n\n"
                f"{bildirim_mesaji}"
            )
        )

    durum: Dict[str, Any] = {
        "surum": UYGULAMA_SURUMU,
        "ders_modu_aktif": True,
        "baslangic_zamani": datetime.now().isoformat(
            timespec="seconds"
        ),
        "onceki_ekran_ayarlari": onceki_ekran_ayarlari,
        "onceki_bildirim_ayarlari": onceki_bildirim_ayarlari
    }

    durum_basarili, durum_mesaji = durum_dosyasini_yaz(
        durum
    )

    if not durum_basarili:
        return False, durum_mesaji

    ekran_basarili, ekran_mesaji = ekran_uyku_modunu_kapat()

    if not ekran_basarili:
        durum_dosyasini_sil()

        return (
            False,
            (
                "Ekran ayarları değiştirilemedi.\n\n"
                f"{ekran_mesaji}"
            )
        )

    bildirim_sistemi = onceki_bildirim_ayarlari.get(
        "bildirim_sistemi"
    )

    bildirim_basarili, bildirim_mesaji = (
        bildirimleri_sustur(
            bildirim_sistemi
        )
    )

    if not bildirim_basarili:
        geri_yukleme_basarili, geri_yukleme_mesaji = (
            ekran_ayarlarini_geri_yukle(
                onceki_ekran_ayarlari
            )
        )

        durum_dosyasini_sil()

        ek_mesaj = ""

        if not geri_yukleme_basarili:
            ek_mesaj = (
                "\n\nEkran ayarları da geri yüklenemedi:\n"
                f"{geri_yukleme_mesaji}"
            )

        return (
            False,
            (
                "Bildirimler susturulamadı.\n\n"
                f"{bildirim_mesaji}"
                f"{ek_mesaj}"
            )
        )

    return (
        True,
        (
            "Ders modu başarıyla başlatıldı.\n\n"
            "• Ekran ders süresince açık kalacak.\n"
            "• Masaüstü bildirimleri susturuldu.\n"
            "• Önceki ayarlar güvenli biçimde kaydedildi."
        )
    )


def ders_modunu_bitir_islemi() -> Tuple[bool, str]:
    """
    Ders modunu bitirir ve önceki sistem ayarlarını geri yükler.
    """

    durum = durum_dosyasini_oku()

    if not durum:
        return False, "Aktif bir ders modu bulunamadı."

    if durum.get("ders_modu_aktif") is not True:
        return False, "Ders modu zaten kapalı."

    onceki_ekran_ayarlari = durum.get(
        "onceki_ekran_ayarlari"
    )

    onceki_bildirim_ayarlari = durum.get(
        "onceki_bildirim_ayarlari"
    )

    if not isinstance(onceki_ekran_ayarlari, dict):
        return (
            False,
            "Kayıtlı ekran ayarları bulunamadı veya geçersiz."
        )

    if not isinstance(onceki_bildirim_ayarlari, dict):
        return (
            False,
            "Kayıtlı bildirim ayarları bulunamadı veya geçersiz."
        )

    ekran_basarili, ekran_mesaji = (
        ekran_ayarlarini_geri_yukle(
            onceki_ekran_ayarlari
        )
    )

    bildirim_basarili, bildirim_mesaji = (
        bildirim_ayarlarini_geri_yukle(
            onceki_bildirim_ayarlari
        )
    )

    hatalar: List[str] = []

    if not ekran_basarili:
        hatalar.append(
            f"Ekran ayarları:\n{ekran_mesaji}"
        )

    if not bildirim_basarili:
        hatalar.append(
            f"Bildirim ayarları:\n{bildirim_mesaji}"
        )

    if hatalar:
        return (
            False,
            (
                "Bazı sistem ayarları geri yüklenemedi.\n\n"
                + "\n\n".join(hatalar)
                + (
                    "\n\nDurum dosyası güvenlik amacıyla "
                    "silinmedi."
                )
            )
        )

    silme_basarili, silme_mesaji = durum_dosyasini_sil()

    if not silme_basarili:
        return (
            False,
            (
                "Sistem ayarları geri yüklendi ancak "
                f"durum dosyası silinemedi.\n\n{silme_mesaji}"
            )
        )

    return (
        True,
        (
            "Ders modu başarıyla bitirildi.\n\n"
            "• Önceki ekran ayarları geri yüklendi.\n"
            "• Önceki bildirim ayarları geri yüklendi."
        )
    )


def ders_modu_durum_bilgisi() -> Dict[str, Any]:
    """GUI ve terminal için özet ders modu durumu üretir."""

    durum = durum_dosyasini_oku()

    if not durum or durum.get("ders_modu_aktif") is not True:
        return {
            "aktif": False,
            "baslangic_zamani": None,
            "bildirim_sistemi": None
        }

    bildirim_ayarlari = durum.get(
        "onceki_bildirim_ayarlari",
        {}
    )

    if not isinstance(bildirim_ayarlari, dict):
        bildirim_ayarlari = {}

    return {
        "aktif": True,
        "baslangic_zamani": durum.get(
            "baslangic_zamani"
        ),
        "bildirim_sistemi": bildirim_ayarlari.get(
            "bildirim_sistemi"
        )
    }


# ---------------------------------------------------------
# TERMİNAL ARAYÜZÜ
# ---------------------------------------------------------

def terminal_basligini_yaz() -> None:
    """Terminal uygulama başlığını gösterir."""

    print("\n" + "=" * 65)
    print("ÇALIPARDUSLAB2 - ETAP DERS MODU")
    print("=" * 65)
    print(
        "Ekranı açık tutar ve masaüstü bildirimlerini "
        "geçici olarak susturur."
    )
    print(f"Sürüm: {UYGULAMA_SURUMU}")
    print("=" * 65)


def terminal_durumunu_goster() -> None:
    """Ders modunun terminal durum bilgisini gösterir."""

    durum = ders_modu_durum_bilgisi()

    print("\n" + "=" * 60)
    print("DERS MODU DURUMU")
    print("=" * 60)

    if not durum["aktif"]:
        print("\nDers modu: KAPALI")
        print("Ekran ve bildirim ayarları normal durumda.")
        return

    print("\nDers modu: AKTİF")
    print(
        f"Başlangıç zamanı: "
        f"{durum.get('baslangic_zamani', 'Bilinmiyor')}"
    )
    print("Ekran: Sürekli açık")
    print("Masaüstü bildirimleri: Susturuldu")
    print(
        f"Bildirim sistemi: "
        f"{durum.get('bildirim_sistemi', 'Bilinmiyor')}"
    )


def terminal_bekle() -> None:
    """Kullanıcının sonucu okuyabilmesi için bekler."""

    input("\nAna menüye dönmek için Enter tuşuna basın...")


def terminal_ana_program() -> None:
    """Terminal tabanlı ana menüyü çalıştırır."""

    terminal_basligini_yaz()

    while True:
        durum_metni = (
            "AKTİF"
            if ders_modu_aktif_mi()
            else "KAPALI"
        )

        print(f"\nDers modu durumu: {durum_metni}")
        print()
        print("1 - Ders Modunu Başlat")
        print("2 - Ders Modunu Bitir")
        print("3 - Durumu Göster")
        print("4 - Çıkış")
        print()

        try:
            secim = input("Seçiminiz: ").strip()

        except (KeyboardInterrupt, EOFError):
            print("\nETAP Ders Modu kapatıldı.")
            break

        if secim == "1":
            basarili, mesaj = ders_modunu_baslat_islemi()

            print()
            print(
                "BAŞARILI"
                if basarili
                else "HATA"
            )
            print(mesaj)

            terminal_bekle()

        elif secim == "2":
            basarili, mesaj = ders_modunu_bitir_islemi()

            print()
            print(
                "BAŞARILI"
                if basarili
                else "HATA"
            )
            print(mesaj)

            terminal_bekle()

        elif secim == "3":
            terminal_durumunu_goster()
            terminal_bekle()

        elif secim == "4":
            if ders_modu_aktif_mi():
                print(
                    "\nUyarı: Ders modu hâlen aktif."
                )

                onay = input(
                    "Uygulama yine de kapatılsın mı? (e/h): "
                ).strip().lower()

                if onay not in ("e", "evet"):
                    continue

            print("\nETAP Ders Modu kapatıldı.")
            break

        else:
            print(
                "\nGeçersiz seçim. "
                "Lütfen 1 ile 4 arasında seçim yapın."
            )


if __name__ == "__main__":
    terminal_ana_program()
