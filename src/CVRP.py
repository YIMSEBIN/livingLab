import requests
import os
import csv

# 거리 행렬 생성 함수
def create_distance_matrix(API_KEY, locations):
    """카카오 지도 API를 사용하여 거리 행렬을 생성합니다."""
    distance_matrix = []

    headers = {
        'Authorization': f'KakaoAK {API_KEY}',
    }

    for i, origin in enumerate(locations):
        distance_row = []
        origin_coords = f"{origin['Longitude']},{origin['Latitude']}"
        for j, destination in enumerate(locations):
            if i == j:
                # 동일한 노드의 거리는 0으로 설정
                distance_row.append(0)
            else:
                destination_coords = f"{destination['Longitude']},{destination['Latitude']}"
                url = f"https://apis-navi.kakaomobility.com/v1/directions?origin={origin_coords}&destination={destination_coords}&priority=RECOMMEND"
                response = requests.get(url, headers=headers)
                result = response.json()

                # 응답에서 거리 값 추출
                if response.status_code == 200:
                    try:
                        distance = result['routes'][0]['summary']['distance']  # 거리(meter)
                        distance_row.append(distance)
                    except (KeyError, IndexError):
                        # 경로를 찾을 수 없는 경우 큰 값으로 설정
                        distance_row.append(float('inf'))
                else:
                    print(f"API 요청 오류: {response.status_code}")
                    return None
        distance_matrix.append(distance_row)

    return distance_matrix

# 거리 행렬 저장 함수
def save_distance_matrix(distance_matrix, filename):
    """거리 행렬을 CSV 파일로 저장합니다."""
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for row in distance_matrix:
            writer.writerow(row)

# 거리 행렬 로드 함수
def load_distance_matrix(filename):
    """CSV 파일에서 거리 행렬을 로드합니다."""
    distance_matrix = []
    with open(filename, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            # 문자열로 읽혀진 값을 숫자로 변환
            distance_row = []
            for value in row:
                if value == 'inf':
                    distance_row.append(float('inf'))
                else:
                    distance_row.append(float(value))
            distance_matrix.append(distance_row)
    return distance_matrix

# 데이터 모델 생성 함수
def create_data_model(DISTANCE_MATRIX_FILE, locations, API_KEY, demands, vehicle):
    """문제에 필요한 데이터를 저장"""
    data = {}
    
    # 거리 행렬 파일이 존재하면 로드하고, 크기를 확인
    if os.path.exists(DISTANCE_MATRIX_FILE):
        print("저장된 거리 행렬을 로드합니다...")
        saved_distance_matrix = load_distance_matrix(DISTANCE_MATRIX_FILE)
        if len(saved_distance_matrix) == len(locations) and all(len(row) == len(locations) for row in saved_distance_matrix):
            print("저장된 거리 행렬을 사용합니다...")
            data["distance_matrix"] = saved_distance_matrix
        else:
            print("거리 행렬의 크기가 현재의 위치 목록과 일치하지 않습니다. 거리 행렬을 다시 생성합니다...")
            data["distance_matrix"] = create_distance_matrix(API_KEY, locations)
            if data["distance_matrix"] is None:
                print("거리 행렬 생성에 실패했습니다.")
                exit(1)
            else:
                # 거리 행렬을 파일로 저장
                save_distance_matrix(data["distance_matrix"], DISTANCE_MATRIX_FILE)
                print(f"거리 행렬을 '{DISTANCE_MATRIX_FILE}' 파일로 저장했습니다.")
    else:
        print("거리 행렬을 생성합니다...")
        data["distance_matrix"] = create_distance_matrix(locations)
        if data["distance_matrix"] is None:
            print("거리 행렬 생성에 실패했습니다.")
            exit(1)
        else:
            # 거리 행렬을 파일로 저장
            save_distance_matrix(data["distance_matrix"], DISTANCE_MATRIX_FILE)
            print(f"거리 행렬을 '{DISTANCE_MATRIX_FILE}' 파일로 저장했습니다.")
    
    data["demands"] = demands                       # 각 노드(고객)의 수요 : demands 리스트
    data["vehicle_capacities"] = vehicle['capacities'] # 각 차량의 용량
    data["num_vehicles"] = vehicle['count']            # 차량 수
    data["depot"] = 0                               # 출발점 (디포)

    return data


# 솔루션을 출력하는 함수
def print_solution(data, manager, routing, solution):
    """해결된 경로를 콘솔에 출력"""
    print(f"Objective: {solution.ObjectiveValue()}")
    total_distance = 0
    total_load = 0

    # 각 차량에 대해 경로 출력
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        plan_output = f"Vehicle {vehicle_id}의 경로:\n"
        route_distance = 0
        route_load = 0

        # 경로의 각 노드(고객)에 대해 반복
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_load += data["demands"][node_index]
            plan_output += f" {node_index} Load({route_load}) -> "
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            if routing.GetArcCostForVehicle(previous_index, index, vehicle_id) is not None:
                route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)

        plan_output += f" {manager.IndexToNode(index)} Load({route_load})\n"
        plan_output += f"경로 거리: {route_distance}m\n"
        plan_output += f"경로 적재량: {route_load}\n"
        print(plan_output)
        total_distance += route_distance
        total_load += route_load

    # 전체 경로 거리와 적재량 출력
    print(f"모든 경로의 총 거리: {total_distance}m")
    print(f"모든 경로의 총 적재량: {total_load}")
