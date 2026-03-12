# Bitingizni Serverda va GitHub-da ishga tushirish qollanmasi

Bu qollanma orqali siz o'zingizning Telegram botingizni GitHub ga yuklab, so'ng bepul yoki pullik serverlarga (masalan: Render, Railway, Heroku, yoxud o'zingizning VPS serveringizga) qanday joylashtirishni (deploy qilishni) o'rganasiz.

## 1-Qadam: Loyihani GitHub ga yuklash

Loyihangiz fayllari orasida `.gitignore` fayli borligiga ishonch hosil qiling. Unda manba kodi bilan birga saqlanmasligi kerak bo'lgan keraksiz va maxfiy fayllar (masalan, `__pycache__`, bazalar `*.db`, `.env` kabi fayllar) ko'satilgan bo'ladi. Men buni avtomatik tarzda yaratib qo'ydim.

1. Agar sizda Git o'rnatilmagan bo'lsa, [git-scm.com](https://git-scm.com/) orqali o'rnating.
2. Terminalda bot joylashgan papkaga o'ting (hozirgi papkada).
3. Quyidagi buyruqlarni terminalda birin-ketin tering:

```bash
git init
git add .
git commit -m "Botning dastlabki versiyasi (quiz olib tashlandi)"
```

4. [GitHub.com](https://github.com/)-da yangi "Repository" (repo) oching.
5. GitHub bergan yo'riqnomadagi quyidagi qatorlarni terminalga kiriting (O'z repongiz ssilkasini qo'ying):

```bash
git branch -M main
git remote add origin https://github.com/SizningUsername/RepozitoriyaNomi.git
git push -u origin main
```

## 2-Qadam: Serverga joylashtirish (Deploy)

Eng oson va bepul variantlardan biri - **Render.com** yoki **Railway.app**. Quyida shular haqida qisqacha ko'rsatma:

### Render.com (Bepul varianti bor)

1. [Render.com](https://render.com/) saytida ro'yxatdan o'ting (GitHub orqali kirish eng qulayi).
2. "New+" tugmasini bosib, "Web Service" ni tanlang (Yoki "Background Worker" botlar uchun yaxshiroq, lekin botingiz webhook ishlatmasa, Background worker qulay).
3. "Build and deploy from a Git repository" tanlang.
4. O'zingiz yaratgan GitHub reponi ulang va tanlang.
5. Maxsus sozlamalarni kiriting:
   - **Name**: Botingiz nomi (ixtiyoriy)
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
6. **Environment Variables** bo'limida "Add Environment Variable" qilib, maxfiy `.env` faylingizdagi o'zgaruvchilarni kiriting:
   - `BOT_TOKEN` = (sizning tokeningiz)
   - `ADMIN_ID` = (admin idsi)
7. Sahifaning pastki qismidagi "Create Web Service" tugmasini bosing.
   Render.com avtomat ravishda botingizni ishga tushiradi!

> [!NOTE]
> Botingiz SQLite ma'lumotlar bazasi (`edu_star.db`) bilan ishlashini hisobga olsak, bulutli xizmatlar (Render, Heroku kabilar) server qayta ishga tushganda bazani tozalab yuborishi mumkin. Haqiqiy va ishonchli foydalanish uchun VPS (virtual server) olish yoki PostgreSQL kabi online database turlaridan foydalanish tavsiya etiladi. Lekin boshlash uchun hozirgi usul yaxshi.

### VPS (Virtual Private Server) - Masalan, Beget, Hostinger yoki Hetzner orqali

1. VPS sotib olganingizdan so'ng, SSH orqali unga ulaning:
   `ssh root@ip_manzilingiz`
2. Serverga kerakli dastullarni o'rnating (Python va Git):
   `sudo apt update && sudo apt install python3 python3-pip git -y`
3. GitHub dan repongizni ko'chirib oling:
   `git clone https://github.com/SizningUsername/RepozitoriyaNomi.git`
   `cd RepozitoriyaNomi`
4. Dasturni kutubxonalarini o'rnating:
   `pip install -r requirements.txt`
5. `.env` faylini serverda yarating:
   `nano .env`
   Fayl ichiga `BOT_TOKEN`, `ADMIN_ID` kabi ma'lumotlarni yozing, va saqlab chiqing (`Ctrl + O`, `Enter`, `Ctrl + X`).
6. Botni orqa fonda ishlashi uchun `screen` yoki `tmux`, yoki undan ham yaxshisi `systemd` servisi orqali ishga tushiring:
   `screen -S bot`
   `python3 main.py`
   Bot ishlashni boshlagach, `Ctrl + A, D` tugmalarini bosib fonda qoldirishingiz mumkin.

Zarur bo'lsa qo'shimcha yordam so'rashingiz mumkin!
