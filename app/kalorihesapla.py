import http.client
import json
import tkinter
from tkinter import messagebox, Scrollbar, Canvas, ttk
from dotenv import load_dotenv
import os
import sqlite3


load_dotenv()  # .env dosyalarını Golang çalışırken keyleri daha güvende tutmak için kullanıldığı öğrenmiştim. Bu projede de kullanmak istedim.

api_key = os.getenv("COLLECT_API")

Tr2En = str.maketrans("ÇĞİÖŞÜçğıöşüâ", "CGiOSUcgiosua")

def mevsim_secim(event):
    ay = lbmevsim.get(tkinter.ACTIVE)
    conn.request("GET", "/food/whenFoods?ay="+ay, headers=headers)
    res = conn.getresponse()
    data = res.read()
    veri =json.loads(data)

    lbsonuc.delete(0, tkinter.END)
    
    if "result" in veri and isinstance(veri["result"], dict):
        mevsim_meyve = veri["result"].get('mevsim_meyve', ['Bilinmiyor'])
        mevsim_sebze = veri["result"].get('mevsim_sebze', ['Bilinmiyor'])
        her_zaman_sebze = veri["result"].get('her_zaman_sebze', ['Bilinmiyor'])     
        lbsonuc.insert(tkinter.END, f"🍉 Mevsim Meyveleri: {', '.join(mevsim_meyve)}")
        lbsonuc.insert(tkinter.END, f"🥬 Mevsim Sebzeleri: {', '.join(mevsim_sebze)}")
        lbsonuc.insert(tkinter.END, f"🌿 Her Mevsim Yenen Sebzeler: {', '.join(her_zaman_sebze)}")
        lbsonuc.insert(tkinter.END, "")
    else:
        lbsonuc.insert(tkinter.END, "Sonuç bulunamadı veya API yanıtı hatalı.")

# Yapay zekadan büyük ölçüde yardım aldım bu kısımda. Çünkü mevsim yiyecekleri bana liste olarak geliyordu. Diğer kısımdaki gibi
# for döngüsü kullanmak yerine if kullanarak durumu düzeltmek gerekiyormuş. Durumu yapay zeka çözmekte zorlandı.


def yiyecek_secim(event):
    yiyecek = lbyiyecek.get(tkinter.ACTIVE).translate(Tr2En)
    conn.request("GET", "/food/calories?query="+yiyecek, headers=headers)
    res = conn.getresponse()
    data = res.read()
    veri = json.loads(data)

    lbsonuc.delete(0, tkinter.END)
    
    for i in veri["result"]:
        lbsonuc.insert(tkinter.END, f"{i['name']} = {i['kcal']}")
    
    if not veri["result"]:
        lbsonuc.insert(tkinter.END, "⚠️ Sonuç bulunamadı.")

    # Scrollbar güncellemesi (yapay zeka kullanıldı)
    frame2_canvas.update_idletasks()
    frame2_canvas.config(scrollregion=frame2_canvas.bbox("all"))


def topla_kalori(): #yapay zeka ile yapıldı
    toplam = 0
    secilenler = lbsonuc.curselection()
    for i in secilenler:
        metin = lbsonuc.get(i)
        try:
            kalori = int(metin.split('=')[1].strip().split(" ")[0])
            toplam += kalori
        except (IndexError, ValueError):
            continue
    toplam_kalori_var.set(f"{toplam}")

def temizle_sonuc():
    lbsonuc.delete(0, tkinter.END)
    toplam_kalori_var.set("0 kcal")

conn = http.client.HTTPSConnection("api.collectapi.com")

def kaydet_yiyecek():
    secilenler = lbsonuc.curselection()
    for i in secilenler:
        metin = lbsonuc.get(i)
        # "Yiyecek İsmi = 123" formatında ise:
        if "=" in metin:
            isim, kalori = metin.split("=")
            isim = isim.strip()
            try:
                kalori = int(kalori.strip().split(" ")[0])
            except ValueError:
                kalori = 0
            cursor.execute("INSERT INTO yiyecekler (isim, kalori) VALUES (?, ?)", (isim, kalori))
    conn_db.commit()
    messagebox.showinfo("Başarılı", "Seçilen yiyecekler kaydedildi.")

headers = {
    'content-type': "application/json",
    'authorization': "apikey " +api_key
    }

pen = tkinter.Tk()
pen.title("🥗 Kalori ve Mevsimsel Besin Bilgisi")
pen.grid_columnconfigure((0, 1, 2), weight=1, uniform="column")

toplam_kalori_var = tkinter.StringVar(value="0 kcal")

