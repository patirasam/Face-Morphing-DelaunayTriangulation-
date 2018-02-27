import cv2
import sys
import numpy as np
from delaunay_div_conq import delaunay
from feature_detector import extract_features
from vid_lib import Video

SRC_IMG = sys.argv[1]  # "donald_trump.jpg"
TARGET_IMG = sys.argv[2]  # "hillary_clinton.jpg"
VID_FILE = sys.argv[3]
# SRC_IMG = "../img_80/donald_trump.jpg"
# TARGET_IMG = "../img_80/hillary_clinton.jpg"
# VID_FILE = 'test.avi'


def apply_affine_transform(src, src_tri, target_tri, size):
    warp_mat = cv2.getAffineTransform(np.float32(src_tri), np.float32(target_tri))
    dst = cv2.warpAffine(src, warp_mat, (size[0], size[1]), None, flags=cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_REFLECT_101)
    return dst


def morph_triangle(img1, img2, img, t1, t2, t, alpha):
    r1 = cv2.boundingRect(np.float32([t1]))
    r2 = cv2.boundingRect(np.float32([t2]))
    r = cv2.boundingRect(np.float32([t]))

    t1_rect = []
    t2_rect = []
    t_rect = []

    for i in xrange(0, 3):
        t_rect.append(((t[i][0] - r[0]), (t[i][1] - r[1])))
        t1_rect.append(((t1[i][0] - r1[0]), (t1[i][1] - r1[1])))
        t2_rect.append(((t2[i][0] - r2[0]), (t2[i][1] - r2[1])))

    mask = np.zeros((r[3], r[2], 3), dtype=np.float32)
    cv2.fillConvexPoly(mask, np.int32(t_rect), (1.0, 1.0, 1.0), 16, 0)

    img1_rect = img1[r1[1]:r1[1] + r1[3], r1[0]:r1[0] + r1[2]]
    img2_rect = img2[r2[1]:r2[1] + r2[3], r2[0]:r2[0] + r2[2]]

    size = (r[2], r[3])
    warp_image1 = apply_affine_transform(img1_rect, t1_rect, t_rect, size)
    warp_image2 = apply_affine_transform(img2_rect, t2_rect, t_rect, size)

    img_rect = (1.0 - alpha) * warp_image1 + alpha * warp_image2


    img[r[1]:r[1]+r[3], r[0]:r[0]+r[2]] = img[r[1]:r[1]+r[3], r[0]:r[0]+r[2]] * (1 - mask) + img_rect * mask



def get_morph(alpha=0.5):

    weighted_pts = []
    for i in xrange(0, len(src_points)):
        x = (1 - alpha) * src_points[i][0] + alpha * target_points[i][0]
        y = (1 - alpha) * src_points[i][1] + alpha * target_points[i][1]
        weighted_pts.append((x, y))

    img_morph = np.zeros(src_img.shape, dtype=src_img.dtype)

    for triangle in del_triangles:
        x, y, z = triangle
        t1 = [src_points[x], src_points[y], src_points[z]]
        t2 = [target_points[x], target_points[y], target_points[z]]
        t = [weighted_pts[x], weighted_pts[y], weighted_pts[z]]
        morph_triangle(src_img, target_img, img_morph, t1, t2, t, alpha)

    return cv2.cvtColor(np.uint8(img_morph), cv2.COLOR_RGB2BGR)


src_img = cv2.imread(SRC_IMG)
target_img = cv2.imread(TARGET_IMG)
src_points = extract_features(SRC_IMG)
target_points = extract_features(TARGET_IMG)

avg_points = []
for i in xrange(0, len(src_points)):
    x = 0.5 * src_points[i][0] + 0.5 * target_points[i][0]
    y = 0.5 * src_points[i][1] + 0.5 * target_points[i][1]
    avg_points.append((int(x), int(y)))

del_triangles = delaunay(avg_points)

video = Video(VID_FILE, 20, 600, 800)
for percent in np.linspace(1, 0, num=200):
    print 'Writing Frame', 200 - int(percent*200) + 1
    video.write(get_morph(alpha=percent))

video.end()
