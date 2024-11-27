from ultralytics import YOLO
import cv2
import matplotlib.pyplot as plt

def model_load(): # 모델 가져오기
    model =  YOLO('best.pt')    #best.pt가 최종 모델(yolov8 파인튜닝함)
    
    return model

def image_preprocess(image_path): #이미지 전처리
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # OpenCV는 기본적으로 BGR로 이미지를 읽기 때문에 RGB로 변환
    
def image_predict(image, model, confidence=0.25):  # !default confidence은 추후 회의 필요
    # YOLOv5로 이미지에 object detection 수행
    result = model.predict(source=image, confidence= confidence)
    
    return result   

def image_visualize(): # 모델 추론 결과 이미지로 저장하고 출력
    return 


# # 결과 확인
# for result in results:
#     boxes = result.boxes.xyxy  # Bounding box 좌표 (xmin, ymin, xmax, ymax)
#     confidences = result.boxes.conf  # Confidence score
#     classes = result.boxes.cls  # 클래스 ID

#     # 결과 출력
#     for box, confidence, cls in zip(boxes, confidences, classes):
#         print(f"Class: {int(cls)}, Confidence: {confidence:.2f}, Box: {box.numpy()}")

# # 예측된 이미지 시각화
# annotated_image = results[0].plot()
# plt.imshow(annotated_image)
# plt.axis('off')
# plt.show()
