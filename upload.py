import subprocess,base64
import os
import cv2
import numpy as np
import time
import dotenv
from tinydb import TinyDB, Query
from PIL import Image
import io

X_ratio=0.8
Y_ratio=0.8
X_ratio_pickup=0.1
Y_ratio_pickup=0.25
ICON_DIR = "image/"  # thư mục chứa icon mẫu
ID_DIR = "img_id/"  # thư mục chứa id  mẫu
ACC_DIR = "img_acc/"  # thư mục chứa acc  mẫu

db= TinyDB('accounts.json')
rows = db.all()
adb_path = "adb"  # nếu adb đã có trong PATH thì để nguyên

def adb_screencap(device_id):
    # Thư mục lưu ảnh
    folder = "screenshot_devices"
    os.makedirs(folder, exist_ok=True)

    # Tên file lưu
    local_path = os.path.join(folder, f"{device_id}_screen.png")

    try:
        # File tạm trên thiết bị
        remote_path = f"/sdcard/{device_id}_screen.png"

        # Chụp ảnh màn hình trên thiết bị
        subprocess.run([adb_path, "-s", device_id, "shell", "screencap", "-p", remote_path], check=True)

        # Kéo file về máy
        subprocess.run([adb_path, "-s", device_id, "pull", remote_path, local_path], check=True)

        # Xóa file tạm trên thiết bị
        subprocess.run([adb_path, "-s", device_id, "shell", "rm", remote_path], check=True)

        print(f"📸 Đã lưu screenshot: {local_path}")
        return local_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Screenshot failed for {device_id}: {e}")
        return None



def find_template_in_screenshot(devices_id, template_path, threshold=0.8):
    """Tìm icon trong ảnh bằng template matching"""
    screenshot="screenshot_devices/" + devices_id + "_screen.png"
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

