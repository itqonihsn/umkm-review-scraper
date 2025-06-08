import psycopg2
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import datetime
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# di dalam scrape_ulasan()
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


# 🔗 Koneksi ke DB Cloud SQL PostgreSQL
import os

def connect_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
    )

# 💾 Simpan ke database
def simpan_ke_db(data):
    conn = connect_db()
    cur = conn.cursor()
    insert_query = """
        INSERT INTO ulasan_produk (user_name, nama_produk, rating, review, tanggal)
        VALUES (%s, %s, %s, %s, %s)
    """
    cur.executemany(insert_query, data)
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ {len(data)} data berhasil disimpan ke database.")

# 🚀 Jalankan scraper
def scrape_ulasan():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    url = "https://www.tokopedia.com/mykonos/review"  # URL produk Tokopedia atau marketplace lain
    driver.get(url)
    time.sleep(5)

    data = []
    for i in range(0, 2):
        soup = BeautifulSoup(driver.page_source, "html.parser")
        containers = soup.findAll('article', attrs={'class': 'css-1pr2lii'})
        print(f"🔍 Halaman {i+1} ditemukan {len(containers)} ulasan")

        for container in containers:
            try:
                # tombol "Selengkapnya"
                selengkapnya = container.find('button', {'class': 'css-89c2tx'})
                if selengkapnya:
                    try:
                        driver.execute_script("arguments[0].click();", selengkapnya)
                        time.sleep(1)
                    except:
                        pass  # ignore error

                review_tag = container.find('span', {'data-testid': 'lblItemUlasan'})
                review = review_tag.text if review_tag else None

                user_tag = container.find('span', {'class': 'name'})
                user = user_tag.text if user_tag else None

                nama_tag = container.find('p', {'data-unify': 'Typography'})
                nama_produk = nama_tag.text if nama_tag else None

                rating_tag = container.find('div', {'data-testid': 'icnStarRating'})
                rating = rating_tag.get('aria-label') if rating_tag else None

                tanggal_tag = container.find('p', {'data-unify': 'Typography', 'class': 'css-vqrjg4-unf-heading e1qvo2ff8'})
                tanggal = tanggal_tag.text if tanggal_tag else None

                if all([user, nama_produk, rating, review, tanggal]):
                    # convert tanggal to datetime
                    try:
                        tanggal_obj = datetime.datetime.strptime(tanggal, '%d %B %Y').date()
                    except:
                        tanggal_obj = None

                    data.append((user, nama_produk, rating, review, tanggal_obj))
                else:
                    print("⚠️ Data tidak lengkap, dilewati")

            except Exception as e:
                print("❌ Error parsing container:", e)
                continue

        time.sleep(4)
        try:
            driver.find_element(By.CSS_SELECTOR, "button[aria-label^='Laman berikutnya']").click()
        except Exception as e:
            print("⚠️ Gagal klik tombol next:", e)
            break
        time.sleep(6)

    driver.quit()

    # Simpan ke DB
    if data:
        simpan_ke_db(data)
    else:
        print("📭 Tidak ada data untuk disimpan.")

# Run
scrape_ulasan()
