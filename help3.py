from PIL import Image

try:
    # مسیری که فایل icon2.ico شما قرار دارد (اگر در همان پوشه است، فقط نام فایل کافیست)
    ico_path = 'D:\\chimiproject\\icon2.ico'
    png_path = 'D:\\chimiproject\\icon2.png' # مسیر و نام فایل خروجی PNG

    # باز کردن فایل ICO
    img = Image.open(ico_path)

    # ذخیره کردن به فرمت PNG
    # اگر ICO چند آیکون دارد، این دستور معمولاً اولین آیکون را ذخیره می‌کند.
    img.save(png_path, 'PNG')
    print(f"فایل با موفقیت به {png_path} تبدیل شد.")

except FileNotFoundError:
    print(f"خطا: فایل {ico_path} یافت نشد. لطفاً مسیر فایل را بررسی کنید.")
except Exception as e:
    print(f"خطا در تبدیل فایل: {e}")
