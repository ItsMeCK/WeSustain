import face_recognition

def match_images(number, action):
    known_image = face_recognition.load_image_file(f"/workspaces/WeSustain/uploads/{number}/profile.png")
    unknown_image = face_recognition.load_image_file(f"/workspaces/WeSustain/uploads/{number}/{action}.png")

    biden_encoding = face_recognition.face_encodings(known_image)[0]
    unknown_encoding = face_recognition.face_encodings(unknown_image)[0]


    results = face_recognition.compare_faces([biden_encoding], unknown_encoding)
    return results[0]