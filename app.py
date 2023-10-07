# Author: Lim Kha Shing
# Reference:
# https://face-recognition.readthedocs.io/en/latest/_modules/face_recognition/api.html#compare_faces
# https://raw.githubusercontent.com/ageitgey/face_recognition/master/examples/web_service_example.py

import os
import json
import cv2
import requests
import request_id
from flask import Flask, jsonify, request, render_template, make_response
from request_id import RequestIdMiddleware
from werkzeug.serving import make_server
from src.utils.sustanability import *

from src.OCR.crop_morphology import crop_morphology
from src.constants import ALLOWED__PICTURE_EXTENSIONS, ALLOWED_VIDEO_EXTENSIONS, frames_folder, upload_folder, \
    image_size_threshold, max_resize, source_type_image, source_type_video
from src.face_processing import compare_face

static = os.path.abspath('static')
app = Flask(__name__, static_url_path='', static_folder=static)

middleware = RequestIdMiddleware(
    app,
    format='{status} {REQUEST_METHOD:<6} {REQUEST_PATH:<60} {REQUEST_ID}',
)

def get_error_result(source_type, is_no_files):
    if is_no_files:
        result = {
            "status_code": 400,
            "error": "No " + source_type + " Found"
        }
    else:
        result = {
            "status_code": 400,
            "error": source_type + " extension is not correct"
        }
    return jsonify(result)


def create_directories():
    # Check if upload and frames folder existed or not.
    # If not then create it
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    if not os.path.exists(frames_folder):
        os.makedirs(frames_folder)

    # Get unique Request ID
    face_matching_request_id = request_id.get_request_id(request)
    print("Request ID:", face_matching_request_id)

    # create a subdirectory with unique request id inside frames and upload folder
    request_upload_folder_path = os.path.join(upload_folder, face_matching_request_id)
    request_frames_folder_path = os.path.join(frames_folder, face_matching_request_id)
    os.makedirs(request_frames_folder_path)
    os.makedirs(request_upload_folder_path)

    return request_upload_folder_path, request_frames_folder_path


def set_tolerance_and_threshold(tolerance, threshold, sharpness):
    if tolerance != '':
        tolerance = float(tolerance)
    else:
        tolerance = 0.50

    if threshold != '':
        threshold = float(threshold)
    else:
        threshold = 0.80

    if sharpness is not None and sharpness != '':
        sharpness = float(sharpness)
    else:
        sharpness = 0.60

    print("Tolerance: ", tolerance)
    print("Face match threshold: ", threshold)
    print("Sharpness threshold: ", sharpness)
    return tolerance, threshold, sharpness


def check_files_uploaded():
    if request.files['known'].filename == '':
        print("no image uploaded")
        return False, source_type_image
    if request.files['unknown'].filename == '':
        print("no video uploaded")
        return False, source_type_video
    return True, "pass"


def check_valid_files_uploaded(known, unknown):
    if not known.filename.lower().endswith(ALLOWED__PICTURE_EXTENSIONS):
        return False, source_type_image
    if not unknown.filename.lower().endswith(ALLOWED_VIDEO_EXTENSIONS):
        return False, source_type_video
    return True, "pass"


@app.route('/api/upload1', methods=['GET'])
def upload_image_video1():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if str(mode).lower() == 'subscribe' and token == 'Pushpa':
            print('WEBHOOK_VERIFIED by CK')
            return make_response(challenge, 200)
        else:
            return {"response": "forbidden"}
    return {"response": "forbidden"}

@app.route('/api/upload1', methods=['POST'])
def upload_image_video2():
    msg_req = json.loads(request.data)
    print(msg_req)
    token = 'EAAtTz8pRH9cBO5BWGnNHQLWFOOjZBotYSgCO57UcId03HyOBA30Qjn9bVlZAPLpRJTuwdZBhUoeoDkFToqOirZBILwlZA78NTAiNsZAvRbxqjJCYdcVEJGuQbPwklWil88Lsg2tiZBdFS2qbqRWdLPgkN0QBgL70Hp9OLchP7OVJ2JxIyK5dkgZCkvMTKZCLzmoimgKcQHJkEByPzVO77NHiGBpeFjIIZD'
    messaging_product = msg_req.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('messaging_product')
    phone_number_id = msg_req.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('metadata', {}).get('phone_number_id')
    name = msg_req.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('contacts', [{}])[0].get('profile', {}).get('name', '')
    from_num = msg_req.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('messages', [{}])[0].get('from')
    media_id = msg_req.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('messages', [{}])[0].get('image', {}).get('id', 'No Media')
    caption = msg_req.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('messages', [{}])[0].get('image', {}).get('caption', 'No Caption')
    text_msg = msg_req.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('messages', [{}])[0].get('text', {}).get('body', '')

    if media_id != 'No Media':
        msg_body = check_action_sequence(from_num, caption, name)
    elif "point" in text_msg.lower():
        msg_body = my_points(from_num, text_msg)
    elif "winner" in text_msg.lower():
        msg_body = get_winner(text_msg, True)
    elif "leader" in text_msg.lower():
        msg_body = leader_board(text_msg)
    else:
        msg_body = "No media received."
       
    ack_text = json.dumps({"body": f"{msg_body}"})

    # Making a POST request
    req_obj = requests.post(f'https://graph.facebook.com/v12.0/{phone_number_id}/messages?access_token={token}', data ={
        "access_token": token,
        "messaging_product": messaging_product,
        "to": from_num,
        "text": ack_text
    })

    # if req_obj.code == 200:
    # save_image(token, media_id)

    # check status code for response received
    # success code - 200
    # print(req_obj)
    # print content of request
    print(req_obj.json())
    return "200"


