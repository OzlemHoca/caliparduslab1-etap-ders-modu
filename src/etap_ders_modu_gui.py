#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ÇalıPardusLab2 - ETAP Ders Modu Grafik Arayüzü

Öğretmenlerin terminal kullanmadan ders modunu başlatmasını
ve bitirmesini sağlayan dokunmatik uyumlu Tkinter arayüzüdür.
"""

from __future__ import annotations

import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox
from typing import Callable, Optional, Tuple

from etap_ders_modu import (
    UYGULAMA_SURUMU,
    baslangic_zamanini_al,
    ders_modu_aktif_mi,
    ders_modu_durum_bilgisi,
    ders_modunu_baslat_islemi,
    ders_modunu_bitir_islemi
)


# ---------------------------------------------------------
# ARAYÜZ RENKLERİ
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

BEYAZ = "#ffffff"
KOYU_YAZI = "#1f2937"
ACIK_YAZI = "#64748b"

YAZI_TIPI = "DejaVu Sans"


class EtapDersModuArayuzu:
    """ETAP Ders Modu grafik arayüzünü yönetir."""

    def __init__(self, pencere: tk.Tk) -> None:
        self.pencere = pencere
        self.tam_ekran = False
        self.islem_devam_ediyor = False
        self.kapanis_yapiliyor = False

        self.pencere.title("ETAP Ders Modu")
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
    # ARAYÜZ OLUŞTURMA
    # -----------------------------------------------------

    def arayuzu_olustur(self) -> None:
        self.ust_paneli_olustur()
        self.durum_kartini_olustur()
        self.islem_butonlarini_olustur()
        self.alt_paneli_olustur()

    def ust_paneli_olustur(self) -> None:
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

        tk.Label(
            baslik_alani,
            text="ETAP DERS MODU",
            font=(YAZI_TIPI, 27, "bold"),
            fg=BEYAZ,
            bg=UST_PANEL,
            anchor="w"
        ).pack(anchor="w")

        tk.Label(
            baslik_alani,
            text=(
                "Ekranı açık tutun ve ders sırasında "
                "masaüstü bildirimlerini susturun"
            ),
            font=(YAZI_TIPI, 12),
            fg="#cbd5e1",
            bg=UST_PANEL,
            anchor="w"
        ).pack(
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

        durum_karti.pack(fill="x")

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

        tk.Label(
            sol_alan,
            text="DERS MODU DURUMU",
            font=(YAZI_TIPI, 12, "bold"),
            fg=ACIK_YAZI,
            bg=KART_ARKA_PLAN,
            anchor="w"
        ).pack(anchor="w")

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

        self.bildirim_etiketi = tk.Label(
            sol_alan,
            text="",
            font=(YAZI_TIPI, 11),
            fg=ACIK_YAZI,
            bg=KART_ARKA_PLAN,
            anchor="w"
        )

        self.bildirim_etiketi.pack(
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

        tk.Label(
            sag_alan,
            text="DERS SÜRESİ",
            font=(YAZI_TIPI, 11, "bold"),
            fg=ACIK_YAZI,
            bg=KART_ARKA_PLAN
        ).pack()

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
            ana_panel,
            0,
            0,
            "DERS MODUNU BAŞLAT",
            (
                "Ekranı açık tut ve masaüstü "
                "bildirimlerini geçici olarak sustur"
            ),
            BASLAT_RENGI,
            BASLAT_AKTIF_RENGI,
            self.ders_modunu_baslat
        )

        self.bitir_butonu = self.buyuk_buton_olustur(
            ana_panel,
            0,
            1,
            "DERS MODUNU BİTİR",
            (
                "Ekran ve bildirim ayarlarını ders "
                "öncesindeki hâline geri döndür"
            ),
            BITIR_RENGI,
            BITIR_AKTIF_RENGI,
            self.ders_modunu_bitir
        )

        self.yenile_butonu = self.kucuk_buton_olustur(
            ana_panel,
            1,
            0,
            "DURUMU YENİLE",
            YENILE_RENGI,
            self.durumu_yenile
        )

        self.cikis_butonu = self.kucuk_buton_olustur(
            ana_panel,
            1,
            1,
            "UYGULAMAYI KAPAT",
            CIKIS_RENGI,
            self.uygulamadan_cik
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

        buton = tk.Button(
            ana_panel,
            text=f"{baslik}\n\n{aciklama}",
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

        tk.Label(
            alt_panel,
            text=f"Sürüm {UYGULAMA_SURUMU}  |  F11: Tam ekran",
            font=(YAZI_TIPI, 10),
            fg="#94a3b8",
            bg=ALT_PANEL
        ).pack(
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
        durum = ders_modu_durum_bilgisi()
        aktif = durum.get("aktif") is True

        if aktif:
            self.durum_etiketi.configure(
                text="AKTİF",
                fg=AKTIF_DURUM_RENGI
            )

            self.aciklama_etiketi.configure(
                text=(
                    "Ekran açık tutuluyor ve masaüstü "
                    "bildirimleri susturuluyor."
                )
            )

            bildirim_sistemi = durum.get(
                "bildirim_sistemi"
            )

            self.bildirim_etiketi.configure(
                text=(
                    "Bildirim sistemi: "
                    f"{str(bildirim_sistemi).upper()}"
                )
            )

            self.baslat_butonu.configure(
                state=tk.DISABLED
            )

            self.bitir_butonu.configure(
                state=tk.NORMAL
            )

            self.bilgi_goster(
                "Ders modu aktif. Ekran ders boyunca açık kalacak.",
                "basarili"
            )

        else:
            self.durum_etiketi.configure(
                text="KAPALI",
                fg=KAPALI_DURUM_RENGI
            )

            self.aciklama_etiketi.configure(
                text=(
                    "Sistem normal ekran ve bildirim "
                    "ayarlarını kullanıyor."
                )
            )

            self.bildirim_etiketi.configure(
                text="Bildirimler normal şekilde gösteriliyor."
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

    def sure_sayacini_guncelle(self) -> None:
        if self.kapanis_yapiliyor:
            return

        if ders_modu_aktif_mi():
            baslangic = baslangic_zamanini_al()

            if baslangic:
                fark = datetime.now() - baslangic
                toplam_saniye = max(
                    0,
                    int(fark.total_seconds())
                )

                saat = toplam_saniye // 3600
                dakika = (
                    toplam_saniye % 3600
                ) // 60
                saniye = toplam_saniye % 60

                self.sure_etiketi.configure(
                    text=(
                        f"{saat:02d}:"
                        f"{dakika:02d}:"
                        f"{saniye:02d}"
                    )
                )

        self.pencere.after(
            1000,
            self.sure_sayacini_guncelle
        )

    # -----------------------------------------------------
    # DERS MODU İŞLEMLERİ
    # -----------------------------------------------------

    def ders_modunu_baslat(self) -> None:
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
                "• Ekran ders süresince açık kalacak.\n"
                "• Masaüstü bildirimleri susturulacak.\n\n"
                "Ders bitirildiğinde önceki ayarlar "
                "otomatik olarak geri yüklenecektir."
            ),
            parent=self.pencere
        )

        if not onay:
            return

        self.arka_planda_calistir(
            "Ders modu başlatılıyor",
            ders_modunu_baslat_islemi,
            self.baslatma_sonucunu_goster
        )

    def ders_modunu_bitir(self) -> None:
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
                "Ekran ve bildirim ayarları ders "
                "öncesindeki durumuna getirilecektir."
            ),
            parent=self.pencere
        )

        if not onay:
            return

        self.arka_planda_calistir(
            "Ders modu bitiriliyor",
            ders_modunu_bitir_islemi,
            self.bitirme_sonucunu_goster
        )

    def baslatma_sonucunu_goster(
        self,
        basarili: bool,
        mesaj: str
    ) -> None:

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

    def bitirme_sonucunu_goster(
        self,
        basarili: bool,
        mesaj: str
    ) -> None:

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

        if self.islem_devam_ediyor:
            self.bilgi_goster(
                "Başka bir işlem devam ediyor.",
                "uyari"
            )
            return

        self.islem_devam_ediyor = True
        self.butonlari_gecici_kapat()

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

        try:
            basarili, mesaj = fonksiyon()

        except Exception as hata:
            basarili = False
            mesaj = (
                "Beklenmeyen bir hata oluştu:\n\n"
                f"{hata}"
            )

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

        self.islem_devam_ediyor = False
        tamamlanma_fonksiyonu(
            basarili,
            mesaj
        )

    def butonlari_gecici_kapat(self) -> None:
        for buton in self.islem_butonlari:
            buton.configure(
                state=tk.DISABLED
            )

    # -----------------------------------------------------
    # TAM EKRAN
    # -----------------------------------------------------

    def tam_ekrani_degistir(
        self,
        event=None
    ) -> None:

        self.tam_ekran = not self.tam_ekran

        self.pencere.attributes(
            "-fullscreen",
            self.tam_ekran
        )

        self.tam_ekran_butonu.configure(
            text=(
                "PENCERE MODU"
                if self.tam_ekran
                else "TAM EKRAN"
            )
        )

    def tam_ekrandan_cik(
        self,
        event=None
    ) -> None:

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
        if self.islem_devam_ediyor:
            messagebox.showwarning(
                "İşlem Devam Ediyor",
                (
                    "Bir sistem işlemi devam ediyor.\n"
                    "Lütfen işlem tamamlandıktan sonra tekrar deneyin."
                ),
                parent=self.pencere
            )
            return

        if ders_modu_aktif_mi():
            mesaj = (
                "Ders modu hâlen aktif.\n\n"
                "Uygulamayı kapatsanız bile ekran açık kalacak "
                "ve bildirimler susturulmaya devam edecektir.\n\n"
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


def ana_program() -> None:
    """Tkinter grafik arayüzünü başlatır."""

    pencere = tk.Tk()
    EtapDersModuArayuzu(pencere)
    pencere.mainloop()


if __name__ == "__main__":
    ana_program()
