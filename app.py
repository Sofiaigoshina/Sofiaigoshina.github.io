import os
import cv2
import numpy as np
from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory, abort
from werkzeug.utils import secure_filename
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Конфигурация
UPLOAD_FOLDER = os.path.join('static', 'uploads')
FRAMES_FOLDER = os.path.join('static', 'frames')
PROCESSED_FOLDER = os.path.join('static', 'processed')
RESOURCES_FOLDER = os.path.join('Resources')
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

# Создание папок
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FRAMES_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(RESOURCES_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['FRAMES_FOLDER'] = FRAMES_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['RESOURCES_FOLDER'] = RESOURCES_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB


class SimpleObjectTracker:
    def __init__(self):
        self.object_id = 1
        self.tracks = {}

    def update(self, detections):
        if not detections:
            return self.tracks

        if not self.tracks:
            for det in detections:
                det['id'] = self.object_id
                self.tracks[self.object_id] = det
                self.object_id += 1
        else:
            # Простейший трекинг - считаем что это тот же объект
            for obj_id, track in self.tracks.items():
                for det in detections:
                    if det['class'] == track['class']:
                        det['id'] = obj_id
                        self.tracks[obj_id] = det
                        break

        return self.tracks


def load_yolo():
    try:
        net = cv2.dnn.readNetFromDarknet(
            os.path.join(app.config['RESOURCES_FOLDER'], "yolov4-tiny.cfg"),
            os.path.join(app.config['RESOURCES_FOLDER'], "yolov4-tiny.weights")
        )
        layer_names = net.getLayerNames()
        out_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

        with open(os.path.join(app.config['RESOURCES_FOLDER'], "coco.names.txt"), "r") as f:
            classes = [line.strip().lower() for line in f.readlines() if line.strip()]

        return net, out_layers, classes
    except Exception as e:
        logger.error(f"Ошибка загрузки YOLO: {str(e)}")
        raise


try:
    net, out_layers, classes = load_yolo()
    logger.info("Модель YOLO успешно загружена")
except Exception as e:
    logger.error(f"Не удалось загрузить модель YOLO: {str(e)}")
    net, out_layers, classes = None, None, []


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_frame(frame, classes_to_look_for):
    height, width = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(frame, 1 / 255, (416, 416), (0, 0, 0), swapRB=True, crop=False)
    net.setInput(blob)
    outs = net.forward(out_layers)

    detections = []
    found_objects = set()

    for out in outs:
        for obj in out:
            scores = obj[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                class_name = classes[class_id].lower()
                if class_name in classes_to_look_for:
                    center_x = int(obj[0] * width)
                    center_y = int(obj[1] * height)
                    w = int(obj[2] * width)
                    h = int(obj[3] * height)
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)

                    detections.append({
                        'class': class_name,
                        'box': [x, y, w, h],
                        'center': (center_x, center_y),
                        'confidence': float(confidence)
                    })
                    found_objects.add(class_name)

    if len(detections) > 0:
        indexes = cv2.dnn.NMSBoxes(
            [d['box'] for d in detections],
            [d['confidence'] for d in detections],
            0.5, 0.4
        )

        if len(indexes) > 0:
            indexes = indexes.flatten()
            filtered_detections = [detections[i] for i in indexes]

            for det in filtered_detections:
                x, y, w, h = det['box']
                label = f"{det['class']} {det['confidence']:.2f}"
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, label, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            return frame, filtered_detections, list(found_objects)

    return frame, [], list(found_objects)



def process_video(video_path, classes_to_look_for):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Не удалось открыть видеофайл")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    processed_name = f"processed_{timestamp}.mp4"
    processed_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_name)

    # Используем другой кодек, если OpenH264 не доступен
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(processed_path, fourcc, fps, (width, height))

    if not out.isOpened():
        cap.release()
        raise ValueError("Не удалось создать выходной видеофайл")

    tracker = SimpleObjectTracker()
    results = []
    frame_count = 0
    frame_interval = max(1, int(fps / 2))  # Используем fps, полученный из видео
    active_objects = {}

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            if frame_count % frame_interval != 0:
                continue

            timestamp_sec = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
            minutes = int(timestamp_sec // 60)
            seconds = int(timestamp_sec % 60)
            current_time = f"{minutes:02}:{seconds:02}"

            processed_frame, detections, _ = process_frame(frame.copy(), classes_to_look_for)
            tracks = tracker.update(detections)

            for object_id, track in tracks.items():
                if object_id not in active_objects:
                    frame_name = f"obj_{object_id}_{current_time.replace(':', '-')}.jpg"
                    frame_path = os.path.join(app.config['FRAMES_FOLDER'], frame_name)

                    cv2.imwrite(frame_path, cv2.resize(processed_frame, (640, int(640 * height / width))))

                    active_objects[object_id] = {
                        'class': track['class'],
                        'first_seen': current_time,
                        'last_seen': current_time,
                        'frame': frame_name
                    }
                else:
                    active_objects[object_id]['last_seen'] = current_time

            out.write(processed_frame)

    finally:
        # Фиксируем все объекты
        for object_id, data in active_objects.items():
            results.append({
                'id': object_id,
                'class': data['class'],
                'start': data['first_seen'],
                'end': data['last_seen'],
                'image': data['frame']
            })

        cap.release()
        out.release()
        cv2.destroyAllWindows()

    return results, processed_name




@app.route('/processed/<filename>')
def serve_processed(filename):
    if '..' in filename or filename.startswith('/'):
        abort(404)
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)


@app.route('/frames/<filename>')
def serve_frame(filename):
    if '..' in filename or filename.startswith('/'):
        abort(404)
    return send_from_directory(app.config['FRAMES_FOLDER'], filename)


@app.route('/', methods=['GET', 'POST'])
def index():
    if not classes:
        flash('Модель YOLO не загружена. Проверьте файлы в папке Resources.', 'error')

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Файл не выбран', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('Не выбран файл', 'error')
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash('Недопустимый формат файла. Разрешены: mp4, avi, mov, mkv', 'error')
            return redirect(request.url)

        classes_input = request.form.get('classes', '').lower()
        if not classes_input:
            flash('Укажите классы для поиска', 'error')
            return redirect(request.url)

        classes_to_look_for = {c.strip() for c in classes_input.split(',') if c.strip() in classes}
        if not classes_to_look_for:
            flash('Нет допустимых классов для поиска', 'error')
            return redirect(request.url)

        try:
            filename = secure_filename(file.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(video_path)

            results, processed_name = process_video(video_path, classes_to_look_for)

            if not results:
                flash('Объекты не найдены. Попробуйте другие классы.', 'info')
                return redirect(request.url)

            return render_template('index.html',
                                   frames=results,
                                   processed_video=processed_name,
                                   classes=classes)

        except Exception as e:
            logger.error(f"Ошибка обработки видео: {str(e)}")
            flash(f'Ошибка обработки видео: {str(e)}', 'error')
            return redirect(request.url)

    return render_template('index.html', frames=None, processed_video=None, classes=classes)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

