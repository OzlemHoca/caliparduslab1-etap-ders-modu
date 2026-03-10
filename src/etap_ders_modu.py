#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ETAP Ders Modu - İlk Prototip
ÇalıPardusLab1 / Pardus Hata Yakalama ve Öneri Yarışması 2026

Bu sürüm, ders modu mantığını göstermek için hazırlanmış basit bir prototiptir.
Gerçek sistem ayarlarını değiştirmez; kullanıcıya simülasyon çıktıları verir.
"""

from datetime import datetime


def baslik_yaz() -> None:
    print("=" * 50)
    print("ETAP DERS MODU")
    print("=" * 50)
    print("Akıllı tahta kullanımına yönelik örnek yardımcı araç")
    print()


def durum_goster() -> None:
    print("\n[Durum Bilgisi]")
    print(f"Tarih/Saat: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print("Ders modu durumu: Hazır")
    print("Bildirimler: Normal")
    print("Ekran sadeleştirme: Kapalı")
    print("Hızlı erişim paneli: Pasif")
    print()


def ders_modu_baslat() -> None:
    print("\n[Ders Modu Başlatılıyor]")
    print("- Bildirimler azaltılıyor...")
    print("- Dikkat dağıtıcı öğeler gizleniyor...")
    print("- Ders kullanım profili uygulanıyor...")
    print("- Öğretmen odaklı sade görünüm etkinleştirildi.")
    print("Ders modu başarıyla başlatıldı.\n")


def ders_modu_kapat() -> None:
    print("\n[Ders Modu Kapatılıyor]")
    print("- Normal sistem görünümü geri yükleniyor...")
    print("- Bildirim ayarları eski haline getiriliyor...")
    print("- Hızlı erişim paneli kapatılıyor...")
    print("Ders modu kapatıldı.\n")


def menu_goster() -> None:
    print("Lütfen bir işlem seçin:")
    print("1 - Durum göster")
    print("2 - Ders modunu başlat")
    print("3 - Ders modunu kapat")
    print("4 - Çıkış")
    print()


def ana_program() -> None:
    baslik_yaz()

    while True:
        menu_goster()
        secim = input("Seçiminiz: ").strip()

        if secim == "1":
            durum_goster()
        elif secim == "2":
            ders_modu_baslat()
        elif secim == "3":
            ders_modu_kapat()
        elif secim == "4":
            print("\nProgram sonlandırıldı.")
            break
        else:
            print("\nGeçersiz seçim yaptınız. Lütfen tekrar deneyin.\n")


if __name__ == "__main__":
    ana_program()
