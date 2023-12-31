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
    # ["DAD", "ICN"],
    # ["PUS", "DAD"],
    # ["DAD", "PUS"],
]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; AS; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.37",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) OPR/77.0.4054.203",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G998U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 YaBrowser/21.6.2.855 Yowser/2.5 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
]


# html parser로 파싱한 데이터에서 정보 추출하는 함수
# 로딩이 끝나면 생기는 비동기 elem : priceGraph_summary__24ALd
# 요소의 className과 element 태그 이름을 CSS선택자로 추출
# 각 정보의 최상위 DOM element : div.indivisual_IndivisualItem__3co62 result
# 항공사이름 : <b class = "airline_name__Tm2wJ">
# 출발시간/도착시간 :  <b class = "route_time__-2Z1T"> x2
# 소요시간 : <i class = "route_info__1RhUH">의 2번째 텍스트
# 가격 : <i class = "item_num__3R0Vz">의 텍스트
def parsingFromHtml(airway_ID, flightDate, parsedHtml_li):
    parsedData_li = []
    for elem in parsedHtml_li:
        try:
            airline = elem.find("b", class_="airline_name__Tm2wJ").get_text()
            departureAndArriveTimes = elem.find_all("b", class_="route_time__-2Z1T")
            departureTime = departureAndArriveTimes[0].get_text()
            arriveTime = departureAndArriveTimes[1].get_text()
            flightTime = elem.find("i", class_="route_info__1RhUH").get_text()
            price = elem.find("i", class_="item_num__3R0Vz").get_text()
            """
            datas_li.append(
                [
                    "Flight Ticket ID",  # idx 후처리
                    "Searching Date", 
                    "Departure Date",
                    "Airway ID",
                    "Depature Time",
                    "Arrive Time",
                    "Flight Time",
                    "Airline",
                    "Price",

                ]
            )
            """
            li = [
                -1,  # 항공권 가격 정보 index는 후처리!
                searchingDate,
                flightDate[0:4] + "-" + flightDate[4:6] + "-" + flightDate[6:8],
                airway_ID,
                departureTime,
                arriveTime,
                flightTime[4:6] + ":" + flightTime[9:11],  # 소요시간 슬라이싱
                airline,
                int(price.replace(",", "")),
            ]
            parsedData_li.append(li)

        # 요소에 데이터가 없는경우 패스
        except Exception as e:
            print(e)
            pass

    return parsedData_li


# airway와 비행날짜 전체의 항공권 데이터를 조사하는 함수
def searchWithAirwayAndFlightDate(airway_ID, flightDate):
    global idx
    global currBrowser
    global browserList

    departureAirport = AIRWAYS[airway_ID][0]
    arriveAirport = AIRWAYS[airway_ID][1]

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
        currBrowser.get(url)
    except:
        print("[ERROR] getUrl failed at ", departureAirport, arriveAirport, flightDate)
        raise Exception("browser.get(url) Failed")

    # WebDriver를 이용한 비동기 html 로딩
    try:
        # 30초 이내 비동기 로딩 실패시 예외처리
        element = WebDriverWait(currBrowser, 30).until(
            EC.presence_of_element_located(
                (
                    By.CLASS_NAME,
                    "priceGraph_summary__24ALd",
                )
            )
        )

        # 카드혜택 필터 제거
        cardFilterElem = currBrowser.find_element(By.CLASS_NAME, "header_sort__1UG7V")
        cardFilterElem.click()

        cardUnSelectedElem = currBrowser.find_element(
            By.CLASS_NAME, "header_option__2G14z"
        )
        cardUnSelectedElem.click()

    except:
        # webDriver 멈춤으로 인한 timeout
        print("[ERROR] 30s timeout at ", departureAirport, arriveAirport, flightDate)
        idx = (idx + 1) % 4
        currBrowser = browserList[idx]
        time.sleep(60)
        return list([])  # 재검색????

    # bs4를 이용한 html parsing
    parsedHtml_li = BeautifulSoup(currBrowser.page_source, "html.parser").find_all(
        "div", class_="indivisual_IndivisualItem__3co62 result"
    )
    return parsingFromHtml(airway_ID, flightDate, parsedHtml_li)


