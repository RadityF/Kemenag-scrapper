from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import pytesseract
from PIL import Image
import io
import os
from datetime import datetime
import uuid
import logging
from typing import Optional, Tuple, Dict
from ..config import settings

logger = logging.getLogger(__name__)

class KemenagScraper:
    def __init__(self):
        self.max_attempts = settings.max_attempts
        self.timeout = settings.selenium_timeout
        self.screenshot_folder = settings.screenshot_folder
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    def setup_chrome_driver(self) -> webdriver.Chrome:
        """Setup Chrome driver dengan opsi headless"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Use webdriver-manager to handle ChromeDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(self.timeout)
            
            return driver
        except Exception as e:
            logger.error(f"Error setting up Chrome driver: {str(e)}")
            raise

    def scrape_text_elements(self, driver: webdriver.Chrome, wait: WebDriverWait, no_porsi: str) -> Optional[Dict]:
        """Fungsi untuk scraping text dari elemen-elemen yang ditentukan"""
        try:
            scraped_data = {}
            
            # Scraping Nama
            try:
                nama = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="search-tabs"]/div[3]/div/div[2]/div[1]/p[1]')
                )).text.strip()
                scraped_data['nama'] = nama
                logger.info(f"Nama berhasil di-scrape: {nama}")
            except Exception as e:
                logger.warning(f"Error scraping nama: {str(e)}")
                scraped_data['nama'] = None
            
            # Scraping Kabupaten
            try:
                kabupaten = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="search-tabs"]/div[3]/div/div[2]/div[1]/p[2]')
                )).text.strip()
                scraped_data['kabupaten'] = kabupaten
                logger.info(f"Kabupaten berhasil di-scrape: {kabupaten}")
            except Exception as e:
                logger.warning(f"Error scraping kabupaten: {str(e)}")
                scraped_data['kabupaten'] = None
            
            # Scraping Provinsi
            try:
                provinsi = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="search-tabs"]/div[3]/div/div[2]/div[2]/p[1]')
                )).text.strip()
                scraped_data['provinsi'] = provinsi
                logger.info(f"Provinsi berhasil di-scrape: {provinsi}")
            except Exception as e:
                logger.warning(f"Error scraping provinsi: {str(e)}")
                scraped_data['provinsi'] = None
            
            # Scraping Kuota Provinsi Kab/Kota Khusus
            try:
                kuota = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="search-tabs"]/div[3]/div/div[2]/div[2]/p[2]')
                )).text.strip()
                scraped_data['kuota_provinsi_kab_kota_khusus'] = kuota
                logger.info(f"Kuota berhasil di-scrape: {kuota}")
            except Exception as e:
                logger.warning(f"Error scraping kuota: {str(e)}")
                scraped_data['kuota_provinsi_kab_kota_khusus'] = None
            
            # Scraping Status Bayar
            try:
                status_bayar = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="search-tabs"]/div[3]/div/div[2]/div[3]/p[1]')
                )).text.strip()
                scraped_data['status_bayar'] = status_bayar
                logger.info(f"Status Bayar berhasil di-scrape: {status_bayar}")
            except Exception as e:
                logger.warning(f"Error scraping status bayar: {str(e)}")
                scraped_data['status_bayar'] = None
            
            # Scraping Estimasi Keberangkatan (gabungan text nodes)
            try:
                parent_element = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="search-tabs"]/div[3]/div/div[2]/div[3]')
                ))
                
                # Ambil semua text nodes menggunakan JavaScript
                script = """
                var element = arguments[0];
                var textNodes = [];
                for (var i = 0; i < element.childNodes.length; i++) {
                    if (element.childNodes[i].nodeType === 3) { // Text node
                        var text = element.childNodes[i].textContent.trim();
                        if (text) {
                            textNodes.push(text);
                        }
                    }
                }
                return textNodes;
                """
                text_nodes = driver.execute_script(script, parent_element)
                
                # Gabungkan text nodes menjadi satu string
                if text_nodes:
                    estimasi_keberangkatan = ' '.join(text_nodes).strip()
                    scraped_data['estimasi_keberangkatan'] = estimasi_keberangkatan
                    logger.info(f"Estimasi Keberangkatan berhasil di-scrape: {estimasi_keberangkatan}")
                else:
                    scraped_data['estimasi_keberangkatan'] = None
                    
            except Exception as e:
                logger.warning(f"Error scraping estimasi keberangkatan: {str(e)}")
                scraped_data['estimasi_keberangkatan'] = None
            
            # Scraping Waktu Permintaan Informasi
            try:
                waktu_permintaan = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="search-tabs"]/div[3]/div/div[2]/div[3]/p[2]')
                )).text.strip()
                scraped_data['waktu_permintaan_informasi'] = waktu_permintaan
                logger.info(f"Waktu Permintaan Informasi berhasil di-scrape: {waktu_permintaan}")
            except Exception as e:
                logger.warning(f"Error scraping waktu permintaan informasi: {str(e)}")
                scraped_data['waktu_permintaan_informasi'] = None
            
            # Tambahkan no_porsi ke data
            scraped_data['no_porsi'] = no_porsi
            
            logger.info(f"Semua data berhasil di-scrape untuk nomor porsi {no_porsi}")
            return scraped_data
            
        except Exception as e:
            logger.error(f"Error saat scraping text: {str(e)}")
            return None

    def scrape(self, no_porsi: str) -> Tuple[bool, Optional[str], Optional[Dict], Optional[str], int]:
        """
        Main scraping function
        Returns: (success, filename, scraped_data, error_message, attempts_used)
        """
        driver = None
        attempts_used = 0
        
        try:
            logger.info(f"Memproses nomor porsi: {no_porsi}")
            
            driver = self.setup_chrome_driver()
            wait = WebDriverWait(driver, 15)
            
            success = False
            
            # Buka URL dengan error handling
            try:
                driver.get("https://haji.kemenag.go.id/v5/?search=estimation")
                time.sleep(3)
            except Exception as e:
                logger.error(f"Error loading website: {str(e)}")
                return False, None, None, f"Error loading website: {str(e)}", attempts_used
            
            # Loop dengan maksimal attempts
            while not success and attempts_used < self.max_attempts:
                try:
                    attempts_used += 1
                    logger.info(f"Percobaan ke-{attempts_used} untuk nomor {no_porsi}")

                    # Input captcha dengan error handling
                    try:
                        elem = wait.until(EC.visibility_of_element_located((By.ID, "canv")))
                        png = elem.screenshot_as_png
                        img = Image.open(io.BytesIO(png))
                        text = pytesseract.image_to_string(img, lang="eng", config="--oem 3 --psm 7").strip()
                        
                        # Validasi hasil OCR
                        if not text or len(text) < 3:
                            logger.warning(f"OCR result tidak valid: '{text}', mencoba lagi...")
                            time.sleep(2)
                            continue
                            
                    except Exception as e:
                        logger.warning(f"Error reading captcha: {str(e)}")
                        time.sleep(2)
                        continue

                    # Input captcha
                    try:
                        captcha_input = driver.find_element(By.ID, "captcha-input")
                        captcha_input.clear()
                        captcha_input.send_keys(text)
                    except NoSuchElementException:
                        logger.warning("Captcha input element not found")
                        continue

                    # Input nomor porsi
                    try:
                        no_porsi_input = driver.find_element(By.XPATH, '//input[@placeholder="Masukkan Nomor Porsi"]')
                        no_porsi_input.clear()
                        no_porsi_input.send_keys(no_porsi)
                    except NoSuchElementException:
                        logger.warning("Nomor porsi input element not found")
                        continue

                    time.sleep(2)

                    # Klik tombol search
                    try:
                        search_button = driver.find_element(By.XPATH, '//*[@id="search-tabs"]/div[3]/div/div/div[1]/form/button')
                        search_button.click()
                    except NoSuchElementException:
                        logger.warning("Search button not found")
                        continue

                    # Tunggu hasil
                    try:
                        hasil_element = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="search-tabs"]/div[3]/div/div[2]')))
                        time.sleep(2)
                        
                        logger.info(f"Berhasil mendapatkan hasil untuk nomor {no_porsi} (percobaan ke-{attempts_used})")
                        
                        # Screenshot hasil pencarian
                        try:
                            screenshot_png = hasil_element.screenshot_as_png
                            
                            # Generate unique filename dengan timestamp
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            unique_id = str(uuid.uuid4())[:8]
                            filename = f"hasil_{no_porsi}_{timestamp}_{unique_id}.png"
                            filepath = os.path.join(self.screenshot_folder, filename)
                            
                            # Simpan screenshot
                            with open(filepath, 'wb') as file:
                                file.write(screenshot_png)
                            
                            logger.info(f"Screenshot disimpan: {filepath}")
                            
                            # Scrape text dari elemen-elemen
                            scraped_data = self.scrape_text_elements(driver, wait, no_porsi)
                            
                            if scraped_data:
                                success = True
                                return True, filename, scraped_data, None, attempts_used
                            else:
                                logger.warning("Scraping data failed, retrying...")
                                continue
                            
                        except Exception as e:
                            logger.error(f"Error saving screenshot: {str(e)}")
                            continue
                        
                    except TimeoutException:
                        logger.warning(f"Element hasil tidak ditemukan, captcha kemungkinan salah (percobaan ke-{attempts_used})")
                        time.sleep(2)
                        continue
                        
                except Exception as e:
                    logger.warning(f"Error pada percobaan ke-{attempts_used}: {str(e)}")
                    time.sleep(2)
                    continue
            
            # Jika sudah mencapai max attempts dan masih belum berhasil
            if not success:
                error_msg = f"Gagal memproses nomor {no_porsi} setelah {self.max_attempts} percobaan"
                logger.error(error_msg)
                return False, None, None, error_msg, attempts_used
                    
        except Exception as e:
            error_msg = f"Error fatal untuk nomor {no_porsi}: {str(e)}"
            logger.error(error_msg)
            return False, None, None, error_msg, attempts_used
        finally:
            # Pastikan driver selalu ditutup
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    logger.warning(f"Error closing driver: {str(e)}")
        
        return False, None, None, "Unknown error occurred", attempts_used