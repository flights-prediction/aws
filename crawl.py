import csv
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver  # 외부
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

from datetime import datetime, timedelta
import time

import asyncio  # 외부
import logging  # 미사용?


# 다낭으로 향하는 4개 노선
AIRWAYS = [
    ["ICN", "DAD"],
    ["DAD", "ICN"],
    ["PUS", "DAD"],
    ["DAD", "PUS"],
]


def parsingFromHtml(airway_ID, flightDate, crawledHtml_li):
    # 로딩이 끝나면 생기는 비동기 elem : div.flights List domestic_DomesticFlight__3wvCd
    # 요소의 className -> CSS선택자로 추출
    # 전체 : div.indivisual_IndivisualItem__3co62 result
    # 항공사 : b.name -> CSS
    # 출발시간/도착시간 : route_time__-2Z1T[2]
    # 소요시간 : route_info__1RhUH 의 2번째 텍스트
    # 카드 혜택 : item_type__2KJOZ
    # 가격 : item_num__3R0Vz
    parsed_li = []
    for elem in crawledHtml_li:
        try:
            airline = elem.find("b", class_="airline_name__Tm2wJ").get_text()
            departureAndArriveTimes = elem.find_all("b", class_="route_time__-2Z1T")
            departureTime = departureAndArriveTimes[0].get_text()
            arriveTime = departureAndArriveTimes[1].get_text()
            flightTime = elem.find("i", class_="route_info__1RhUH").get_text()
            # card_benefit = elem.find("span", class_="item_type__2KJOZ").get_text()
            price = elem.find("i", class_="item_num__3R0Vz").get_text()
            """
            datas_li.append(
                [
                    "Flight Ticket ID",  # idx 후처리
                    "Searching Date",  # 조사날짜 후처 리 
                    "Departure Date",
                    "Airway ID",
                    "Depature Time",
                    "Arrive Time",
                    "Flight Time",
                    "Airline",
                    "Price",
                    "Card Benefit",
                ]
            )
            """
            li = [
                1,
                1,
                flightDate[0:4] + "-" + flightDate[4:6] + "-" + flightDate[6:8],
                airway_ID,
                departureTime,
                arriveTime,
                flightTime[4:6] + ":" + flightTime[9:11],  # 소요시간 슬라이싱
                airline,
                int(price.replace(",", "")),
                # card_benefit[3:],
            ]
            parsed_li.append(li)

        # 요소에 데이터가 없는경우 패스
        except Exception as e:
            print(e)
            pass

    return parsed_li


def searchWithAirwayAndFlightDate(airway_ID, flightDate):
    global countingURL
    global browser

    departureAirport = AIRWAYS[airway_ID][0]
    arriveAirport = AIRWAYS[airway_ID][1]

    countingURL += 1
    url = (
        "https://m-flight.naver.com/flights/international/"
        + departureAirport
        + "-"
        + arriveAirport
        + "-"
        + flightDate
        + "?adult=1&isDirect=true&fareType=Y"
    )
    # WebDriver에 Get요청 실패시 예외처리
    try:
        browser.get(url)
    except:
        print("[ERROR] getUrl failed at ", departureAirport, arriveAirport, flightDate)
        raise Exception("browser.get(url) Failed")

    # WebDriver를 이용한 비동기 html 로딩
    try:
        # 15초 이내 비동기 로딩 실패시 예외처리
        element = WebDriverWait(browser, 20).until(
            EC.presence_of_element_located(
                (
                    By.CLASS_NAME,
                    "priceGraph_summary__24ALd",
                )
            )
        )
    except:
        # webDriver 멈춤으로 인한 timeout
        print("[ERROR] 20s timeout at ", departure, arrive, date)
        print("[SYS] switching chrome browser to idx : ", idx)

        return list([])  # 재검색

    # bs4를 이용한 parsing

    soup = BeautifulSoup(browser.page_source, "html.parser")
    crawledHtml_li = soup.find_all(
        "div", class_="indivisual_IndivisualItem__3co62 result"
    )
    parsedHtml_li = parsingFromHtml(airway_ID, flightDate, crawledHtml_li)  # bs4

    return parsedHtml_li