def main():
    global totalFlightsCount
    global datas_li
    global startTime

    global idx
    global currBrowser
    global browserList

    totalFlightsCount = 0
    datas_li = []

    # 노선의 ID
    for airway_ID in range(4):
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=" + USER_AGENTS[0])
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-gpu")
        options.add_argument("--log-level=1")
        options.add_argument("headless")
        browser0 = webdriver.Chrome("chromedriver.exe", options=options)  # 브라우저 실행
        browser1 = webdriver.Chrome("chromedriver.exe", options=options)  # 브라우저 실행
        browser2 = webdriver.Chrome("chromedriver.exe", options=options)  # 브라우저 실행
        browser3 = webdriver.Chrome("chromedriver.exe", options=options)  # 브라우저 실행
        browserList = [browser0, browser1, browser2, browser3]
        idx = 0
        currBrowser = browserList[idx]

        currBrowser.execute_cdp_cmd("Network.enable", {})
        currBrowser.execute_cdp_cmd(
            "Network.setExtraHTTPHeaders",
            {"headers": {"User-Agent": USER_AGENTS[0]}},
        )
        time.sleep(3)  # 브라우저 열고 잠깐 기다림

        for days in range(3, 181):  # 3일뒤 항공편부터 존재(해외) 6개월까지
            if days % 19 == 0:
                print("WebDriver Reload..")
                browser0.quit()
                browser1.quit()
                browser2.quit()
                browser3.quit()
                time.sleep(3)

                options = webdriver.ChromeOptions()
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument("user-agent=" + USER_AGENTS[int(days // 19)])

                options.add_argument("--disable-web-security")
                options.add_argument("--disable-gpu")
                options.add_argument("--log-level=1")
                options.add_argument("headless")
                browser0 = webdriver.Chrome(
                    "chromedriver.exe", options=options
                )  # 브라우저 실행
                browser1 = webdriver.Chrome(
                    "chromedriver.exe", options=options
                )  # 브라우저 실행
                browser2 = webdriver.Chrome(
                    "chromedriver.exe", options=options
                )  # 브라우저 실행
                browser3 = webdriver.Chrome(
                    "chromedriver.exe", options=options
                )  # 브라우저 실행
                browserList = [browser0, browser1, browser2, browser3]
                idx = 0
                currBrowser = browserList[idx]
                time.sleep(3)

                currBrowser.execute_cdp_cmd("Network.enable", {})
                currBrowser.execute_cdp_cmd(
                    "Network.setExtraHTTPHeaders",
                    {"headers": {"User-Agent": USER_AGENTS[int(days // 19)]}},
                )
                time.sleep(2)

            departureAirPort = AIRWAYS[airway_ID][0]
            arriveAirPort = AIRWAYS[airway_ID][1]
            filghtDate = (startTime + timedelta(days=days)).strftime("%Y%m%d")

            # 해당 날짜 항공편 수집 소요 시간 검사
            before_crawl_time = datetime.today() + timedelta(hours=9)
            parsedDatas_li = searchWithAirwayAndFlightDate(airway_ID, filghtDate)
            after_crawl_time = datetime.today() + timedelta(hours=9)

            crawl_time = after_crawl_time - before_crawl_time
            print(
                f"{airway_ID}th airway about {days} days later, {departureAirPort} to {arriveAirPort} at {filghtDate} have {len(parsedDatas_li)} flights. Running Time : {crawl_time}(ms)"
            )

            totalFlightsCount += len(parsedDatas_li)

            datas_li += parsedDatas_li
        print(
            f">> {departureAirPort} to {arriveAirPort} flights : {len(parsedDatas_li)}  --TOTAL FLIGHTS : {len(datas_li)}"
        )
        print("----------------changing airway----------------------\n")
        # 브라우저 리셋 - 끄기
        browser0.quit()
        browser1.quit()
        browser2.quit()
        browser3.quit()

    # Flight Ticket ID,  후처리
    for i in range(len(datas_li)):
        datas_li[i][0] = i

    for data in datas_li:
        print(data)


# Running Time Check - Start
startTime = datetime.today() + timedelta(hours=0)

# 전역변수
searchingDate = startTime.strftime("%Y-%m-%d")

todayFileNameFormatting = startTime.strftime("%Y%m%d_%H%M%S")
print("today : ", todayFileNameFormatting)
main()
# Running Time Check - Finish
endTime = datetime.today() + timedelta(hours=0)

print(f"[Start Time] {startTime}\n")
print(f"[End Time] {endTime}\n")
print(f"[Running Time] : { endTime - startTime} (ms)\n")
print(f"[File Length] 4 airways, {len(datas_li)} rows \n\n")


# csv 생성
fd = open(f"data/{todayFileNameFormatting}.csv", "w", encoding="utf-8", newline="")
csvWriter = csv.writer(fd)
for li in datas_li:
    csvWriter.writerow(li)
fd.close()
print("[INFO]   ", todayFileNameFormatting, ".csv generated")


# log 출력
log_fd = open("timelog.txt", "a", newline="")
log_fd.write(f"[Start Time] {startTime}\n")
log_fd.write(f"[End Time] {endTime}\n")
log_fd.write(f"[Running Time] : { endTime - startTime} (ms)\n")
log_fd.write(f"[File Length] 4 airways, {len(datas_li)} rows \n\n")
log_fd.close()

print("[LOGGED] timelog.txt generated")


# 기존 csv에 추가
fd2 = open("data/flights.csv", "r", encoding="UTF-8")  # 마지막인덱스찾기
csvReader = csv.reader(fd2)
lastIdx = 0
for i in csvReader:
    lastIdx = i[0]
lastIdx = int(lastIdx)
print("lastidx : ", lastIdx)
fd2.close()
for i in range(len(datas_li)):
    datas_li[i][0] = i + lastIdx + 1

fd3 = open("data/flights.csv", "a", encoding="utf-8", newline="")
csvWriter = csv.writer(fd3)
for li in datas_li:
    csvWriter.writerow(li)
fd3.close()
print("[UPDATE] flights.csv updated")
