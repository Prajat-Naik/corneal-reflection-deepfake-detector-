import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import math
from skimage.metrics import structural_similarity as compare_ssim
import statistics
import heapq
import skimage.filters as filter
from skimage.filters import threshold_otsu, threshold_mean, thresholding

from skimage import feature
import joblib

def compute_lbp_feature(image, radius=3, n_points=24):
    """
    Compute Local Binary Pattern (LBP) histogram for texture classification.
    """
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Uniform LBP is rotation invariant and robust
    try:
        lbp = feature.local_binary_pattern(gray, n_points, radius, method="uniform")
        
        # Calculate histogram
        (hist, _) = np.histogram(lbp.ravel(), bins=np.arange(0, n_points + 3), range=(0, n_points + 2))

        # Normalize the histogram
        hist = hist.astype("float")
        hist /= (hist.sum() + 1e-7)
        return hist
    except Exception as e:
        print(f"LBP Error: {e}")
        return np.zeros(n_points + 2)

def analyze_face_texture(img, face_landmarks=None, model=None):
    """
    Analyze the texture of the face to detect smoothness (common in GANs).
    Returns a score between 0.0 (Fake/Smooth) and 1.0 (Real/Textured).
    """
    try:
        # 1. Prediction using SVM Model (if available)
        if model:
             # Resize to valid size if needed (SVM trained on 512x512 usually, but LBP is robust to size if texture is consistent)
             # Better to resize to match training consistency
             img_resized = cv2.resize(img, (512, 512))
             hist = compute_lbp_feature(img_resized)
             hist = hist.reshape(1, -1)
             
             # predict_proba returns [[prob_class_0, prob_class_1]]
             # We want Class 1 (Real)
             probs = model.predict_proba(hist)[0]
             score = probs[1] # Probability of being Real
             
             # Variance for logging
             gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
             variance = cv2.Laplacian(gray, cv2.CV_64F).var()
             
             return score, variance

        # 2. Fallback to Variance Logic
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Enforce distinct ranges for FAKE and REAL
        # FAKE range: [0.0, 0.4]
        # REAL range: [0.6, 1.0]
        # (0.4 to 0.6 is a gap to ensure distinction)

        # Base threshold for variance based on empirical logs
        # Fake images typically have very low variance, but some outliers hit ~230
        # Map variance up to 250 strictly into the [0.0, 0.6] range
        variance_threshold_low = 250
        variance_threshold_high = 600
        
        if variance < variance_threshold_low:
             # Map variance [0, 250) to score [0.0, 0.6] based on user request
             score = (variance / 250.0) * 0.6
        elif variance > variance_threshold_high:
             # Cap score at 1.0 for very high variance
             score = 1.0
        else:
             # Map variance [250, 600] to score [0.6, 1.0]
             score = 0.6 + ((variance - 250.0) / (600.0 - 250.0)) * 0.4
             
        return score, variance
    except Exception as e:
        print(f"Texture analysis failed: {e}")
        return 0.5, 0.0 # Return neutral score on failure


# def alignImages(im1, im2, mask_left_img, MAX_FEATURES = 50000, GOOD_MATCH_PERCENT = 1):
#     # Convert images to grayscale
#     im1Gray = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)
#     im2Gray = cv2.cvtColor(im2, cv2.COLOR_BGR2GRAY)
#
#     # Detect ORB features and compute descriptors.
#     orb = cv2.ORB_create(MAX_FEATURES)
#     # orb = cv2.ORB_create()
#     keypoints1, descriptors1 = orb.detectAndCompute(im1Gray, None)
#     keypoints2, descriptors2 = orb.detectAndCompute(im2Gray, None)
#
#     # Match features.
#     matcher = cv2.DescriptorMatcher_create(cv2.DESCRIPTOR_MATCHER_BRUTEFORCE_HAMMING)
#     # matcher = cv2.DescriptorMatcher_create(cv2.NORM_L2)
#     matches = matcher.match(descriptors1, descriptors2, None)
#
#     # Sort matches by score
#     matches.sort(key=lambda x: x.distance, reverse=False)
#
#     # Remove not so good matches
#     numGoodMatches = int(len(matches) * GOOD_MATCH_PERCENT)
#     matches = matches[:numGoodMatches]
#
#     # Draw top matches
#     imMatches = cv2.drawMatches(im1, keypoints1, im2, keypoints2, matches, None)
#     # cv2.imwrite("matches.jpg", imMatches)
#
#     # Extract location of good matches
#     points1 = np.zeros((len(matches), 2), dtype=np.float32)
#     points2 = np.zeros((len(matches), 2), dtype=np.float32)
#
#     for i, match in enumerate(matches):
#         points1[i, :] = keypoints1[match.queryIdx].pt
#         points2[i, :] = keypoints2[match.trainIdx].pt
#
#     # Find homography
#     h, mask = cv2.estimateAffinePartial2D(points1, points2, method = cv2.RANSAC) ####2D
#     # h, mask = cv2.estimateAffine2D(points1, points2, method=cv2.RANSAC)  ####2D
#     # h, mask = cv2.findHomography(points1, points2, cv2.RANSAC)#####3D
#
#     # Use homography
#     h= np.float64([[1,0,h[0][2]],[0,1,h[1][2]]])
#     height, width, channels = im2.shape
#     im1Reg =cv2.warpAffine(im1, h, (width, height))#####2D
#     # im1Reg = cv2.warpPerspective(im1, h, (width, height))######3D
#     im1Reg_mask = cv2.warpAffine(mask_left_img, h, (width, height))
#     return im1Reg, h, im1Reg_mask

