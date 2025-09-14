import subprocess
import os

def insert_text_into_video(input_video, text, output_folder="output",
                           font_file=r"C:\Windows\Fonts\arial.ttf",
                           x=100, y=100, fontsize=40, fontcolor="white"):
    """
    Chèn text vào video và xuất ra output_folder
    """
    # Tạo folder output nếu chưa có
    os.makedirs(output_folder, exist_ok=True)

    # Tên file gốc + hậu tố _out.mp4
    base_name = os.path.splitext(os.path.basename(input_video))[0]
    output_video = os.path.join(output_folder, f"{base_name}_out.mp4")

    # Lưu text ra file tạm (fix Unicode)
    temp_caption = "caption_temp.txt"
    with open(temp_caption, "w", encoding="utf-8") as f:
        f.write(text)

    drawtext = (
        f"drawtext=textfile='{temp_caption}':"
        f"fontfile='{font_file}':"
        f"x={x}:y={y}:fontsize={fontsize}:fontcolor={fontcolor}:"
        f"box=1:boxcolor=black@0.5:boxborderw=5"
    )

    cmd = [
        "ffmpeg", "-y", "-i", input_video,
        "-vf", drawtext,
        "-codec:a", "copy", output_video
    ]

    print(" ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"✅ Đã chèn text vào {output_video}")

    # Xóa file tạm
    if os.path.exists(temp_caption):
        os.remove(temp_caption)

if __name__ == "__main__":
    insert_text_into_video(
        input_video=r"E:\kid\AFF.mp4",
        text="Xin chào đây là caption test",
        output_folder=r"E:\output",
        font_file=r"C:\Windows\Fonts\arial.ttf",   # ✅ font .ttf chuẩn
        x=200, y=150
    )
