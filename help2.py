import os
import ast
import json

print("=== تبدیل CUSTOM_REACTIONS.txt به JSON ===\n")

# مسیر دسکتاپ
desktop = os.path.join(os.path.expanduser("~"), "Desktop")

input_file = os.path.join(desktop, "CUSTOM_REACTIONS.txt")
output_file = os.path.join(desktop, "CUSTOM_REACTIONS.json")

# اگر فایل پیدا نشد، مسیر دقیق رو بگیر
if not os.path.exists(input_file):
    print("❌ فایل CUSTOM_REACTIONS.txt روی دسکتاپ پیدا نشد!")
    input_file = input("مسیر کامل فایل txt رو وارد کن:\n> ").strip()

# خوندن فایل
with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read().strip()

# استخراج دیکشنری
start = content.find('{')
end = content.rfind('}') + 1
dict_str = content[start:end]

# تبدیل به دیکشنری پایتون
reactions_db = ast.literal_eval(dict_str)

# حذف تکراری‌ها (آخرین نسخه نگه داشته می‌شه)
clean_db = {}
for key, value in reactions_db.items():
    clean_db[key] = value

# ذخیره به صورت JSON تمیز
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(clean_db, f, ensure_ascii=False, indent=4)

print("\n🎉 تبدیل با موفقیت انجام شد!")
print(f"فایل JSON ذخیره شد:")
print(output_file)
print(f"تعداد واکنش‌های شیمیایی: {len(clean_db)}")
input("\nEnter بزن تا برنامه بسته بشه...")