def save_image(token, media_id):
    # Making a POST request
    # print("============================")
    req_obj = requests.get(f'https://graph.facebook.com/v18.0/{media_id}?access_token={token}', data ={
        "access_token": token
    })

    req_obj = requests.get(f'https://lookaside.fbsbx.com/whatsapp_business/attachments/?mid=1874886782907256&ext=1696604175&hash=ATuVMLp8P7Gt6qYU_351ZEEbmGKr1R-kgxAH5QCFkXCy9A?access_token={token}', data ={
        "access_token": token
    })
    # print('Hiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii')
    # print(req_obj)
    # print('Hiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii')
    # print(req_img)
    # success code - 200
    # print(req_obj)
    # # print content of request
    print(req_obj.json())


@app.route('/api/upload', methods=['POST'])
def upload_image_video():
    # print(request.args)
    # print("Next")
    # print(request.query_string)
    # print("next")
    # print(request.data)
    # Check whether files is uploaded or not
    is_files_uploaded, source_type = check_files_uploaded()
    if not is_files_uploaded:
        if source_type == "image":
            return get_error_result("Image", True)
        else:
            return get_error_result("Video", True)

    known = request.files['known']
    unknown = request.files['unknown']

    # Check if a valid image and video file was uploaded
    is_valid_files_uploaded, source_type = check_valid_files_uploaded(known, unknown)
    if not is_valid_files_uploaded:
        if source_type == "image":
            return get_error_result("Image", True)
        else:
            return get_error_result("Video", True)

    # Flask doesn't receive any information about
    # what type the client intended each value to be.
    # So it parses all values as strings.
    # And we need to parse it manually to float and set the value
    tolerance = request.form['tolerance']
    threshold = request.form['threshold']
    sharpness = request.form.get('sharpness')
    tolerance, threshold, sharpness = set_tolerance_and_threshold(tolerance, threshold, sharpness)

    # for Unit Test to pass without running through whole face matching process
    if "testing" in request.form:
        return jsonify(result={"status_code": 200})

    # create absolutely paths for the uploaded files
    request_upload_folder_path, request_frames_folder_path = create_directories()
    unknown_filename_path = os.path.join(request_upload_folder_path, unknown.filename)
    known_filename_path = os.path.join(request_upload_folder_path, known.filename)

    # Save the uploaded files to directory
    # Example: upload/request-id/image.jpg
    unknown.save(unknown_filename_path)
    known.save(known_filename_path)
    video_path = os.path.join(request_upload_folder_path, unknown.filename)

    if known and unknown:

        # Resize the known image and scale it down
        known_image_size = os.stat(known_filename_path).st_size
        print("Image Size: ", known_image_size)
        if known_image_size > image_size_threshold:
            print("Resizing the known image as it was larger than ", image_size_threshold)
            known_image = cv2.imread(known_filename_path)
            resized_image = cv2.resize(known_image, None, fx=0.1, fy=0.1, interpolation=cv2.INTER_AREA)
            cv2.imwrite(known_filename_path, resized_image)
            print("Resized image ", os.stat(known_filename_path).st_size)

            if os.stat(known_filename_path).st_size < max_resize:
                print("Enlarge back as it smaller than ", max_resize)
                known_image = cv2.imread(known_filename_path)
                resized_image = cv2.resize(known_image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                cv2.imwrite(known_filename_path, resized_image)
                print("Resized image ", os.stat(known_filename_path).st_size)

        crop_morphology(known_filename_path)

        # process both image and video
        return compare_face(known_filename_path,
                            video_path,
                            request_upload_folder_path,
                            request_frames_folder_path,
                            tolerance=tolerance,
                            face_match_threshold=threshold,
                            sharpness_threshold=sharpness)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    # add own IPV4 address for debug
    # In android, put android:usesCleartextTraffic="true" in manifest application tag
    # for allow cross domain to LocalHost
    server = make_server('0.0.0.0', 8080, middleware)
    server.serve_forever()
