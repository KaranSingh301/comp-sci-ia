from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import datetime
from pymongo import MongoClient
import re
from flask import Flask, render_template, request, jsonify, session, flash
from pymongo import MongoClient
from datetime import datetime, time
import hashlib
from flask_mail import Mail, Message

tags = ['overseas', 'education', 'university', 'australia', 'uk', 'us', 'qs', 'schools', 'foundation year']

def connectToDatabase():
    client = MongoClient('mongodb+srv://singhkaran5567:biks%401209@cluster0.wq4ok.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
    db = client['comp-sci-ia']
    col = db['events']
    return col

col = connectToDatabase()

driver = webdriver.Chrome()

def scrapeEventListing(url):
    driver.get(url)
    time.sleep(2)
    
    next = driver.find_element(By.XPATH, "//*[@data-testid='page-next-wrapper']")

    while next.find_element(By.TAG_NAME, "button"):
        events = driver.find_elements(By.XPATH, "//div[@class='search-results-panel-content__events']/section/ul/li")
        for i in range(len(events)):
            try:
                details_url = driver.find_element(By.XPATH, f"//div[@class='search-results-panel-content__events']/section/ul/li[{i + 1}]//div[@class='discover-search-desktop-card discover-search-desktop-card--hiddeable']//a[@class='event-card-link ']").get_attribute("href")
                name = driver.find_element(By.XPATH, f"//div[@class='search-results-panel-content__events']/section/ul/li[{i + 1}]//div[@class='discover-search-desktop-card discover-search-desktop-card--hiddeable']//a[@class='event-card-link ']").get_attribute("aria-label")
                image_url = driver.find_element(By.XPATH, f"//div[@class='search-results-panel-content__events']/section/ul/li[{i + 1}]//div[@class='discover-search-desktop-card discover-search-desktop-card--hiddeable']//img[@class='event-card-image']").get_attribute("src")
                if any(tag in name.lower().split() for tag in tags):
                    fees = driver.find_element(By.XPATH, f"//div[@class='search-results-panel-content__events']/section/ul/li[{i + 1}]//div[@class='discover-search-desktop-card discover-search-desktop-card--hiddeable']//div[@class='DiscoverHorizontalEventCard-module__priceWrapper___3rOUY']").text.strip()
                    scrapeEventInformation(name, fees, image_url, details_url)
                driver.back()
                time.sleep(4)
            except:
                None
        next.find_element(By.TAG_NAME, "button").click()
        time.sleep(2)
        next = driver.find_element(By.XPATH, "//*[@data-testid='page-next-wrapper']")
    
    return None

def scrapeEventInformation(name, fees, image_url, details_url):
    driver.get(details_url)
    time.sleep(4)
    summary = driver.find_element(By.XPATH, "//p[@class='summary']").text.strip()
    organizer = driver.find_element(By.XPATH, "//strong[@class='organizer-listing-info-variant-b__name-link']").text.strip()
    dates = []
    try:
        driver.find_element(By.XPATH, "//ul[@class='child-event-dates-list']")
        items = driver.find_elements(By.XPATH, "//ul[@class='child-event-dates-list']/li")
        for i in range(len(items)):
            date = driver.find_element(By.XPATH, f"//ul[@class='child-event-dates-list']/li{i + 1}//button").get_attribute("aria-label").split("GMT")[0].strip()
            dates.append(date)
    except NoSuchElementException:
        date = driver.find_element(By.XPATH, "//*[@class='date-info__full-datetime']").text.split("GMT")[0].strip()
        dates.append(date)
    mode = None
    address = driver.find_element(By.XPATH, "//p[@class='location-info__address-text']").text.strip()
    if "virtual event" in address.lower():
        mode = "Virtual"
        location = None
    else:
        mode = "Face-to-Face"
        location = address.strip() + ", " + driver.find_element(By.XPATH, "//div[@class='location-info__address']").text.strip()
    fees_type = None
    if "free" in fees.lower():
        fees_type = "Free"
        price = 0
    else:
        fees_type = "Paid"
        price = float(re.findall(r'\d+\.?\d*', fees)[0].strip())
    return insertEventInDatabase(
        image_url,
        re.sub(r'^View ', '', name),
        summary,
        organizer,
        dates,
        mode,
        location,
        fees_type,
        price,
        details_url
    )
        
def insertEventInDatabase(image_url, name, summary, organizer, dates, mode, location, fees_type, price, details_url):
    for j in range(len(dates)):
        if not col.find_one({"name": name}):
            try:
                start_datetime = datetime.datetime.strptime(dates[j].split("-")[0].strip(), "%a, %d %b %Y %H:%M")
                hour, minute = map(int, dates[j].split("-")[1].strip().split(':'))
                end_time = datetime.time(hour, minute)
                end_datetime = datetime.datetime(start_datetime.year, start_datetime.month, start_datetime.day, end_time.hour, end_time.minute)
            except:
                start_datetime = datetime.datetime.strptime(dates[j].split("-")[0].strip(), "%a, %d %b %Y %I:%M %p")
                end_time = datetime.datetime.strptime(dates[j].split("-")[1].strip(), "%I:%M %p").time()
                end_datetime = datetime.datetime(start_datetime.year, start_datetime.month, start_datetime.day, end_time.hour, end_time.minute)
            destination_country = []
            if "world" in name.lower().split() or "overseas" in name.lower().split():
                destination_country = ["Asia", "Europe", "Australia", "UK", "US"]
            else:
                if "asia" in name.lower().split():
                    destination_country.append("Asia")
                if "europe" in name.lower().split():
                    destination_country.append("Europe")
                if "australia" in name.lower().split():
                    destination_country.append("Australia")
                if "uk" in name.lower().split():
                    destination_country.append("UK")
                if "us" in name.lower().split():
                    destination_country.append("US")
            if len(destination_country) == 0:
                destination_country = None
            else:
                destination_country = ", ".join(destination_country)
            col.insert_one({
                "image_url": image_url,
                "name": name,
                "summary": summary,
                "organizer": organizer,
                "mode": mode,
                "location": location,
                "fees_type": fees_type,
                "price": price,
                "details_url": details_url,
                "start_datetime": start_datetime,
                "end_datetime": end_datetime,
                "destination_country": destination_country
            })
    return None

scrapeEventListing(url="https://www.eventbrite.sg/d/singapore--singapore/overseas-education-fair/")