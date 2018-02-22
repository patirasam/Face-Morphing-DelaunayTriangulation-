import dlib
from skimage import io

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')


def extract_features(img_path):
    img = io.imread(img_path)

    # Ask the detector to find the bounding boxes of each face. The 1 in the
    # second argument indicates that we should upsample the image 1 time. This
    # will make everything bigger and allow us to detect more faces.
    dets = detector(img, 1)
    for k, d in enumerate(dets):
        shape = predictor(img, d)

    vec = [(0, 0), (0, img.shape[0]-1)]

    for j in range(0, 68):
        vec.append((shape.part(j).x, shape.part(j).y))
    vec.append((img.shape[1]-1, 0))
    vec.append((img.shape[1]-1, img.shape[0]-1))

    return vec

# extract_features('../img_80/donald_trump.jpg')