def matrix_reduce(iris_left_matrix, iris_right_matrix):
    """
    Shrink iris.
    [reduced_iris_left_matrix, reduced_iris_right_matrix] = matrix_reduce(iris_left_matrix, iris_right_matrix)

    Parameters
    ----------
    iris_left_matrix: list
        The mask of the left iris (boolean).
    iris_right_matrix: list
        The mask of the right iris (boolean).

    Returns
    -------
    reduced_iris_left_matrix: list
        The shrinking mask of the left iris (boolean).
    reduced_iris_right_matrix: list
        The shrinking mask of the right iris (boolean).
    """
    reduced_iris_left_matrix = np.zeros((iris_left_matrix.shape[0], iris_left_matrix.shape[1]), dtype=int)
    reduced_iris_right_matrix = np.zeros((iris_right_matrix.shape[0], iris_right_matrix.shape[1]), dtype=int)

    rows, cols = iris_left_matrix.shape
    for i in range(rows):
        for j in range(cols):
            if iris_left_matrix[i][j]==1:
                # Check neighbors with bounds
                # (i>0 and [i-1]) or (i<rows-1 and [i+1]) ...
                # Actually logic is: if ANY neighbor is 0, set to 0.
                # If neighbor is out of bounds, treat as 0 (boundary is edge).
                
                is_boundary = False
                if i == 0 or i == rows - 1 or j == 0 or j == cols - 1:
                     is_boundary = True
                elif iris_left_matrix[i-1][j]==0 or \
                     iris_left_matrix[i+1][j]==0 or \
                     iris_left_matrix[i][j-1] == 0 or \
                     iris_left_matrix[i][j+1] == 0:
                     is_boundary = True
                
                if is_boundary:
                    reduced_iris_left_matrix[i][j] = 0
                else:
                    reduced_iris_left_matrix[i][j] = 1
            else:
                reduced_iris_left_matrix[i][j] = 0

    rows, cols = iris_right_matrix.shape
    for i in range(rows):
        for j in range(cols):
            if iris_right_matrix[i][j]==1:
                is_boundary = False
                if i == 0 or i == rows - 1 or j == 0 or j == cols - 1:
                     is_boundary = True
                elif iris_right_matrix[i-1][j]==0 or \
                     iris_right_matrix[i+1][j]==0 or \
                     iris_right_matrix[i][j-1] == 0 or \
                     iris_right_matrix[i][j+1] == 0:
                     is_boundary = True
                
                if is_boundary:
                    reduced_iris_right_matrix[i][j] = 0
                else:
                    reduced_iris_right_matrix[i][j] = 1
            else:
                reduced_iris_right_matrix[i][j] = 0

    return reduced_iris_left_matrix, reduced_iris_right_matrix

