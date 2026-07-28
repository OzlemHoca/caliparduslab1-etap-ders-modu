#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ÇalıPardusLab2 - ETAP Ders Modu Grafik Arayüzü

Pardus ve ETAP sınıflarında öğretmenlerin ders sırasında
gerekli ekran ayarlarını tek dokunuşla yönetmesini sağlar.

Özellikler:
- Ders modunu başlatma
- Ders modunu bitirme
- Ders modu durumunu gösterme
- Ders süresini gösterme
- Tam ekran ve pencere modu
- Büyük, dokunmatik uyumlu düğmeler
- Terminal gerektirmeyen kullanım
"""

import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox
from typing import Any, Callable, Dict, Optional, Tuple

from project import (
    ders_modu_aktif_mi,
    durum_dosyasini_oku,
    durum_dosyasini_sil,
    durum_dosyasini_yaz,
    ekran_ayarlarini_geri_yukle,
    ekran_uyku_modunu_kapat,
    komut_var_mi,
    xset_ayarlarini_ayristir,
    xset_bilgisi_al
)


# ---------------------------------------------------------
# UYGULAMA BİLGİLERİ
# ---------------------------------------------------------

UYGULAMA_ADI = "ETAP Ders Modu"
UYGULAMA_SURUMU = "0.2.0"


# ---------------------------------------------------------
# RENKLER
# ---------------------------------------------------------

ARKA_PLAN = "#eef3f7"
UST_PANEL = "#1f2937"
ALT_PANEL = "#111827"

KART_ARKA_PLAN = "#ffffff"
KART_KENAR = "#d5dde5"

BASLAT_RENGI = "#15803d"
BASLAT_AKTIF_RENGI = "#166534"

BITIR_RENGI = "#c62828"
BITIR_AKTIF_RENGI = "#991b1b"

YENILE_RENGI = "#0369a1"
TAM_EKRAN_RENGI = "#475569"
CIKIS_RENGI = "#374151"

AKTIF_DURUM_RENGI = "#15803d"
KAPALI_DURUM_RENGI = "#64748b"
HATA_RENGI = "#b91c1c"
UYARI_RENGI = "#b45309"

BEYAZ = "#ffffff"
KOYU_YAZI = "#1f2937"
ACIK_YAZI = "#64748b"

YAZI_TIPI = "DejaVu Sans"


# ---------------------------------------------------------
# ANA UYGULAMA SINIFI
# ---------------------------------------------------------

class EtapDersModuArayuzu:
    """
    ETAP Ders Modu dokunmatik grafik arayüzünü yönetir.
    """

    def __init__(self, pencere: tk.Tk) -> None:
        self.pencere = pencere
        self.tam_ekran = False
        self.islem_devam_ediyor = False
        self.kapanis_yapiliyor = False

        self.pencere.title(UYGULAMA_ADI)
        self.pencere.geometry("1100x700")
        self.pencere.minsize(850, 580)
        self.pencere.configure(bg=ARKA_PLAN)

        self.pencere.protocol(
            "WM_DELETE_WINDOW",
            self.uygulamadan_cik
        )

        self.pencere.bind(
            "<F11>",
            self.tam_ekrani_degistir
        )

        self.pencere.bind(
            "<Escape>",
            self.tam_ekrandan_cik
        )

        self.arayuzu_olustur()
        self.durumu_yenile()

        self.pencere.after(
            1000,
            self.sure_sayacini_guncelle
        )

    # -----------------------------------------------------
    # ARAYÜZ
    # -----------------------------------------------------

    def arayuzu_olustur(self) -> None:
        """
        Ana pencerenin bütün arayüz bileşenlerini oluşturur.
        """

        self.ust_paneli_olustur()
        self.durum_kartini_olustur()
        self.islem_butonlarini_olustur()
        self.alt_paneli_olustur()

    def ust_paneli_olustur(self) -> None:
        """
        Uygulama başlığı ve tam ekran düğmesini oluşturur.
        """

        ust_panel = tk.Frame(
            self.pencere,
            bg=UST_PANEL,
            height=115
        )

        ust_panel.pack(
            side="top",
            fill="x"
        )

        ust_panel.pack_propagate(False)

        baslik_alani = tk.Frame(
            ust_panel,
            bg=UST_PANEL
        )

        baslik_alani.pack(
            side="left",
            fill="both",
            expand=True,
            padx=30,
            pady=18
        )

        baslik = tk.Label(
            baslik_alani,
            text="ETAP DERS MODU",
            font=(YAZI_TIPI, 27, "bold"),
            fg=BEYAZ,
            bg=UST_PANEL,
            anchor="w"
        )

        baslik.pack(anchor="w")

        alt_baslik = tk.Label(
            baslik_alani,
            text=(
                "Ders sırasında ekranın kapanmasını "
                "tek dokunuşla engelleyin"
            ),
            font=(YAZI_TIPI, 12),
            fg="#cbd5e1",
            bg=UST_PANEL,
            anchor="w"
        )

        alt_baslik.pack(
            anchor="w",
            pady=(5, 0)
        )

        self.tam_ekran_butonu = tk.Button(
            ust_panel,
            text="TAM EKRAN",
            command=self.tam_ekrani_degistir,
            font=(YAZI_TIPI, 12, "bold"),
            bg=TAM_EKRAN_RENGI,
            fg=BEYAZ,
            activebackground="#64748b",
            activeforeground=BEYAZ,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=22,
            pady=14
        )

        self.tam_ekran_butonu.pack(
            side="right",
            padx=25,
            pady=25
        )

    def durum_kartini_olustur(self) -> None:
        """
        Ders modunun mevcut durumunu gösteren kartı oluşturur.
        """

        dis_cerceve = tk.Frame(
            self.pencere,
            bg=ARKA_PLAN
        )

        dis_cerceve.pack(
            fill="x",
            padx=30,
            pady=(25, 10)
        )

        durum_karti = tk.Frame(
            dis_cerceve,
            bg=KART_ARKA_PLAN,
            highlightbackground=KART_KENAR,
            highlightthickness=1
        )

        durum_karti.pack(
            fill="x"
        )

        sol_alan = tk.Frame(
            durum_karti,
            bg=KART_ARKA_PLAN
        )

        sol_alan.pack(
            side="left",
            fill="both",
            expand=True,
            padx=25,
            pady=20
        )

        durum_basligi = tk.Label(
            sol_alan,
            text="DERS MODU DURUMU",
            font=(YAZI_TIPI, 12, "bold"),
            fg=ACIK_YAZI,
            bg=KART_ARKA_PLAN,
            anchor="w"
        )

        durum_basligi.pack(anchor="w")

        self.durum_etiketi = tk.Label(
            sol_alan,
            text="Kontrol ediliyor...",
            font=(YAZI_TIPI, 28, "bold"),
            fg=KAPALI_DURUM_RENGI,
            bg=KART_ARKA_PLAN,
            anchor="w"
        )

        self.durum_etiketi.pack(
            anchor="w",
            pady=(5, 0)
        )

        self.aciklama_etiketi = tk.Label(
            sol_alan,
            text="",
            font=(YAZI_TIPI, 12),
            fg=ACIK_YAZI,
            bg=KART_ARKA_PLAN,
            anchor="w"
        )

        self.aciklama_etiketi.pack(
            anchor="w",
            pady=(5, 0)
        )

        sag_alan = tk.Frame(
            durum_karti,
            bg=KART_ARKA_PLAN
        )

        sag_alan.pack(
            side="right",
            padx=30,
            pady=20
        )

        sure_basligi = tk.Label(
            sag_alan,
            text="DERS SÜRESİ",
            font=(YAZI_TIPI, 11, "bold"),
            fg=ACIK_YAZI,
            bg=KART_ARKA_PLAN
        )

        sure_basligi.pack()

        self.sure_etiketi = tk.Label(
            sag_alan,
            text="00:00:00",
            font=(YAZI_TIPI, 24, "bold"),
            fg=KOYU_YAZI,
            bg=KART_ARKA_PLAN
        )

        self.sure_etiketi.pack(
            pady=(7, 0)
        )

    def islem_butonlarini_olustur(self) -> None:
        """
        Dokunmatik kullanıma uygun büyük işlem düğmelerini oluşturur.
        """

        ana_panel = tk.Frame(
            self.pencere,
            bg=ARKA_PLAN
        )

        ana_panel.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=10
        )

        ana_panel.grid_columnconfigure(0, weight=1)
        ana_panel.grid_columnconfigure(1, weight=1)
        ana_panel.grid_rowconfigure(0, weight=3)
        ana_panel.grid_rowconfigure(1, weight=1)

        self.baslat_butonu = self.buyuk_buton_olustur(
            ana_panel=ana_panel,
            satir=0,
            sutun=0,
            baslik="DERS MODUNU BAŞLAT",
            aciklama=(
                "Ekran koruyucuyu ve ekran güç "
                "yönetimini geçici olarak kapat"
            ),
            renk=BASLAT_RENGI,
            aktif_renk=BASLAT_AKTIF_RENGI,
            komut=self.ders_modunu_baslat
        )

        self.bitir_butonu = self.buyuk_buton_olustur(
            ana_panel=ana_panel,
            satir=0,
            sutun=1,
            baslik="DERS MODUNU BİTİR",
            aciklama=(
                "Ders öncesindeki ekran ayarlarını "
                "güvenli biçimde geri yükle"
            ),
            renk=BITIR_RENGI,
            aktif_renk=BITIR_AKTIF_RENGI,
            komut=self.ders_modunu_bitir
        )

        self.yenile_butonu = self.kucuk_buton_olustur(
            ana_panel=ana_panel,
            satir=1,
            sutun=0,
            metin="DURUMU YENİLE",
            renk=YENILE_RENGI,
            komut=self.durumu_yenile
        )

        self.cikis_butonu = self.kucuk_buton_olustur(
            ana_panel=ana_panel,
            satir=1,
            sutun=1,
            metin="UYGULAMAYI KAPAT",
            renk=CIKIS_RENGI,
            komut=self.uygulamadan_cik
        )

        self.islem_butonlari = [
            self.baslat_butonu,
            self.bitir_butonu,
            self.yenile_butonu
        ]

    def buyuk_buton_olustur(
        self,
        ana_panel: tk.Frame,
        satir: int,
        sutun: int,
        baslik: str,
        aciklama: str,
        renk: str,
        aktif_renk: str,
        komut: Callable[[], None]
    ) -> tk.Button:
        """
        Başlık ve açıklama içeren büyük düğme oluşturur.
        """

        metin = f"{baslik}\n\n{aciklama}"

        buton = tk.Button(
            ana_panel,
            text=metin,
            command=komut,
            font=(YAZI_TIPI, 19, "bold"),
            bg=renk,
            fg=BEYAZ,
            activebackground=aktif_renk,
            activeforeground=BEYAZ,
            disabledforeground="#d1d5db",
            relief="flat",
            bd=0,
            cursor="hand2",
            justify="center",
            wraplength=420,
            padx=30,
            pady=30
        )

        buton.grid(
            row=satir,
            column=sutun,
            sticky="nsew",
            padx=10,
            pady=10
        )

        return buton

    def kucuk_buton_olustur(
        self,
        ana_panel: tk.Frame,
        satir: int,
        sutun: int,
        metin: str,
        renk: str,
        komut: Callable[[], None]
    ) -> tk.Button:
        """
        Alt işlem alanı için yardımcı düğme oluşturur.
        """

        buton = tk.Button(
            ana_panel,
            text=metin,
            command=komut,
            font=(YAZI_TIPI, 14, "bold"),
            bg=renk,
            fg=BEYAZ,
            activebackground=renk,
            activeforeground=BEYAZ,
            disabledforeground="#d1d5db",
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=16
        )

        buton.grid(
            row=satir,
            column=sutun,
            sticky="nsew",
            padx=10,
            pady=10
        )

        return buton

    def alt_paneli_olustur(self) -> None:
        """
        İşlem ve klavye bilgilerini gösteren alt paneli oluşturur.
        """

        alt_panel = tk.Frame(
            self.pencere,
            bg=ALT_PANEL,
            height=65
        )

        alt_panel.pack(
            side="bottom",
            fill="x"
        )

        alt_panel.pack_propagate(False)

        self.bilgi_etiketi = tk.Label(
            alt_panel,
            text="Uygulama başlatılıyor...",
            font=(YAZI_TIPI, 11, "bold"),
            fg=BEYAZ,
            bg=ALT_PANEL,
            anchor="w"
        )

        self.bilgi_etiketi.pack(
            side="left",
            fill="both",
            expand=True,
            padx=25
        )

        surum_etiketi = tk.Label(
            alt_panel,
            text=f"Sürüm {UYGULAMA_SURUMU}  |  F11: Tam ekran",
            font=(YAZI_TIPI, 10),
            fg="#94a3b8",
            bg=ALT_PANEL
        )

        surum_etiketi.pack(
            side="right",
            padx=25
        )

    # -----------------------------------------------------
    # DURUM YÖNETİMİ
    # -----------------------------------------------------

    def bilgi_goster(
        self,
        mesaj: str,
        tur: str = "normal"
    ) -> None:
        """
        Alt bilgi alanındaki metni ve rengini günceller.
        """

        renkler = {
            "normal": BEYAZ,
            "basarili": "#86efac",
            "uyari": "#fde68a",
            "hata": "#fca5a5"
        }

        self.bilgi_etiketi.configure(
            text=mesaj,
            fg=renkler.get(tur, BEYAZ)
        )

    def durumu_yenile(self) -> None:
        """
        Durum dosyasına göre arayüzü günceller.
        """

        aktif = ders_modu_aktif_mi()
        durum = durum_dosyasini_oku()

        if aktif:
            self.durum_etiketi.configure(
                text="AKTİF",
                fg=AKTIF_DURUM_RENGI
            )

            self.aciklama_etiketi.configure(
                text=(
                    "Ekran koruyucu ve ekran güç "
                    "yönetimi geçici olarak kapalı."
                )
            )

            self.baslat_butonu.configure(
                state=tk.DISABLED
            )

            self.bitir_butonu.configure(
                state=tk.NORMAL
            )

            baslangic = self.baslangic_zamanini_al(durum)

            if baslangic:
                self.bilgi_goster(
                    "Ders modu aktif. Ekran ders boyunca açık kalacak.",
                    "basarili"
                )
            else:
                self.bilgi_goster(
                    "Ders modu aktif ancak başlangıç zamanı okunamadı.",
                    "uyari"
                )

        else:
            self.durum_etiketi.configure(
                text="KAPALI",
                fg=KAPALI_DURUM_RENGI
            )

            self.aciklama_etiketi.configure(
                text=(
                    "Sistem normal ekran ve güç "
                    "ayarlarını kullanıyor."
                )
            )

            self.baslat_butonu.configure(
                state=tk.NORMAL
            )

            self.bitir_butonu.configure(
                state=tk.DISABLED
            )

            self.sure_etiketi.configure(
                text="00:00:00"
            )

            self.bilgi_goster(
                "Ders modu başlatılmaya hazır.",
                "normal"
            )

    def baslangic_zamanini_al(
        self,
        durum: Optional[Dict[str, Any]]
    ) -> Optional[datetime]:
        """
        Durum dosyasındaki başlangıç zamanını datetime nesnesine çevirir.
        """

        if not durum:
            return None

        baslangic_metni = durum.get("baslangic_zamani")

        if not isinstance(baslangic_metni, str):
            return None

        try:
            return datetime.fromisoformat(baslangic_metni)

        except ValueError:
            return None

    def sure_sayacini_guncelle(self) -> None:
        """
        Ders modu aktifken geçen süreyi her saniye günceller.
        """

        if self.kapanis_yapiliyor:
            return

        if ders_modu_aktif_mi():
            durum = durum_dosyasini_oku()
            baslangic = self.baslangic_zamanini_al(durum)

            if baslangic:
                fark = datetime.now() - baslangic
                toplam_saniye = max(0, int(fark.total_seconds()))

                saat = toplam_saniye // 3600
                dakika = (toplam_saniye % 3600) // 60
                saniye = toplam_saniye % 60

                self.sure_etiketi.configure(
                    text=f"{saat:02d}:{dakika:02d}:{saniye:02d}"
                )

        self.pencere.after(
            1000,
            self.sure_sayacini_guncelle
        )

    # -----------------------------------------------------
    # DERS MODUNU BAŞLATMA
    # -----------------------------------------------------

    def ders_modunu_baslat(self) -> None:
        """
        Kullanıcı onayından sonra ders modunu başlatır.
        """

        if ders_modu_aktif_mi():
            messagebox.showinfo(
                "Ders Modu",
                "Ders modu zaten aktif.",
                parent=self.pencere
            )

            self.durumu_yenile()
            return

        onay = messagebox.askyesno(
            "Ders Modunu Başlat",
            (
                "Ders modu başlatılsın mı?\n\n"
                "Ekran koruyucu ve ekran güç yönetimi "
                "ders süresince kapatılacaktır."
            ),
            parent=self.pencere
        )

        if not onay:
            return

        self.arka_planda_calistir(
            islem_adi="Ders modu başlatılıyor",
            fonksiyon=self.ders_modunu_baslat_islemi,
            tamamlanma_fonksiyonu=self.baslatma_sonucunu_goster
        )

    def ders_modunu_baslat_islemi(
        self
    ) -> Tuple[bool, str]:
        """
        Ders modu başlangıç işlemlerini gerçekleştirir.
        """

        if not komut_var_mi("xset"):
            return (
                False,
                (
                    "xset komutu bulunamadı.\n\n"
                    "Kurulum için:\n"
                    "sudo apt install x11-xserver-utils"
                )
            )

        basarili, xset_ciktisi = xset_bilgisi_al()

        if not basarili:
            return (
                False,
                (
                    "Mevcut ekran ayarları okunamadı.\n\n"
                    f"{xset_ciktisi}"
                )
            )

        onceki_ayarlar = xset_ayarlarini_ayristir(
            xset_ciktisi
        )

        durum = {
            "ders_modu_aktif": True,
            "baslangic_zamani": datetime.now().isoformat(
                timespec="seconds"
            ),
            "onceki_ekran_ayarlari": onceki_ayarlar
        }

        if not durum_dosyasini_yaz(durum):
            return (
                False,
                "Ders modu durum dosyası kaydedilemedi."
            )

        basarili, mesaj = ekran_uyku_modunu_kapat()

        if not basarili:
            durum_dosyasini_sil()

            return (
                False,
                (
                    "Ekran ayarları değiştirilemedi.\n\n"
                    f"{mesaj}"
                )
            )

        return (
            True,
            (
                "Ders modu başarıyla başlatıldı.\n\n"
                "Ekran ders süresince açık kalacak."
            )
        )

    def baslatma_sonucunu_goster(
        self,
        basarili: bool,
        mesaj: str
    ) -> None:
        """
        Ders modu başlatma sonucunu kullanıcıya gösterir.
        """

        self.durumu_yenile()

        if basarili:
            self.bilgi_goster(
                "Ders modu başarıyla başlatıldı.",
                "basarili"
            )

            messagebox.showinfo(
                "Ders Modu Başlatıldı",
                mesaj,
                parent=self.pencere
            )

        else:
            self.bilgi_goster(
                "Ders modu başlatılamadı.",
                "hata"
            )

            messagebox.showerror(
                "Ders Modu Başlatılamadı",
                mesaj,
                parent=self.pencere
            )

    # -----------------------------------------------------
    # DERS MODUNU BİTİRME
    # -----------------------------------------------------

    def ders_modunu_bitir(self) -> None:
        """
        Kullanıcı onayından sonra ders modunu bitirir.
        """

        if not ders_modu_aktif_mi():
            messagebox.showinfo(
                "Ders Modu",
                "Aktif bir ders modu bulunamadı.",
                parent=self.pencere
            )

            self.durumu_yenile()
            return

        onay = messagebox.askyesno(
            "Ders Modunu Bitir",
            (
                "Ders modu bitirilsin mi?\n\n"
                "Ders öncesindeki ekran ayarları "
                "geri yüklenecektir."
            ),
            parent=self.pencere
        )

        if not onay:
            return

        self.arka_planda_calistir(
            islem_adi="Ders modu bitiriliyor",
            fonksiyon=self.ders_modunu_bitir_islemi,
            tamamlanma_fonksiyonu=self.bitirme_sonucunu_goster
        )

    def ders_modunu_bitir_islemi(
        self
    ) -> Tuple[bool, str]:
        """
        Önceki ekran ayarlarını geri yükler.
        """

        durum = durum_dosyasini_oku()

        if not durum:
            return (
                False,
                "Ders modu durum dosyası bulunamadı."
            )

        onceki_ayarlar = durum.get(
            "onceki_ekran_ayarlari"
        )

        if not isinstance(onceki_ayarlar, dict):
            return (
                False,
                "Önceki ekran ayarları bulunamadı."
            )

        basarili, mesaj = ekran_ayarlarini_geri_yukle(
            onceki_ayarlar
        )

        if not basarili:
            return (
                False,
                (
                    "Önceki ekran ayarları geri yüklenemedi.\n\n"
                    f"{mesaj}"
                )
            )

        if not durum_dosyasini_sil():
            return (
                False,
                (
                    "Ekran ayarları geri yüklendi ancak "
                    "durum dosyası silinemedi."
                )
            )

        return (
            True,
            (
                "Ders modu başarıyla bitirildi.\n\n"
                "Ders öncesindeki ekran ayarları geri yüklendi."
            )
        )

    def bitirme_sonucunu_goster(
        self,
        basarili: bool,
        mesaj: str
    ) -> None:
        """
        Ders modu bitirme sonucunu kullanıcıya gösterir.
        """

        self.durumu_yenile()

        if basarili:
            self.bilgi_goster(
                "Ders modu bitirildi ve önceki ayarlar geri yüklendi.",
                "basarili"
            )

            messagebox.showinfo(
                "Ders Modu Bitirildi",
                mesaj,
                parent=self.pencere
            )

        else:
            self.bilgi_goster(
                "Ders modu güvenli biçimde bitirilemedi.",
                "hata"
            )

            messagebox.showerror(
                "Ders Modu Bitirilemedi",
                mesaj,
                parent=self.pencere
            )

    # -----------------------------------------------------
    # ARKA PLAN İŞLEMLERİ
    # -----------------------------------------------------

    def arka_planda_calistir(
        self,
        islem_adi: str,
        fonksiyon: Callable[[], Tuple[bool, str]],
        tamamlanma_fonksiyonu: Callable[[bool, str], None]
    ) -> None:
        """
        Sistem işlemlerini arayüzü dondurmadan çalıştırır.
        """

        if self.islem_devam_ediyor:
            self.bilgi_goster(
                "Başka bir işlem devam ediyor.",
                "uyari"
            )
            return

        self.islem_devam_ediyor = True
        self.butonlari_etkinlestir(False)

        self.bilgi_goster(
            f"{islem_adi}...",
            "normal"
        )

        is_parcacigi = threading.Thread(
            target=self.arka_plan_islemi,
            args=(
                fonksiyon,
                tamamlanma_fonksiyonu
            ),
            daemon=True
        )

        is_parcacigi.start()

    def arka_plan_islemi(
        self,
        fonksiyon: Callable[[], Tuple[bool, str]],
        tamamlanma_fonksiyonu: Callable[[bool, str], None]
    ) -> None:
        """
        Arka plan işlemini çalıştırır ve sonucu ana pencereye iletir.
        """

        try:
            basarili, mesaj = fonksiyon()

        except Exception as hata:
            basarili = False
            mesaj = f"Beklenmeyen bir hata oluştu:\n{hata}"

        self.pencere.after(
            0,
            lambda: self.arka_plan_islemini_tamamla(
                basarili,
                mesaj,
                tamamlanma_fonksiyonu
            )
        )

    def arka_plan_islemini_tamamla(
        self,
        basarili: bool,
        mesaj: str,
        tamamlanma_fonksiyonu: Callable[[bool, str], None]
    ) -> None:
        """
        İşlem tamamlandığında düğmeleri yeniden etkinleştirir.
        """

        self.islem_devam_ediyor = False
        self.butonlari_etkinlestir(True)
        tamamlanma_fonksiyonu(basarili, mesaj)

    def butonlari_etkinlestir(
        self,
        etkin: bool
    ) -> None:
        """
        İşlem sırasında tekrarlı dokunmaları engeller.
        """

        durum = tk.NORMAL if etkin else tk.DISABLED

        for buton in self.islem_butonlari:
            buton.configure(state=durum)

        if etkin:
            self.durumu_yenile()

    # -----------------------------------------------------
    # TAM EKRAN
    # -----------------------------------------------------

    def tam_ekrani_degistir(
        self,
        event=None
    ) -> None:
        """
        Tam ekran ve pencere modu arasında geçiş yapar.
        """

        self.tam_ekran = not self.tam_ekran

        self.pencere.attributes(
            "-fullscreen",
            self.tam_ekran
        )

        if self.tam_ekran:
            self.tam_ekran_butonu.configure(
                text="PENCERE MODU"
            )
        else:
            self.tam_ekran_butonu.configure(
                text="TAM EKRAN"
            )

    def tam_ekrandan_cik(
        self,
        event=None
    ) -> None:
        """
        Escape tuşuyla tam ekrandan çıkar.
        """

        if not self.tam_ekran:
            return

        self.tam_ekran = False

        self.pencere.attributes(
            "-fullscreen",
            False
        )

        self.tam_ekran_butonu.configure(
            text="TAM EKRAN"
        )

    # -----------------------------------------------------
    # ÇIKIŞ
    # -----------------------------------------------------

    def uygulamadan_cik(self) -> None:
        """
        Aktif ders modunu kontrol ederek uygulamayı kapatır.
        """

        if self.islem_devam_ediyor:
            messagebox.showwarning(
                "İşlem Devam Ediyor",
                (
                    "Sistem işlemi devam ediyor.\n"
                    "Lütfen işlem tamamlandıktan sonra tekrar deneyin."
                ),
                parent=self.pencere
            )
            return

        if ders_modu_aktif_mi():
            mesaj = (
                "Ders modu hâlen aktif.\n\n"
                "Uygulamayı kapatsanız bile ekran ayarları "
                "ders modunda kalacaktır.\n\n"
                "Uygulama yine de kapatılsın mı?"
            )
        else:
            mesaj = "ETAP Ders Modu kapatılsın mı?"

        onay = messagebox.askyesno(
            "Uygulamayı Kapat",
            mesaj,
            parent=self.pencere
        )

        if onay:
            self.kapanis_yapiliyor = True
            self.pencere.destroy()


# ---------------------------------------------------------
# PROGRAM BAŞLANGICI
# ---------------------------------------------------------

def ana_program() -> None:
    """
    Tkinter grafik arayüzünü başlatır.
    """

    pencere = tk.Tk()
    EtapDersModuArayuzu(pencere)
    pencere.mainloop()


if __name__ == "__main__":
    ana_program()