# 3 alana ayırdım (yapay zeka yardım aldım, uniform her sütunu eşit genişlikte olması için)
pen.grid_columnconfigure(0, weight=1, uniform="column")
pen.grid_columnconfigure(1, weight=1, uniform="column")
pen.grid_columnconfigure(2, weight=1, uniform="column")

# Besinler
frame1 = tkinter.Frame(pen, borderwidth=2, relief="groove", bd=5)
frame1_canvas = Canvas(frame1)
frame1.grid(row=0, column=0, sticky="nsew")  # Çerçeveyi genişletmek için sticky eklendi (AI)
lbyiyecek = tkinter.Listbox(frame1, height=20, bg="white", font="Calibri", selectbackground="green")
ttk.Label(frame1, text="🥗 BESİNLER", font="Calibri 20",background="green",foreground="white").pack(pady=5)
scrollbaryiyecek = Scrollbar(lbyiyecek, orient="vertical", command=frame1_canvas.yview)
scrollbaryiyecek.pack(side="right", fill="y")
lbyiyecek.config(yscrollcommand=scrollbaryiyecek.set)
frame1_canvas.configure(yscrollcommand=scrollbaryiyecek.set)
lbyiyecek.pack(fill="both", expand=True)  
for i in open("yiyecekler.txt", encoding="utf-8"):
    lbyiyecek.insert(tkinter.END, i[:-1])
lbyiyecek.bind('<Double-1>', yiyecek_secim)

# Sonuçlar
frame2 = tkinter.Frame(pen, borderwidth=2, relief="groove",bd=5, width=300)
frame2.grid(row=0, column=1, sticky="nsew") #sticky kısmında AI kullandım, pencere boyutuna göre ölçeklemek için)
ttk.Label(frame2, text="📋 SONUÇ", font="Calibri 20",background="green",foreground="white").pack(pady=5)
lbsonuc = tkinter.Listbox(frame2, height=20, bg="white", font="Calibri", selectbackground="green",selectmode="multiple")
lbsonuc.pack(fill="both", expand=True)
# Canvas ve Scrollbar ile kaydırılabilir alan (yapay zeka yardımı)
frame2_canvas = Canvas(frame2)
frame2_canvas.pack(side="left", fill="y", expand=True)
scrollbarsonuc1 = Scrollbar(lbsonuc, orient="vertical", command=frame2_canvas.yview)
scrollbarsonuc1.pack(side="right", fill="y")
lbsonuc.config(yscrollcommand=scrollbarsonuc1.set)
frame2_canvas.configure(yscrollcommand=scrollbarsonuc1.set)
scrollbarsonuc2 = Scrollbar(lbsonuc,orient="horizontal",command=frame2_canvas.xview)
scrollbarsonuc2.pack(side="bottom", fill = "x")
lbsonuc.config(xscrollcommand= scrollbarsonuc2.set)
frame2_canvas.configure(xscrollcommand=scrollbarsonuc2.set)

ttk.Button(frame2, text="Topla", command=topla_kalori).pack(anchor="center",fill="x")
ttk.Button(frame2, text="Sepeti Temizle", command=temizle_sonuc).pack(pady=(0, 10))
ttk.Label(frame2, text="Toplam Kalori", font=("Segoe UI", 10, "bold")).pack(pady=(10, 0))
entry_toplam = ttk.Entry(frame2, textvariable=toplam_kalori_var, state="readonly", justify="center")
entry_toplam.pack(pady=(0, 10), ipadx=10)


# Mevsimler
frame3 = tkinter.Frame(pen, borderwidth=2, relief="groove", bd=5)
frame3.grid(row=0, column=2, sticky="nsew")  # Çerçeveyi genişletmek için sticky eklendi (AI)
ttk.Label(frame3, text="🌤️ MEVSİMLER", font="Calibri 20",background="green",foreground="white").pack(pady=5)
lbmevsim = tkinter.Listbox(frame3, height=20, bg="white", font="Calibri", selectbackground="green")
lbmevsim.pack(fill="both", expand=True)
for i in open("mevsim.txt"):
    lbmevsim.insert(tkinter.END, i[:-1])
lbmevsim.bind('<Double-1>', mevsim_secim)

frame2_content = tkinter.Frame(frame2_canvas)
frame2_canvas.create_window((0, 0), window=frame2_content, anchor="nw")

# Veritabanı
conn_db = sqlite3.connect("kayitli_yiyecekler.db")
cursor = conn_db.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS yiyecekler (
    id INTEGER PRIMARY KEY,
    isim TEXT,
    kalori INTEGER
)
""")

conn_db.commit()

ttk.Button(frame2, text="Kaydet", command=kaydet_yiyecek).pack(anchor="center", fill="x")

pen.mainloop()
conn_db.close()