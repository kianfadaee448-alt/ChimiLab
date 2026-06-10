import requests
import ast
import json

url = "https://raw.githubusercontent.com/kianfadaee448-alt/ChemLab-DB/main/README.json"

print("🔄 در حال دانلود آخرین نسخه از گیت‌هاب...")

r = requests.get(url)
r.raise_for_status()
content = r.text.strip()

# استخراج دیکشنری
start = content.find('{')
end = content.rfind('}') + 1
dict_str = content[start:end]

# تبدیل به دیکشنری پایتون
chem_db = ast.literal_eval(dict_str)

# تمیز کردن: حذف تکراری‌ها (آخرین نسخه برنده)
clean_db = {}
for key, value in chem_db.items():
    clean_key = key.strip().lower().replace(" ", "_")   # تمیز کردن کلیدها
    clean_db[clean_key] = value

# ذخیره فایل JSON تمیز
with open('CHEMICAL_DB_clean.json', 'w', encoding='utf-8') as f:
    json.dump(clean_db, f, ensure_ascii=False, indent=4)

print("\n🎉 تبدیل با موفقیت انجام شد!")
print(f"تعداد مواد نهایی: {len(clean_db)}")
print("فایل ذخیره شد: CHEMICAL_DB_clean.json")
print("حالا می‌تونی مستقیم از این فایل استفاده کنی ✅")