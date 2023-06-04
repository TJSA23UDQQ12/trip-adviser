from flask import Flask, render_template, request,  jsonify
from pymongo import MongoClient, GEOSPHERE
from haversine import haversine
import pandas as pd
from flask_bootstrap import Bootstrap

app = Flask(__name__)
bootstrap = Bootstrap(app)

# MongoDB와 연결
client = MongoClient('localhost', 27017)
collection = client.place.total

data = list(collection.find())
df = pd.DataFrame(data)
df = df.sort_values(by=["score"], ascending=[False])

already = set()

def find_mainplace(start): # 두 주 목적지 출력
    tmp = pd.DataFrame()

    for idx1 in range(len(df)):
        if (idx1 not in already) and (df['종류'][idx1] == "관광지"):
            destin1 = (df['위도'][idx1], df['경도'][idx1])
            dist_d1 = haversine(destin1, start, unit='km')
            already.add(idx1)

            for idx2 in range(len(df)):
                if idx2 not in already:
                    destin2 = (df['위도'][idx2], df['경도'][idx2])
                    dist_d2 = haversine(destin2, start, unit='km')
                    between = haversine(destin2, destin1, unit='km')
                    maxdist = max(dist_d1, dist_d2)

                    if (dist_d1 < 12) and (dist_d2 < 12) and (maxdist > between) and (df['종류'][idx2] == "관광지"):
                        tmp = df.iloc[[idx1, idx2]].reset_index(drop=True)
                        already.add(idx2)
                        return tmp
    return None

def find_middle(tuple1, tuple2): #두 좌표의 중앙 출력

    latitude = (tuple1[0] + tuple2[0]) / 2
    longitude = (tuple1[1] + tuple2[1]) / 2
    result = (latitude, longitude)
    return result

def find_nearby(df, start, destin, typeof): # 출발지, 목적지 간 추천 여행지 제공
    tmp = pd.DataFrame()  # 반복문 밖에서 데이터프레임 생성
    between = haversine(start, destin, unit='km')
    # 다음 이동경로 간의 거리가 2km 보다 작으면 반경 3km 내에서 목적지 검색
    # 그렇지 않으면 두 목적지 간의 거리를 지름으로 하는 원을 반경으로 하여 검색
    search_range = 2 if between < 2 else between/2
    coord = find_middle(start, destin)

    for idx in range(len(df)):
        spot = (df['위도'][idx], df['경도'][idx])
        # 출발지와 목적지 중앙에서 search_range 범위 내인, 특정 종류의, 이미 갔던 루트가 아닌 위치 찾기
        if (haversine(coord, spot, unit='km') < search_range) and (df['종류'][idx] in typeof) and (idx not in already):
            # 찾으면, 간 목적지로 추가.
            already.add(idx)
            tmp = df.iloc[idx].reset_index(drop=True)
            return tmp
    return None

def findone_nearby(loc, distance, typeof):
    tmp = pd.DataFrame()  # 반복문 밖에서 데이터프레임 생성

    for idx in range(len(df)):
        spot = (df['위도'][idx], df['경도'][idx])
        if (haversine(loc, spot, unit='km') < distance) and (df['종류'][idx] == typeof) and (idx not in already):
            already.add(idx)
            tmp = df.iloc[idx].reset_index(drop=True)
            return tmp
    return None

def route_print(start): #총 여행일정 출력

    main = find_mainplace(start)
    main1_coord = (main['위도'][0], main['경도'][0])
    main2_coord = (main['위도'][1], main['경도'][1])

    breakfast = findone_nearby(start, 2, "식당")

    lunch = findone_nearby(main1_coord, 2, "식당")
    lunch_coord = (lunch[5], lunch[4])

    dinner = findone_nearby(main2_coord, 2, "식당")
    dinner_coord = (dinner[5], dinner[4])

    subplace = find_nearby(df, dinner_coord, start, ["관광지", "카페"])

    mainplace1 = main.iloc[0]
    mainplace1 = mainplace1.rename({'상호명': 1, '주소': 2, '종류': 3, '위도': 5, '경도': 4, 'score': 6})
    mainplace2 = main.iloc[1]
    mainplace2 = mainplace2.rename({'상호명': 1, '주소': 2, '종류': 3, '위도': 5, '경도': 4, 'score': 6})

    route = pd.concat([breakfast, mainplace1, lunch,  mainplace2, dinner, subplace], axis=1)

    route = route.T
    route = route.reset_index(drop=True)
    route.rename(columns ={0: 'ID', 1: '상호명', 2: '주소', 3: '종류', 4: '경도', 5: '위도', 6: '점수', 7: 'NAN'}, inplace=True)

    print(route)

    return route


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save', methods=('GET', 'POST'))
def results():
    return render_template('FORSAVE.html')

@app.route('/kakaomap')
def kakao():
    latitude = float(request.args.get('latitude'))
    longitude = float(request.args.get('longitude'))
    start = (latitude, longitude)
    df = find_mainplace(start)

    return render_template('kakaomap.html', latitude=latitude, longitude=longitude, df=df)

@app.route('/juso')
def juso():
    return render_template('juso.html')

@app.route('/practice')
def prac():
    latitude = float(request.args.get('latitude'))
    longitude = float(request.args.get('longitude'))
    start = (latitude, longitude)
    df = route_print(start)

    # 데이터 프레임을 레코드 리스트로 변환
    records = df.to_dict('records')
    print(records)
    return render_template('practice.html', latitude=latitude, longitude=longitude, records=records)

if __name__ == '__main__':
    app.run(debug=True, port=5000)