def main():
    global countingURL
    global datas_li
    global startTime

    global browser

    countingURL = 0
    datas_li = []

    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    browser = webdriver.Chrome("chromedriver.exe")  # 브라우저 실행S

    # 노선의 ID
    for airway_ID in range(4):
        routeTotalFlights = 0

        time.sleep(3)  # 브라우저 열고 잠깐 기다림

        for days in range(3, 5):  # 3일뒤 항공편부터 존재(해외) 6개월까지
            # 90번마다 브라우저 리셋?

            departureAirPort = AIRWAYS[airway_ID][0]
            arriveAirPort = AIRWAYS[airway_ID][1]
            filghtDate = (startTime + timedelta(days=days)).strftime("%Y%m%d")

            # 해당 날짜 항공편 수집 소요 시간 검사
            before_crawl_time = datetime.today() + timedelta(hours=9)
            parsed_li = searchWithAirwayAndFlightDate(airway_ID, filghtDate)
            after_crawl_time = datetime.today() + timedelta(hours=9)

            crawl_time = after_crawl_time - before_crawl_time
            print(
                f"{airway_ID}-at {days} days later,       {departureAirPort} to {arriveAirPort} at {filghtDate} have {len(parsed_li)} flights. Running Time : {crawl_time}(ms)"
            )

            routeTotalFlights += len(parsed_li)

            datas_li += parsed_li
        print(
            f">> {departureAirPort} to {arriveAirPort} flights : {routeTotalFlights}  --TOTAL FLIGHTS : {len(datas_li)}"
        )
        print("----------------changing airway----------------------\n")

    browser.quit()

    # Flight Ticket ID, searchingDate 후처리
    for i in range(len(datas_li)):
        datas_li[i][0] = i
        datas_li[i][1] = startTime.strftime("%Y-%m-%d")


# Running Time Check - Start
startTime = datetime.today() + timedelta(hours=0)

todayFileNameFormatting = startTime.strftime("%Y%m%d_%H%M%S")
print("today : ", todayFileNameFormatting)
main()
# Running Time Check - Finish
endTime = datetime.today() + timedelta(hours=0)

print(f"[Start Time] {startTime}\n")
print(f"[End Time] {endTime}\n")
print(f"[Running Time] : { endTime - startTime} (ms)\n")
print(f"[File Length] {countingURL} url, {len(datas_li)} rows \n\n")

exit(0)

# csv 출력
fd = open(
    f"crawledFiles/{todayFileNameFormatting}.csv", "w", encoding="utf-8", newline=""
)
csvWriter = csv.writer(fd)
for li in datas_li:
    csvWriter.writerow(li)
fd.close()
print("[INFO]   ", todayFileNameFormatting, ".csv generated")


# log 출력
log_fd = open("crawledFiles/timelog.txt", "a", newline="")
log_fd.write(f"[Start Time] {startTime}\n")
log_fd.write(f"[End Time] {endTime}\n")
log_fd.write(f"[Running Time] : { endTime - startTime} (ms)\n")
log_fd.write(f"[File Length] {countingURL} url, {len(datas_li)} rows \n\n")
log_fd.close()

print("[LOGGED] timelog.txt generated")


# 기존 csv에 추가

fd2 = open("crawledFiles/flights.csv", "r", encoding="UTF-8")  # 마지막인덱스찾기
csvReader = csv.reader(fd2)
lastIdx = 1
for i in csvReader:
    lastIdx = i[0]
lastIdx = int(lastIdx)
print("lastidx : ", lastIdx)
fd2.close()
for i in range(len(datas_li)):
    datas_li[i][0] = i + lastIdx + 1

fd3 = open("crawledFiles/flights.csv", "a", encoding="utf-8", newline="")
csvWriter = csv.writer(fd3)
for li in datas_li:
    csvWriter.writerow(li)
fd3.close()
print("[UPDATE] flights.csv updated")