def find_and_tap(devices_id,template_path, threshold=0.6, long_press=False):
    """Tìm icon trong màn hình bằng template matching và tap"""
    screenshot="screenshot_devices/" + devices_id + "_screen.png"
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
        cv2.rectangle(img_rgb,
              (pt[0]-w//2, pt[1]-h//2),
              (pt[0]+w//2, pt[1]+h//2),
              (0,255,255), 3) 
        cv2.circle(img_rgb, pt, 5, (0,255,0), -1)
        cv2.imwrite("debug_match.png", img_rgb)

        # Thực hiện thao tác
        if long_press:
            subprocess.run([
                "adb","-s", devices_id ,"shell",
                f"input swipe {pt[0]} {pt[1]} {pt[0]} {pt[1]} 1000"
            ])
        else:
            subprocess.run([
                "adb","-s",devices_id, "shell",
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
            adb_screencap(devices_id)
            find_and_tap(devices_id,os.path.join(ICON_DIR,"3dot.png"), long_press=False)
            time.sleep(1)
            adb_screencap(device_id=devices_id)
            if find_and_tap(devices_id,os.path.join("./image/downloadvideo.png"), long_press=False):
                adb_screencap(devices_id)
                try:
                    find_and_tap(devices_id,os.path.join(ICON_DIR,"continue.png"), long_press=False)
                    print("Da cap quyen truy cap bo nho")
                    adb_screencap(devices_id)
                    find_and_tap(devices_id,os.path.join(ICON_DIR,"allow.png"))
                except Exception:
                    return True          
            print("✅ Đã thực hiện tải video.")
            return True
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

def open_tiktok_app(devices_id):
    """Mở ứng dụng TikTok trên thiết bị Android, thử lần lượt các package"""
    packages = get_tiktok_package()
    for pkg in packages:
        try:
            result = subprocess.run(
                ["adb","-s",devices_id, "shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✅ Đã mở ứng dụng TikTok trên {devices_id} với package: {pkg}")
                time.sleep(10)

                adb_screencap(devices_id) 
                tap_in(devices_id, x_ratio=0.95, y_ratio=0.95)
                # find_and_tap(devices_id,os.path.join(ICON_DIR, "profile.png"),long_press=False)
                return True
            else:
                print(f"❌ Lỗi khi mở ứng dụng TikTok với package {pkg}:")
                print(result.stderr)
        except FileNotFoundError:
            print("❌ Không tìm thấy adb. Hãy chắc chắn rằng đã cài adb và thêm vào PATH.")
            return False
    print("❌ Không mở được ứng dụng TikTok với bất kỳ package nào.")
    return False
def account_logined(devices_id):
    """Bấm vào icon plus.png sau khi cộng 90 pixel theo chiều y, trừ 90 pixel theo chiều x"""
    time.sleep(5)
    adb_screencap(device_id=devices_id)
    screenshot = "screenshot_devices/" + devices_id + "_screen.png"
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
        pt = (loc[1][0] + w // 2 -60, loc[0][0] + h // 2 + 120)  # trừ 90 pixel theo chiều x, cộng 90 pixel theo chiều y
        print(f"👉 Found plus.png at {pt} (đã -90 pixel x, +60 pixel y)")
        # Vẽ ô highlight để debug
        cv2.rectangle(img_rgb, (pt[0]-w//2, pt[1]-h//2), (pt[0]+w//2, pt[1]+h//2), (0,0,255), 3)
        cv2.imwrite("debug_match.png", img_rgb)
        subprocess.run([
            "adb","-s",devices_id, "shell",
            f"input tap {pt[0]} {pt[1]}"
        ])
        time.sleep(1)
        return True
    else:
        print("❌ Không tìm thấy plus.png")
        return False
    
def change_account(devices_id, IMG_ACC, IMG_ID):
    """Thay đổi tài khoản TikTok"""
    account_logined(devices_id)
    
    adb_screencap(device_id=devices_id)
    if find_and_tap(devices_id, IMG_ACC, long_press=False):
        print("✅ Đã Login tài khoản " + IMG_ACC)
        acc_id = os.path.splitext(os.path.basename(IMG_ACC))[0]  # lấy tên file không có đuôi
        time.sleep(10)
        adb_screencap(device_id=devices_id)
        
    tap_in(devices_id, x_ratio=0.95, y_ratio=0.95)
    return True
    # if find_and_tap(devices_id,os.path.join(ICON_DIR, "profile.png"), long_press=False):
    #     adb_screencap(device_id=devices_id)
    #     profile_id =os.path.splitext(os.path.basename(IMG_ID))[0]  # lấy tên file không có đuôi
    
    # if acc_id != profile_id:
    #     print(f"⚠️ Tài khoản hiện tại ({profile_id}) khác với tài khoản đăng nhập ({acc_id}). Vui lòng kiểm tra lại.")
    #     return False
    # else:
    #     print(f"✅ Tài khoản hiện tại ({profile_id}) khớp với tài khoản đăng nhập ({acc_id}).")
    #     return True
def tap_in(devices_id, x=None, y=None, x_ratio=None, y_ratio=None):
    try:
        screen_image = adb_screencap(devices_id)
        width = None
        height = None
        with Image.open(screen_image) as img:
            width = img.width
            height = img.height
        print(width, height)
    except Exception as e:
        print(f"❌ Không lấy đc kích thước màn hình {e}")
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
        "adb", "-s", devices_id, "shell", "input", "tap", str(x), str(y)
    ])
    print(f"👉 Tap tại ({x},{y})")

    time.sleep(5)
    # screenshot = "screen.jpg"
    # img = cv2.imread(screenshot)
    # if img is not None:
    #     cv2.circle(img, (x, y), 10, (0, 255, 0), -1)
    #     cv2.imwrite("debug_match.png", img)
    # else:
    #     print("❌ Không load được screen.jpg để vẽ chấm xanh.")

    return True
def adb_clear_downloads(device_id):
    """
    Xóa toàn bộ file trong thư mục /sdcard/Download.

    Args:
        device_id (str): ID của thiết bị adb
    """
    clear_cmd = ["adb", "-s", device_id, "shell", "rm", "-rf", "/sdcard/Download/*"]
    result = subprocess.run(clear_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"❌ ADB clear lỗi: {result.stderr.strip()}")

    print("🗑️ Đã xóa toàn bộ file trong /sdcard/Download")
    
def adb_push_file(device_id, local_path):
    """
    Push file vào thư mục /sdcard/Download và scan để hiện trong Gallery.

    Args:
        device_id (str): ID của thiết bị adb (vd: "ce11160b6411822f05")
        local_path (str): Đường dẫn file trên PC
    """
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Không tìm thấy file: {local_path}")

    filename = os.path.basename(local_path)
    remote_path = f"/sdcard/Download/{filename}"

    # Push file
    push_cmd = ["adb", "-s", device_id, "push", local_path, remote_path]
    result = subprocess.run(push_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ADB push lỗi: {result.stderr.strip()}")

    # Quét lại để Gallery thấy file
    scan_cmd = [
        "adb", "-s", device_id, "shell", "am", "broadcast",
        "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
        "-d", f"file://{remote_path}"
    ]
    subprocess.run(scan_cmd, capture_output=True, text=True)

    print(f"✅ Đã push file: {local_path} → {remote_path}")
    print("👉 File đã sẵn sàng trong Gallery.")


def adb_delete_file(device_id, filename):
    """
    Xóa file trong thư mục /sdcard/Download.

    Args:
        device_id (str): ID của thiết bị adb
        filename (str): Tên file cần xóa (vd: "test.mp4")
    """
    remote_path = f"/sdcard/Download/{filename}"

    rm_cmd = ["adb", "-s", device_id, "shell", "rm", remote_path]
    result = subprocess.run(rm_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ADB rm lỗi: {result.stderr.strip()}")

    print(f"🗑️ Đã xóa file: {remote_path}")
        
def upload_video_to_tiktok(devices_id):
    tap_in(devices_id, x_ratio=0.5, y_ratio=0.95)
    adb_screencap(device_id=devices_id)
    tap_in(devices_id, x_ratio=X_ratio, y_ratio=Y_ratio)  # Tap 
    time.sleep(1)
    adb_screencap(device_id=devices_id)
    tap_in(devices_id, x_ratio=X_ratio_pickup, y_ratio=Y_ratio_pickup)  # Chọn video đầu tiên
    print("✅ Đã chọn video đầu tiên")
    time.sleep(1)
    adb_screencap(device_id=devices_id)
    find_and_tap(devices_id,os.path.join(ICON_DIR, "next.png"), long_press=False)
    adb_screencap(device_id=devices_id)
    find_and_tap(devices_id,os.path.join(ICON_DIR, "next.png"), long_press=False)
        
def add_link(device_id, product_name, caption_text,url):
    if subprocess.run(["adb", "-s", f"{device_id}", "shell", "ime", "set", "com.android.adbkeyboard/.AdbIME"]):
        print("thiết bị " + devices_id + " đã chuyển sang adbkeyboard")
    time.sleep(1)
    adb_screencap(device_id=device_id)
    find_and_tap(device_id, os.path.join(ICON_DIR, "add_link.png"), long_press=False)
    adb_screencap(device_id=device_id)
    find_and_tap(device_id, os.path.join(ICON_DIR, "shop.png"), long_press=False)
    time.sleep(3)
    adb_screencap(device_id=device_id)
    find_and_tap(device_id, os.path.join(ICON_DIR, "search.png"), long_press=False)
    time.sleep(1)
    subprocess.run(
        ["adb", "-s", device_id, "shell", "am", "broadcast", "-a", "ADB_CLEAR_TEXT"],
        check=True
    )
    time.sleep(1)
    print('product_name', product_name)
    subprocess.run([
        "adb","-s", device_id, "shell", "am", "broadcast","-a", "ADB_INPUT_TEXT","--es", "msg",f"'{product_name}'"
    ])
    time.sleep(1)
    subprocess.run(
        ["adb", "-s", device_id, "shell", "input", "keyevent", "66"],
        check=True
    )
    time.sleep(1)
    adb_screencap(device_id=device_id)
    if not find_and_tap(device_id,os.path.join(ICON_DIR, "remind.png"), long_press=False):
        find_and_tap(device_id,os.path.join(ICON_DIR, "add.png"), long_press=False)
        time.sleep(1)
        adb_screencap(device_id=device_id)
    else:
        find_and_tap(device_id,os.path.join(ICON_DIR, "remind.png"), long_press=False)
    time.sleep(1)
    adb_screencap(device_id=device_id)
    subprocess.run(
        ["adb", "-s", device_id, "shell", "am", "broadcast", "-a", "ADB_CLEAR_TEXT"],
        check=True
    )
    time.sleep(1)
    subprocess.run([
        "adb","-s" ,device_id,"shell", "am", "broadcast",
        "-a", "ADB_INPUT_TEXT",
        "--es", "msg", "'Mua ở đây'"
    ])
    time.sleep(1)
    subprocess.run(
        ["adb", "-s", device_id, "shell", "input", "keyevent", "66"],
        check=True
    )
    time.sleep(1)
    adb_screencap(device_id=devices_id)
    while(1):       
        find_and_tap(devices_id,os.path.join(ICON_DIR, "confirm.png"), long_press=False)
        adb_screencap(device_id=devices_id)
         # Kiểm tra nếu không tìm thấy nữa thì thoát vòng lặp
        if not find_and_tap(devices_id,os.path.join(ICON_DIR, "confirm.png"), long_press=False):
            break   
    time.sleep(1)
    adb_screencap(device_id=devices_id)
    if find_and_tap(devices_id,os.path.join(ICON_DIR, "caption.png"), long_press=False):
        if subprocess.run([
          "adb","-s", f"{device_id}", "shell", "am", "broadcast","-a", "ADB_INPUT_TEXT","--es", "msg",f"'{caption_text + " "}'"
        ]):
            subprocess.run([
            "adb","-s",f"{device_id}", "shell", "ime", "set", "com.samsung.android.honeyboard/.service.HoneyBoardService"
            ])
            time.sleep(1)
            
    adb_screencap(device_id=device_id)
    if find_and_tap(device_id,os.path.join(ICON_DIR, "post.png"), long_press=False):
        print("✅ Đã đăng video lên TikTok")
        time.sleep(10)  # chờ thêm 10 giây để đảm bảo video đăng xong
        video_file_name = os.path.basename(url.split("?")[0])
        path = f"/sdcard/Download/{video_file_name}"
        if subprocess.run([
                "adb","-s",f"{device_id}", "shell","rm","-rf",path
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
            # if not open_and_download_video(devices_id,url):
            #     print("❌ Không tải được video -> bỏ qua dòng này")
            #     continue
            adb_clear_downloads(devices_id)
            
            adb_push_file(devices_id, r"D:\TOOL\new upload video\uploadVideo\source_video\AFF.mp4")

            if not open_tiktok_app(devices_id):
                print("❌ Không mở được TikTok -> bỏ qua dòng này")
                continue
            time.sleep(5)
            adb_screencap(device_id=devices_id)
            
            if not find_template_in_screenshot(devices_id, IMG_ID, threshold=0.8):
                if not change_account(devices_id, IMG_ACC, IMG_ID):
                    print("❌ Không đổi được tài khoản -> bỏ qua dòng này")
                    continue
            else:
                print("✅ Tài khoản đã đúng, không cần đổi")    

            upload_video_to_tiktok(devices_id)
            
            add_link(devices_id, product_name=product_name,caption_text=caption_text, url=url)
            
            adb_delete_file(devices_id, "AFF.mp4")
            
            print(f"✅ Hoàn tất xử lý cho dòng {i}")

        except Exception as e:
            print(f"❌ Lỗi khi xử lý dòng {i}: {e}")
            continue