def shiftbits(template, noshifts, matrix=False):
    """
    Shift the bit-wise highlight patterns.
    [templatenew] = shiftbits(template, noshifts, matrix=False)

    Parameters
    ----------
    template: list
        The mask of the highlights (boolean).
    noshifts: int
        The step size and direction of moving.
    matrix: bool
        Fill the empty item in the mask or not

    Returns
    -------
    templatenew: list
        The shifting mask of the highlights (boolean).
    """
    templatenew = np.zeros(template.shape)
    width = template.shape[1]
    s = np.abs(noshifts)
    if s >= width:
         return np.zeros(template.shape)
    p = width - s

    if noshifts == 0:
        templatenew = template

    elif noshifts < 0:
        x = np.arange(p)
        templatenew[:, x] = template[:, s + x]
        x = np.arange(p, width)
        if matrix:
            templatenew[:, x] = 0
        else:
            templatenew[:, x] = template[:, x - p]

    else:
        x = np.arange(s, width)
        templatenew[:, x] = template[:, x - s]
        x = np.arange(s)
        if matrix:
            templatenew[:, x] = 0
        else:
            templatenew[:, x] = template[:, p + x]

    return templatenew

# def calculate_overlap(left_matrix,right_matrix):
#     sum = 0
#     for i in range(left_matrix.shape[0]):
#         for j in range(left_matrix.shape[1]):
#             if left_matrix[i][j]==1 and right_matrix[i][j]==1:
#                 sum=sum+1
#     return sum


def shift(img_left_matrix, img_right_matrix, negative_lr_shift, positive_lr_shift,negative_ud_shift, positive_ud_shift):
    """
    Move the mask of the left highlights up, down, left, and right to maximize the overlap with the mask of the right highlights to get the best IOU score.
    [opt_img_left_shift, max_overlap, opt_shift, IOU_score]
    = shift(img_left_matrix, img_right_matrix, negative_lr_shift, positive_lr_shift,negative_ud_shift, positive_ud_shift)

    Parameters
    ----------
    img_left_matrix: list
        The mask of the left highlights (boolean).
    img_right_matrix: list
        The mask of the right highlights (boolean).
    negative_lr_shift: int
        The maximum step size of moving left
    positive_lr_shift: int
        The maximum step size of moving right
    negative_ud_shift: int
        The maximum step size of moving up
    positive_ud_shift: int
        The maximum step size of moving down

    Returns
    -------
    opt_img_left_shift: list
        The optimal mask of the left highlights after moving.
    max_overlap: int
        The maximum number of overlapped pixels.
    opt_shift: int
        The optimal steps of moving
    IOU_score: float
        The best IoU score.
    """
    max_overlap = -math.inf
    IOU_score = 0
    opt_shift = [0, 0]
    opt_img_left_shift = img_left_matrix
    for shifts_lr in range(negative_lr_shift, positive_lr_shift):
        for shift_ud in range(negative_ud_shift, positive_ud_shift):
            img_left_ud_shift = shiftbits(img_left_matrix, shift_ud, matrix =True)
            img_left_lr_shift = np.transpose(shiftbits(np.transpose(img_left_ud_shift), shifts_lr, matrix =True))
            m = np.sum(np.logical_and(img_left_lr_shift, img_right_matrix).astype(int))
            union_individual = np.sum(np.logical_or(img_left_lr_shift, img_right_matrix).astype(int))
            if m>=max_overlap:
                max_overlap = m
                if union_individual == 0:
                    IOU_score = 0
                else:
                    IOU_score = m / union_individual
                opt_shift = [shift_ud, shifts_lr]
                opt_img_left_shift = img_left_lr_shift
    return opt_img_left_shift, max_overlap, opt_shift, IOU_score

