import subprocess,base64
import os
import cv2
import numpy as np
import time
import dotenv
from tinydb import TinyDB, Query

X_ratio=0.8
Y_ratio=0.8
X_ratio_pickup=0.1
Y_ratio_pickup=0.25
ICON_DIR = "image/"  # thư mục chứa icon mẫu
ID_DIR = "img_id/"  # thư mục chứa id  mẫu
ACC_DIR = "img_acc/"  # thư mục chứa acc  mẫu

db= TinyDB('accounts.json')
rows = db.all()

def get_connected_devices():
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    lines = result.stdout.strip().splitlines()
    devices = []
    for line in lines[1:]:  # bỏ dòng đầu "List of devices attached"
        if line.strip() and "device" in line:
            device_id = line.split()[0]
            devices.append(device_id)
    return devices

def adb_screencap(filename="screen.jpg"):
    """Chụp màn hình từ điện thoại qua ADB và lưu file hợp lệ"""
    result = subprocess.run(
        ["adb", "exec-out", "screencap", "-p"],
        stdout=subprocess.PIPE
    )
    # Chuyển \r\n thành \n để ảnh hợp lệ
    fixed_data = result.stdout.replace(b"\r\n", b"\n")

    with open(filename, "wb") as f:
        f.write(fixed_data)

    return filename

