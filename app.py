#!/usr/bin/env python3
"""
Еженедельный парсинг «Пятерочка» (Брянск) → PDF
"""
import os
import csv
import datetime as dt
import requests
import tabula
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
TARGET_FILE = os.path.join(BASE_DIR, 'targets.txt')
PDF_FILE    = os.path.join(BASE_DIR, f"PyatPrices_{dt.date.today():%Y-%m-%d}.pdf")

def download_catalog():
    """Скачивает PDF-каталог за текущую неделю."""
    tue = (dt.date.today() + dt.timedelta(days=(1-dt.date.today().weekday())%7)).strftime('%y%m%d')
    pdf_path = os.path.join(BASE_DIR, f'pyat_{tue}.pdf')
    url = f'https://katoteka.ru/pya/{tue}/bry/catalog.pdf'
    with open(pdf_path, 'wb') as f:
        f.write(requests.get(url, timeout=30).content)
    return pdf_path

def parse_prices(pdf_path):
    """Парсит нужные товары из PDF."""
    df = tabula.read_pdf(pdf_path, pages='all', multiple_tables=False)[0]
    df.columns = ['name', 'old_price', 'new_price', 'discount']
    with open(TARGET_FILE, encoding='utf-8') as f:
        targets = [line.strip().lower() for line in f if line.strip()]
    mask = df['name'].str.lower().apply(
        lambda x: any(t in x for t in targets)
    )
    return df[mask][['name', 'new_price']].rename(columns={'new_price': 'price'}).to_dict('records')

def save_pdf(records):
    """Сохраняет таблицу в PDF."""
    c = canvas.Canvas(PDF_FILE, pagesize=A4)
    w, h = A4
    y = h - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, f"Цены Пятерочка {dt.date.today():%d.%m.%Y}")
    y -= 30
    c.setFont("Helvetica", 11)
    for r in records:
        if y < 50:
            c.showPage()
            y = h - 50
        c.drawString(50, y, f"{r['name'][:70]}   {r['price']:.2f} ₽")
        y -= 15
    c.save()
    print("PDF сохранён:", PDF_FILE)

if __name__ == "__main__":
    pdf = download_catalog()
    data = parse_prices(pdf)
    save_pdf(data)
