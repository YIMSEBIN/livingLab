import pandas as pd
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from address_changer.addrChanger_GPStoLAT import addrChangerToLAT
from CVRP import create_data_model, print_solution
from secrets_manager import get_secret_key
from select_oldest_waste import select_data

def main():
    API_KEY = get_secret_key()                          # 카카오 REST API 키 (유준형)
    DISTANCE_MATRIX_FILE = 'store/distance_matrix.csv'  # 거리 행렬 파일 이름
    INPUT_DATA_PATH = 'store/inputData.csv'             # input Data 파일
    TRASH_COST_PATH = 'docs/TrashCost.xlsx'             # 쓰레기 유형에 따른 비용 파일
    LATLOT_DATA_PATH = 'store/address.csv'              # 주소 위경도 파일

    input_data = select_data(INPUT_DATA_PATH, 20)
    trash_cost_data = pd.read_excel(TRASH_COST_PATH)

    # Parameter1. locations : 폐기물 주소 정보(도로명주소, 위도, 경도)
    addrChangerToLAT(INPUT_DATA_PATH, LATLOT_DATA_PATH)
    locations = pd.read_csv(f"{LATLOT_DATA_PATH}").to_dict("records")

    # Parameter2. demands : 각 폐기물의 용량
    cost_map = trash_cost_data.set_index('type')['cost'].to_dict()    # 쓰레기 유형에 따른 비용

    def calculate_total_cost(row):
        types = [typ.strip() for typ in row['trashType'].split(',')]
        counts = list(map(int, [count.strip() for count in row['count'].split(',')]))
        total_cost = sum(cost_map[typ] * count for typ, count in zip(types, counts))
        return total_cost
    
    input_data['total_cost'] = input_data.apply(calculate_total_cost, axis=1)
    demands = input_data['total_cost'].tolist()

    # Parameter3. vehicle : 폐기물 수거 차량 (용량, 수)
    vehicle = {'capacities': [500], 'count': 1} 


    """CVRP 문제 해결"""
    # 데이터 모델 초기화
    data = create_data_model(DISTANCE_MATRIX_FILE, locations, API_KEY, demands, vehicle)

    # 거리 행렬이 제대로 생성되었는지 확인
    if data["distance_matrix"] is None:
        print("거리 행렬 생성에 실패했습니다.")
        return

    # 라우팅 인덱스 매니저 생성
    manager = pywrapcp.RoutingIndexManager(len(data["distance_matrix"]), data["num_vehicles"], data["depot"])
    # 라우팅 모델 생성
    routing = pywrapcp.RoutingModel(manager)

    # 거리 계산 콜백 함수 정의 및 등록
    def distance_callback(from_index, to_index):
        """두 노드 간의 거리를 반환"""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(data["distance_matrix"][from_node][to_node])

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # 각 호(arc)의 비용 설정
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # 용량 제약 추가
    def demand_callback(from_index):
        """각 노드의 수요를 반환"""
        from_node = manager.IndexToNode(from_index)
        return data["demands"][from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # 용량 여유 없음
        data["vehicle_capacities"],  # 차량 최대 용량
        True,  # 누적값을 0에서 시작
        "Capacity",
    )

    # 첫 솔루션 탐색 전략 설정
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_parameters.time_limit.FromSeconds(30)  # 시간을 늘려 더 나은 솔루션 탐색

    # 문제 해결
    solution = routing.SolveWithParameters(search_parameters)

    # 솔루션이 있으면 출력
    if solution:
        print_solution(data, manager, routing, solution)
    else:
        print('솔루션 없음')

# 스크립트가 실행되면 main 함수를 호출
if __name__ == "__main__":
    main()