def find_template_in_screenshot(template_path, screenshot="screen.jpg", threshold=0.8):
    """Tìm icon trong ảnh bằng template matching"""
    img_rgb = cv2.imread(screenshot)
    template = cv2.imread(template_path)

    if img_rgb is None or template is None:
        print(f"❌ Không load được ảnh: {template_path}")
        return None

    h, w = template.shape[:2]
    result = cv2.matchTemplate(img_rgb, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(result >= threshold)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    if len(loc[0]) > 0:
        pt = (loc[1][0] + w // 2, loc[0][0] + h // 2)
        print(f"👉 Found {os.path.basename(template_path)} at {pt} with accuracy {max_val:.2f}")

        # Vẽ ô highlight để debug
        cv2.rectangle(img_rgb, (pt[0]-w//2, pt[1]-h//2), (pt[0]+w//2, pt[1]+h//2), (0,0,255), 3)
        cv2.imwrite("debug_match.png", img_rgb)

        return True
    else:
        print(f"❌ Không tìm thấy {template_path}")
        return False

def find_and_tap(template_path, screenshot="screen.jpg", threshold=0.6, long_press=False):
    """Tìm icon trong màn hình bằng template matching và tap"""
    img_rgb = cv2.imread(screenshot)
    template = cv2.imread(template_path)

    if img_rgb is None or template is None:
        print(f"❌ Không load được ảnh: {template_path}")
        return False

    h, w = template.shape[:2]
    result = cv2.matchTemplate(img_rgb, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(result >= threshold)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    if len(loc[0]) > 0:
        pt = (loc[1][0] + w // 2, loc[0][0] + h // 2)
        print(f"👉 Found {os.path.basename(template_path)} at {pt} with accuracy {max_val:.2f}")

        # Vẽ ô highlight để debug
        cv2.rectangle(img_rgb, (pt[0]-w//2, pt[1]-h//2), (pt[0]+w//2, pt[1]+h//2), (0,0,255), 3)
        cv2.imwrite("debug_match.png", img_rgb)

        # Thực hiện thao tác
        if long_press:
            subprocess.run([
                "adb", "shell",
                f"input swipe {pt[0]} {pt[1]} {pt[0]} {pt[1]} 1000"
            ])
        else:
            subprocess.run([
                "adb", "shell",
                f"input tap {pt[0]} {pt[1]}"
            ])
            time.sleep(5)  # chờ thêm 2 giây sau long press
        return True
    else:
        print(f"❌ Không tìm thấy {template_path}")
        return False     
def open_and_download_video(devices_id, url):
    """Mở URL trên thiết bị Android qua adb shell"""
    # Lấy tên file từ URL
    filename = os.path.basename(url.split("?")[0])
    try:
        result = subprocess.run(
            ["adb", "-s",devices_id,"shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ Đã mở URL {url} trên thiết bị:{devices_id}")
            print(f"📄 Tên file: {filename}")
            print("⏳ Đang chờ 5 giây để video tải...")
            time.sleep(5)
            adb_screencap()
            find_and_tap(os.path.join("image","play.png"), long_press=True)
            time.sleep(1)
            adb_screencap()
            if find_and_tap(os.path.join("./image/download.png"), long_press=False):
                print("✅ Đã thực hiện tải video.")
            time.sleep(10)  # chờ thêm 10 giây để đảm bảo video tải xong
        else:
            print(f"❌ Lỗi khi mở URL:")
            print(result.stderr)
    except FileNotFoundError:
        print("❌ Không tìm thấy adb. Hãy chắc chắn rằng đã cài adb và thêm vào PATH.")

def get_tiktok_package():
    """Lấy package TikTok từ file .env, ưu tiên com.ss.android.ugc.trill"""
    dotenv.load_dotenv(".env")
    pkgs = os.getenv("TIKTOK_PACKAGE", "com.ss.android.ugc.trill,com.zhiliaoapp.musically")
    pkg_list = [pkg.strip() for pkg in pkgs.split(",") if pkg.strip()]
    return pkg_list

def open_tiktok_app():
    """Mở ứng dụng TikTok trên thiết bị Android, thử lần lượt các package"""
    packages = get_tiktok_package()
    for pkg in packages:
        try:
            result = subprocess.run(
                ["adb", "shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✅ Đã mở ứng dụng TikTok với package: {pkg}")
                time.sleep(5)

                adb_screencap() 
                find_and_tap(os.path.join(ICON_DIR, "profile.png"),long_press=False)
                return True
            else:
                print(f"❌ Lỗi khi mở ứng dụng TikTok với package {pkg}:")
                print(result.stderr)
        except FileNotFoundError:
            print("❌ Không tìm thấy adb. Hãy chắc chắn rằng đã cài adb và thêm vào PATH.")
            return False
    print("❌ Không mở được ứng dụng TikTok với bất kỳ package nào.")
    return False
def account_logined():
    """Bấm vào icon plus.png sau khi cộng 90 pixel theo chiều y, trừ 90 pixel theo chiều x"""
    adb_screencap()
    screenshot = "screen.jpg"
    template_path = os.path.join(ICON_DIR, "plus.png")
    img_rgb = cv2.imread(screenshot)
    template = cv2.imread(template_path)

    if img_rgb is None or template is None:
        print(f"❌ Không load được ảnh: {template_path}")
        return False

    h, w = template.shape[:2]
    result = cv2.matchTemplate(img_rgb, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.8
    loc = np.where(result >= threshold)

    if len(loc[0]) > 0:
        pt = (loc[1][0] + w // 2 -90, loc[0][0] + h // 2 + 90)  # trừ 90 pixel theo chiều x, cộng 90 pixel theo chiều y
        print(f"👉 Found plus.png at {pt} (đã -90 pixel x, +60 pixel y)")
        # Vẽ ô highlight để debug
        cv2.rectangle(img_rgb, (pt[0]-w//2, pt[1]-h//2), (pt[0]+w//2, pt[1]+h//2), (0,0,255), 3)
        cv2.imwrite("debug_match.png", img_rgb)
        subprocess.run([
            "adb", "shell",
            f"input tap {pt[0]} {pt[1]}"
        ])
        time.sleep(1)
        return True
    else:
        print("❌ Không tìm thấy plus.png")
        return False
    
def change_account(IMG_ACC, IMG_ID):
    """Thay đổi tài khoản TikTok"""
    adb_screencap() 
    account_logined()
    adb_screencap()
    if find_and_tap(IMG_ACC,long_press=False):
        print("✅ Đã Login tài khoản " + IMG_ACC)
        acc_id = os.path.splitext(os.path.basename(IMG_ACC))[0]  # lấy tên file không có đuôi
        time.sleep(10)
        adb_screencap()

    if find_and_tap(os.path.join(ICON_DIR, "profile.png"), long_press=False):
        adb_screencap()
        profile_id =os.path.splitext(os.path.basename(IMG_ID))[0]  # lấy tên file không có đuôi
    if acc_id != profile_id:
        print(f"⚠️ Tài khoản hiện tại ({profile_id}) khác với tài khoản đăng nhập ({acc_id}). Vui lòng kiểm tra lại.")
    else:
        print(f"✅ Tài khoản hiện tại ({profile_id}) khớp với tài khoản đăng nhập ({acc_id}).")
        return True
def tap_in(x=None, y=None, x_ratio=None, y_ratio=None):
    # Lấy kích thước màn hình từ adb
    result = subprocess.run(
        ["adb", "shell", "wm", "size"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print("❌ Không lấy được kích thước màn hình")
        return False

    output = result.stdout.strip()
    # Ví dụ output: "Physical size: 1080x2400"
    try:
        size_str = output.split(":")[1].strip()
        width, height = map(int, size_str.split("x"))
    except Exception as e:
        print(f"❌ Parse lỗi wm size: {output}, error: {e}")
        return False

    # Nếu dùng ratio
    if x_ratio is not None:
        x = int(width * x_ratio)
    if y_ratio is not None:
        y = int(height * y_ratio)

    if x is None or y is None:
        print("❌ Thiếu tọa độ x,y hoặc x_ratio,y_ratio")
        return False

    # Thực hiện tap
    subprocess.run([
        "adb", "shell",
        f"input tap {x} {y}"
    ])
    print(f"👉 Tap tại ({x},{y})")
    time.sleep(1)
    screenshot = "screen.jpg"
    img = cv2.imread(screenshot)
    if img is not None:
        cv2.circle(img, (x, y), 10, (0, 255, 0), -1)
        cv2.imwrite("debug_match.png", img)
    else:
        print("❌ Không load được screen.jpg để vẽ chấm xanh.")

    return True
        
def upload_video_to_tiktok():
    adb_screencap()
    if find_and_tap(os.path.join(ICON_DIR, "newvideo.png"), long_press=False):
        adb_screencap()
        tap_in(x_ratio=X_ratio, y_ratio=Y_ratio)  # Tap 
        time.sleep(1)
        adb_screencap()
        tap_in(x_ratio=X_ratio_pickup, y_ratio=Y_ratio_pickup)  # Chọn video đầu tiên
        print("✅ Đã chọn video đầu tiên")
        time.sleep(1)
        adb_screencap()
        find_and_tap(os.path.join(ICON_DIR, "next2.png"), long_press=False)
        adb_screencap()
        find_and_tap(os.path.join(ICON_DIR, "next2.png"), long_press=False)
        adb_screencap()

def add_link(devices_id, product_name, caption_text,url):
    if subprocess.run(["adb", "-s", f"{devices_id}", "shell", "ime", "set", "com.android.adbkeyboard/.AdbIME"]):
        print("thiết bị " + devices_id + " đã chuyển sang adbkeyboard")
    time.sleep(1)
    adb_screencap()
    find_and_tap(os.path.join(ICON_DIR, "add_link.png"), long_press=False)
    adb_screencap()
    find_and_tap(os.path.join(ICON_DIR, "shop.png"), long_press=False)
    time.sleep(3)
    adb_screencap()
    find_and_tap(os.path.join(ICON_DIR, "search.png"), long_press=False)
    time.sleep(1)
    subprocess.run([
        "adb", "shell", "am", "broadcast","-a", "ADB_INPUT_TEXT","--es", "msg",f"'{product_name}'"
    ])
    subprocess.run([
        "adb", "shell","input keyevent 66"  # 66 là mã keyevent cho Enter
    ])
    time.sleep(1)
    adb_screencap()
    if not find_and_tap(os.path.join(ICON_DIR, "remind.png"), long_press=False):
        find_and_tap(os.path.join(ICON_DIR, "add.png"), long_press=False)
        time.sleep(1)
        adb_screencap()
    else:
        find_and_tap(os.path.join(ICON_DIR, "remind.png"), long_press=False)
    time.sleep(1)
    adb_screencap()
    subprocess.run([
            "adb", "shell","am","broadcast","-a","ADB_CLEAR_TEXT",
    ])
    time.sleep(1)
    subprocess.run([
        "adb", "shell", "am", "broadcast",
        "-a", "ADB_INPUT_TEXT",
        "--es", "msg", "'Mua ở đây nha'"
    ])
    subprocess.run([
        "adb", "shell",
        "input keyevent 66"  # 66 là mã keyevent cho Enter
    ])
    adb_screencap()
    while(1):       
        find_and_tap(os.path.join(ICON_DIR, "confirm.png"), long_press=False)
        adb_screencap()
         # Kiểm tra nếu không tìm thấy nữa thì thoát vòng lặp
        if not find_and_tap(os.path.join(ICON_DIR, "confirm.png"), long_press=False):
            break   
    time.sleep(1)
    adb_screencap()
    if find_and_tap(os.path.join(ICON_DIR, "caption.png"), long_press=False):
        if subprocess.run([
          "adb", "shell", "am", "broadcast","-a", "ADB_INPUT_TEXT","--es", "msg",f"'{caption_text}'"
        ]):
            subprocess.run([
            "adb","-s",f"{devices_id}", "shell","ime", "set", "com.samsung.android.honeyboard/.service.HoneyBoardService"
            ])
            time.sleep(1)
    adb_screencap()
    if find_and_tap(os.path.join(ICON_DIR, "post.png"), long_press=False):
        print("✅ Đã đăng video lên TikTok")
        time.sleep(10)  # chờ thêm 10 giây để đảm bảo video đăng xong
        video_file_name = os.path.basename(url.split("?")[0])
        path = f"/sdcard/Download/{video_file_name}"
        if subprocess.run([
                "adb","-s",f"{devices_id}", "shell","rm","-rf",path
        ]):
            print(f"✅ Đã xóa video {video_file_name} khỏi thiết bị.") 

if __name__ == "__main__":
    if not rows:
        print("⚠️ Không có dữ liệu trong accounts.json")
        exit(0)

    for i, row in enumerate(rows, start=1):
        print(f"\n=== Xử lý dòng {i}: {row} ===")

        # Đọc thông tin
        devices_id   = row.get("ten_thiet_bi", "").strip()
        url          = row.get("url", "").strip()
        IMG_ACC      = row.get("anh_acc", "").strip()
        IMG_ID       = row.get("anh_id", "").strip()
        product_name = row.get("anh_san_pham", "").strip()
        caption_text = row.get("caption", "").strip()

        # Kiểm tra dữ liệu bắt buộc
        if not devices_id or not url or not IMG_ACC or not IMG_ID:
            print(f"⚠️ Dòng {i} thiếu dữ liệu bắt buộc -> Bỏ qua")
            continue

        print(f"Thiết bị: {devices_id}\n"
              f"URL: {url}\n"
              f"Ảnh acc: {IMG_ACC}\n"
              f"Ảnh id: {IMG_ID}\n"
              f"Tên SP: {product_name}\n"
              f"Caption: {caption_text}")

        # Các bước upload
        try:
            if not open_and_download_video(devices_id,url):
                print("❌ Không tải được video -> bỏ qua dòng này")
                continue

            if not open_tiktok_app():
                print("❌ Không mở được TikTok -> bỏ qua dòng này")
                continue
            adb_screencap()
            if not find_template_in_screenshot(IMG_ID, threshold=0.8):
                if not change_account(IMG_ACC, IMG_ID):
                    print("❌ Không đổi được tài khoản -> bỏ qua dòng này")
                    continue
            else:
                print("✅ Tài khoản đã đúng, không cần đổi")    

            upload_video_to_tiktok()
            add_link(devices_id, product_name=product_name,
                     caption_text=caption_text, url=url)

            print(f"✅ Hoàn tất xử lý cho dòng {i}")

        except Exception as e:
            print(f"❌ Lỗi khi xử lý dòng {i}: {e}")
            continue
