import os
import sys
import subprocess

def resource_path(relative_path):
    """ PyInstaller ile paketlendiğinde dosyaların geçici yolunu, 
    normal çalışırken ise mevcut dizini döndürür. """
    try:
        # PyInstaller geçici klasörü (_MEIPASS)
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Araçların yollarını tanımlıyoruz
FFPROBE_PATH = resource_path("ffprobe.exe")
HANDBRAKE_PATH = resource_path("HandBrakeCLI.exe")

def get_video_files(root_folder):
    video_files = []
    valid_extensions = [".mp4", ".MP4", ".mts", ".MTS"]  
    for folder, _, files in os.walk(root_folder):
        for file in files:
            # "HB " ile başlamayan ve uygun uzantılı dosyaları seç
            if any(file.lower().endswith(ext.lower()) for ext in valid_extensions) and not file.startswith("HB "):
                video_files.append(os.path.join(folder, file))
    return video_files

def move_to_ham_folder(file_path):
    parent_folder = os.path.dirname(file_path)
    ham_folder = os.path.join(parent_folder, "Ham")
    os.makedirs(ham_folder, exist_ok=True)
    new_path = os.path.join(ham_folder, os.path.basename(file_path))
    
    # Eğer hedefte aynı isimde dosya varsa üzerine yazmamak için kontrol edilebilir
    os.rename(file_path, new_path)
    return new_path

def get_fps(input_file):
    # ffprobe.exe yolunu kullanıyoruz
    command = [
        FFPROBE_PATH, "-v", "error", "-select_streams", "v:0", 
        "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", input_file
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        fps_value = result.stdout.strip()
        if "/" in fps_value:
            try:
                num, denom = map(int, fps_value.split("/"))
                return num / denom
            except ValueError:
                print(f"FPS ayrıştırma hatası (kesirli): {fps_value}")
                return None
        else:
            try:
                return float(fps_value)
            except ValueError:
                print(f"FPS ayrıştırma hatası (float): {fps_value}")
                return None
    return None

def get_file_size(file_path):
    # Dosya boyutunu MB cinsinden hesapla
    return os.path.getsize(file_path) / (1024 * 1024)

def compress_video(input_file):
    input_folder = os.path.dirname(input_file)
    output_folder = os.path.dirname(input_folder)  # "Ham" klasörünün bir üst dizini
    output_file = os.path.join(output_folder, "HB " + os.path.basename(input_file))
    
    original_size = get_file_size(input_file)
    fps = get_fps(input_file)
    
    # HandBrakeCLI.exe yolunu kullanıyoruz
    if fps:
        command = [
            HANDBRAKE_PATH, "-i", input_file, "-o", output_file,
            "-e", "x264", "-q", "22", "--cfr", "-r", str(fps)
        ]
    else:
        command = [
            HANDBRAKE_PATH, "-i", input_file, "-o", output_file,
            "-e", "x264", "-q", "22", "--cfr"
        ]
    
    # İşlem sırasında terminali kirletmemek için çıktıları gizliyoruz
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if os.path.exists(output_file):
        compressed_size = get_file_size(output_file)
        savings = ((original_size - compressed_size) / original_size) * 100
        print(f"Sıkıştırma tamamlandı: {os.path.basename(output_file)} (Tasarruf: %{savings:.2f})")
    else:
        print(f"Hata: {output_file} oluşturulamadı!")
    
    return output_file

def main():
    print("--- Video Sıkıştırma Aracı ---")
    root_folder = input("İşlem yapılacak klasör yolunu girin: ").strip('"') # Tırnakları temizler
    
    if not os.path.exists(root_folder):
        print("Geçersiz klasör yolu!")
        return
    
    video_files = get_video_files(root_folder)
    if not video_files:
        print("İşlenecek yeni video dosyası bulunamadı!")
        return
    
    print(f"{len(video_files)} adet video bulundu. İşlem başlıyor...\n")
    
    for file in video_files:
        print(f"İşleniyor: {os.path.basename(file)}")
        # 1. Dosyayı "Ham" klasörüne taşı
        ham_file = move_to_ham_folder(file)
        # 2. "Ham" içindeki dosyayı bir üst klasöre sıkıştırarak çıkar
        compress_video(ham_file)
    
    print("\nBütün işlemler başarıyla tamamlandı!")
    input("Kapatmak için Enter'a basın...")

if __name__ == "__main__":
    main()
