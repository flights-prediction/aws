import csv
# first_data = [[]] : 원본데이터id, 조사날짜, 예측가격, 힝공편id(fk)
# 첫 번째 CSV 파일 읽기 : 크롤링 원본 데이터
with open("data/flights.csv", 'r', newline='', encoding='utf-8') as first_file:
    first_reader = csv.reader(first_file)
    first_data = list(first_reader)
    print(len(first_data))

# 두 번째 CSV 파일 읽기 : 항공편 테이블 csv 변환 데이터
with open('flight_info_0430.csv', 'r', newline='', encoding='utf-8') as second_file:
    second_reader = csv.reader(second_file)
    second_data = list(second_reader)
    print(len(second_data))

cnt=0
# tmp=0

# 첫 번째 CSV 파일의 각 행을 반복하여 작업 수행
for first_row in first_data:
    # 첫 번째 CSV 파일의 각 행에서 필요한 열 추출
    
    columns_to_compare = [first_row[i] for i in [2,3,4,5,7]]
    
    
    # 두 번째 CSV 파일의 각 행을 반복하여 비교
    for second_row in second_data:
        # 두 번째 CSV 파일의 각 행에서 필요한 열 추출
        columns_to_match = [second_row[i] for i in [3,5,4,2,1]]
        
        # if tmp <=10 :
        #     print(columns_to_compare)
        #     print(columns_to_match)
        #     print()
        #     tmp+=1
        

        # 두 번째 파일의 열 값이 첫 번째 파일의 값과 일치하는지 확인하고, 일치하는 경우 처리
        if columns_to_compare[:] == columns_to_match[:]:
            # 첫 번째 파일의 10번째 열에 두 번째 파일의 0번째 열 값을 추가
            first_row.pop(7)
            first_row.pop(6)
            first_row.pop(5)
            first_row.pop(4)
            first_row.pop(3)
            first_row.pop(2)
            
            # first_row = [first_row[i] for i in [0,1,6,8]]
            first_row.append(second_row[0])
            if cnt % 10000 ==0 :
                print("@",cnt)
            cnt+=1
            break  # 매칭된 경우에는 더 이상의 비교는 불필요하므로 반복문 종료

# 결과를 출력하거나 다른 작업을 수행할 수 있음
# 예를 들어, 수정된 데이터를 새로운 CSV 파일에 저장할 수 있음

# 수정된 데이터 출력
# for row in first_data:
#     print(row)

# 수정된 데이터를 새로운 CSV 파일에 저장
with open('modified_first_file.csv', 'w', newline='', encoding='utf-8') as modified_file:
    writer = csv.writer(modified_file)
    writer.writerows(first_data)
