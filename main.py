import os
import subprocess

def get_video_files(root_folder):
    video_files = []
    valid_extensions = [".mp4", ".MP4", ".mts", ".MTS"]  
    for folder, _, files in os.walk(root_folder):
        for file in files:
            if any(file.lower().endswith(ext.lower()) for ext in valid_extensions) and not file.startswith("HB "):
                video_files.append(os.path.join(folder, file))
    return video_files

def move_to_ham_folder(file_path):
    parent_folder = os.path.dirname(file_path)
    ham_folder = os.path.join(parent_folder, "Ham")
    os.makedirs(ham_folder, exist_ok=True)
    new_path = os.path.join(ham_folder, os.path.basename(file_path))
    os.rename(file_path, new_path)
    return new_path

def get_fps(input_file):
    command = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", input_file]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        fps_value = result.stdout.strip()
        if "/" in fps_value:
            try:
                num, denom = map(int, fps_value.split("/"))
                return num / denom
            except ValueError:
                print(f"FPS ayrıştırma hatası: {fps_value}")
                return None
        else:
            try:
                return float(fps_value)
            except ValueError:
                print(f"FPS ayrıştırma hatası: {fps_value}")
                return None
    return None

def get_file_size(file_path):
    return os.path.getsize(file_path) / (1024 * 1024)  # MB cinsinden döndür

def compress_video(input_file):
    input_folder = os.path.dirname(input_file)
    output_folder = os.path.dirname(input_folder)  # "Ham" klasörünün bir üstü
    file_extension = os.path.splitext(input_file)[-1]  # Orijinal uzantıyı al
    output_file = os.path.join(output_folder, "HB " + os.path.basename(input_file))
    
    original_size = get_file_size(input_file)
    
    fps = get_fps(input_file)
    if fps:
        command = [
            "HandBrakeCLI", "-i", input_file, "-o", output_file,
            "-e", "x264", "-q", "22", "--cfr", "-r", str(fps)
        ]
    else:
        command = [
            "HandBrakeCLI", "-i", input_file, "-o", output_file,
            "-e", "x264", "-q", "22", "--cfr"
        ]
    
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    compressed_size = get_file_size(output_file)
    compression_ratio = ((original_size - compressed_size) / original_size) * 100
    print(f"Sıkıştırma tamamlandı: {input_file} -> {output_file} (Tasarruf: {compression_ratio:.2f}%)")
    
    return output_file

def main():
    root_folder = input("Klasör yolunu girin: ")
    if not os.path.exists(root_folder):
        print("Geçersiz klasör yolu!")
        return
    
    video_files = get_video_files(root_folder)
    if not video_files:
        print("Video dosyası bulunamadı!")
        return
    
    for file in video_files:
        ham_file = move_to_ham_folder(file)
        print(f"Taşındı: {ham_file}")
        
        output_file = compress_video(ham_file)
    
    print("İşlem tamamlandı!")

if __name__ == "__main__":
    main()