def process_aligned_image(iris_left, iris_right, iris_left_matrix, iris_right_matrix, l_highlights, r_highlights,
                          left_eye_image,right_eye_image, double_eye_img, double_eye_position_difference_list,
                          reduce = True, reduce_size = 2, threshold_scale_left =1, threshold_scale_right =1):
    """
    Crop highlights from the left and right iris.
    [iris_left, iris_right, left_recolor, right_recolor, left_recolor_resize, right_recolor_resize, IOU_score, double_eye_img_modified]
    = process_aligned_image(iris_left, iris_right, iris_left_matrix, iris_right_matrix, l_highlights, r_highlights,
                          left_eye_image,right_eye_image, double_eye_img, double_eye_position_difference_list,
                          reduce, reduce_size, threshold_scale_left, threshold_scale_right)

    Parameters
    ----------
    iris_left: list
        The image of the left iris (the background is white).
    iris_right: list
        The image of the right iris (the background is white).
    iris_left_matrix: list
        The mask of the left iris (boolean).
    iris_right_matrix: list
        The mask of the right iris (boolean).
    l_highlights: list
        The mask of the left highlights (boolean).
    r_highlights: list
        The mask of the right highlights (boolean).
    left_eye_image: list
        The features of the left eye.
    right_eye_image: list
        The features of the right eye.
    double_eye_img: list
        Consecutive double eyes area features taken from the face.
    double_eye_position_difference_list: ndarray
        The distance between new_eyes_position_list and double_eye_list.
    reduce: boolean
        Shrink iris or not.
    reduce_size: int
        The step size to shrink from the edge to the inside.
    threshold_scale_left: float
        Set a scale to increase or decrease the threshold for the left iris.
    threshold_scale_right: float
        Set a scale to increase or decrease the threshold for the right iris.

    Returns
    -------
    iris_left: list
        Resized image of the left iris.
    iris_right: int
        Resized image of the right iris.
    left_recolor: list
        Only show highlights (black color) in the left iris with the white background.
    right_recolor: int
        Only show highlights (black color) in the right iris with the white background.
    left_recolor_resize: list
        Resize the left iris image and show highlights with green color.
    right_recolor_resize: int
        Resize the right iris image and show highlights with red color.
    IOU_score: float
        Calculate IoU score based on the overlap of left highlights and right highlights.
    double_eye_img_modified: int
        Show highlights (green color in left and red color in right) on both eyes in the double_eye_img.
    """

    #####reduce iris boundary
    double_eye_img_modified = double_eye_img.copy()
    if reduce:
        for i in range(reduce_size):
            iris_left_matrix, iris_right_matrix = matrix_reduce(iris_left_matrix, iris_right_matrix)
        left_matrix = iris_left_matrix
        right_matrix = iris_right_matrix
        for i in range(left_matrix.shape[0]):
            for j in range(left_matrix.shape[1]):
                if left_matrix[i][j] != 1:
                    iris_left[i][j] = np.asarray([255, 255, 255])

        for i in range(right_matrix.shape[0]):
            for j in range(right_matrix.shape[1]):
                if right_matrix[i][j] != 1:
                    iris_right[i][j] = np.asarray([255, 255, 255])
    else:
        left_matrix = iris_left_matrix
        right_matrix = iris_right_matrix

    left_matrix_new = np.logical_xor(left_matrix, l_highlights)
    right_matrix_new = np.logical_xor(right_matrix, r_highlights)
    l_iris_vals = left_eye_image[left_matrix_new, :]
    r_iris_vals = right_eye_image[right_matrix_new, :]
    lIrisMean = np.mean(l_iris_vals, axis=0).astype(int)
    rIrisMean = np.mean(r_iris_vals, axis=0).astype(int)

    iris_left_ori_reduce_iris_color = iris_left.astype(int) - lIrisMean
    iris_right_ori_reduce_iris_color = iris_right.astype(int) - rIrisMean
    iris_left_ori_reduce_iris_color[iris_left_ori_reduce_iris_color < 0] = 0
    iris_right_ori_reduce_iris_color[iris_right_ori_reduce_iris_color < 0] = 0
    iris_left_ori_reduce_iris_color = iris_left_ori_reduce_iris_color.astype(np.uint8)
    iris_right_ori_reduce_iris_color = iris_right_ori_reduce_iris_color.astype(np.uint8)

    #### calculate threshold.
    # iris_left_Gray = cv2.cvtColor(iris_left_ori_reduce_iris_color, cv2.COLOR_BGR2GRAY)
    # iris_right_Gray = cv2.cvtColor(iris_right_ori_reduce_iris_color, cv2.COLOR_BGR2GRAY)
    iris_left_HSV = cv2.cvtColor(iris_left_ori_reduce_iris_color, cv2.COLOR_BGR2HSV)
    iris_right_HSV = cv2.cvtColor(iris_right_ori_reduce_iris_color, cv2.COLOR_BGR2HSV)

    # CLAHE Enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    iris_left_HSV[:,:,2] = clahe.apply(iris_left_HSV[:,:,2])
    iris_right_HSV[:,:,2] = clahe.apply(iris_right_HSV[:,:,2])

    left_color_list = []
    for i in range(left_matrix.shape[0]):
        for j in range(left_matrix.shape[1]):
            if left_matrix[i][j] == 1:
                left_color_list.append(iris_left_HSV[i][j])

    if len(left_color_list) == 0:
        the_left_V = 255 # High threshold = no highlights
    else:
        # threshold_yen might fail on small inputs too, fallback to safe default if needed
        try:
             arr = np.asarray(left_color_list)
             if arr.ndim == 1: # Empty or malformed
                 the_left_V = 255
             else:
                 the_left_V = filter.threshold_yen(arr[:, 2]) * threshold_scale_left
        except:
             the_left_V = 255

    right_color_list = []
    for i in range(right_matrix.shape[0]):
        for j in range(right_matrix.shape[1]):
            if right_matrix[i][j] == 1:
                right_color_list.append(iris_right_HSV[i][j])
    
    if len(right_color_list) == 0:
        the_right_V = 255
    else:
        try:
             arr = np.asarray(right_color_list)
             if arr.ndim == 1:
                 the_right_V = 255
             else:
                 the_right_V = filter.threshold_yen(arr[:, 2]) * threshold_scale_right
        except:
             the_right_V = 255

    #### extract highlights.
    left_recolor = np.zeros((iris_left.shape[0], iris_left.shape[1], 3), dtype=np.uint8)
    right_recolor = np.zeros((iris_right.shape[0], iris_right.shape[1], 3), dtype=np.uint8)
    left_recolor_matrix = np.zeros((iris_left.shape[0], iris_left.shape[1]), dtype=int)
    right_recolor_matrix = np.zeros((iris_right.shape[0], iris_right.shape[1]), dtype=int)

    for i in range(left_matrix.shape[0]):
        for j in range(left_matrix.shape[1]):
            if left_matrix[i][j]==1:
                if iris_left_HSV[i][j][2]>the_left_V:
                    left_recolor[i][j]=np.asarray([0, 0, 0])
                    left_recolor_matrix[i][j] = 1
                    
                    # Add bounds check before writing to double_eye_img_modified
                    dy = i+double_eye_position_difference_list[0][1]
                    dx = j+double_eye_position_difference_list[0][0]
                    if 0 <= dy < double_eye_img_modified.shape[0] and 0 <= dx < double_eye_img_modified.shape[1]:
                        double_eye_img_modified[dy][dx]=np.asarray([0, 255, 0])
                else:
                    left_recolor[i][j] = np.asarray([255, 255, 255])
                    left_recolor_matrix[i][j] = 0
            else:
                left_recolor[i][j] = np.asarray([255, 255, 255])
                left_recolor_matrix[i][j] = 0

    for i in range(right_matrix.shape[0]):
        for j in range(right_matrix.shape[1]):
            if right_matrix[i][j] == 1:
                if iris_right_HSV[i][j][2] > the_right_V:
                    right_recolor[i][j] = np.asarray([0, 0, 0])
                    right_recolor_matrix[i][j] = 1
                    
                    # Add bounds check
                    dy = i + double_eye_position_difference_list[1][1]
                    dx = j + double_eye_position_difference_list[1][0]
                    if 0 <= dy < double_eye_img_modified.shape[0] and 0 <= dx < double_eye_img_modified.shape[1]:
                         double_eye_img_modified[dy][dx] = np.asarray([255, 0, 0])
                else:
                    right_recolor[i][j] = np.asarray([255, 255, 255])
                    right_recolor_matrix[i][j] = 0
            else:
                right_recolor[i][j] = np.asarray([255, 255, 255])
                right_recolor_matrix[i][j] = 0

    #######Create 2 consistent images and matrix
    max_x_axis = max(iris_left.shape[0],iris_right.shape[0])
    max_y_axis = max(iris_left.shape[1], iris_right.shape[1])
    left_ori_resize = np.full((max_x_axis, max_y_axis, 3), 255, dtype=np.uint8)
    right_ori_resize = np.full((max_x_axis, max_y_axis, 3), 255, dtype=np.uint8)
    left_recolor_resize = np.full((max_x_axis, max_y_axis, 3), 255, dtype=np.uint8)
    right_recolor_resize = np.full((max_x_axis, max_y_axis, 3), 255, dtype=np.uint8)
    left_recolor_matrix_resize = np.zeros((max_x_axis, max_y_axis), dtype=int)
    right_recolor_matrix_resize = np.zeros((max_x_axis, max_y_axis), dtype=int)
    left_matrix_resize = np.zeros((max_x_axis, max_y_axis), dtype=int)
    right_matrix_resize = np.zeros((max_x_axis, max_y_axis), dtype=int)

    for i in range(left_recolor.shape[0]):
        for j in range(left_recolor.shape[1]):
            # left_recolor_resize[i][j]=left_recolor[i][j]
            left_ori_resize[i][j] = iris_left[i][j]
            left_recolor_matrix_resize[i][j]=left_recolor_matrix[i][j]
            left_matrix_resize[i][j]= left_matrix[i][j]

    for i in range(right_recolor.shape[0]):
        for j in range(right_recolor.shape[1]):
            # right_recolor_resize[i][j] = right_recolor[i][j]
            right_ori_resize[i][j] = iris_right[i][j]
            right_recolor_matrix_resize[i][j] = right_recolor_matrix[i][j]
            right_matrix_resize[i][j] = right_matrix[i][j]


    
    debug_l_pixels = np.sum(left_recolor_matrix_resize)
    debug_r_pixels = np.sum(right_recolor_matrix_resize)
    if debug_l_pixels == 0 or debug_r_pixels == 0:
        return iris_left,iris_right,iris_left_matrix,iris_right_matrix,iris_left,iris_right,-1.0,double_eye_img, 0.0

    ####do shift (or translation)
    # Fixed: Use max_y (Width) for LR shift, max_x (Height) for UD shift. Enforce min range.
    range_lr = max(int(max_y_axis/4), 6)
    range_ud = max(int(max_x_axis/4), 6)

    opt_img_left_shift, max_overlap, opt_shift, IOU_score \
        = shift(left_recolor_matrix_resize, right_recolor_matrix_resize, \
                -range_lr, range_lr, -range_ud, range_ud)

    #####draw recolor resize
    left_matrix_ud_resize = shiftbits(left_matrix_resize, opt_shift[0], matrix=True)
    left_matrix_lr_resize = np.transpose(shiftbits(np.transpose(left_matrix_ud_resize), opt_shift[1], matrix=True))
    
    # --- SSIM Calculation ---
    # Convert original resized irises to grayscale for SSIM
    left_gray = cv2.cvtColor(left_ori_resize, cv2.COLOR_RGB2GRAY)
    right_gray = cv2.cvtColor(right_ori_resize, cv2.COLOR_RGB2GRAY)
    
    # Apply the same shift to the left grayscale image
    left_gray_ud = shiftbits(left_gray, opt_shift[0], matrix=True) # shiftbits works on 2D arrays
    left_gray_aligned = np.transpose(shiftbits(np.transpose(left_gray_ud), opt_shift[1], matrix=True))
    
    # Mask out background (0) to avoid artificial similarity on black borders?
    # Or just compute on the whole patch. The patch includes the iris and white background.
    # The shift introduces 0s (black) which might clash with white bg.
    # Let's just compute SSIM on the aligned images.
    
    # Ensure dimensions match and types are correct
    left_gray_aligned = left_gray_aligned.astype(np.uint8)
    right_gray = right_gray.astype(np.uint8)
    
    try:
        ssim_score, _ = compare_ssim(left_gray_aligned, right_gray, full=True)
    except Exception as e:
        print(f"SSIM Error: {e}")
        ssim_score = 0.0

    for i in range(opt_img_left_shift.shape[0]):
        for j in range(opt_img_left_shift.shape[1]):
            if left_matrix_lr_resize[i][j] == 1:
                if opt_img_left_shift[i][j] == 1:
                    left_recolor_resize[i][j] = np.asarray([0, 255, 0])
                else:
                    left_recolor_resize[i][j] = np.asarray([255, 255, 255])
            else:
                left_recolor_resize[i][j] = np.asarray([255,255,255])
            if right_matrix_resize[i][j]==1:
                if right_recolor_matrix_resize[i][j]==1:
                    right_recolor_resize[i][j] = np.asarray([255, 0, 0])
                else:
                    right_recolor_resize[i][j] = np.asarray([255, 255, 255])
            else:
                right_recolor_resize[i][j] = np.asarray([255,255,255])
    return iris_left, iris_right, left_recolor, right_recolor, left_recolor_resize, right_recolor_resize, IOU_score, double_eye_img_modified, ssim_score
