import cv2
import numpy as np

def scan(img):

    dim_limit = 1000
    max_dim = max(img.shape)

    if max_dim > dim_limit:
        resize_scale = dim_limit / max_dim
        img = cv2.resize(img, None, fx=resize_scale, fy=resize_scale)

    org_img = img.copy()

    # to detect edges properly .. we need to remove text from the document
    # not convolution .. the kernel is there but here this is energy difference comparison .. something of that sort
    kernel = np.ones((5, 5), np.uint8)
    img_morphed = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel, iterations=3)
    # MORPH_CLOSE .. does the dilation then erosion .. so it is useful for filling small parts and join broken parts

    img = img_morphed

    # cv2.imwrite("image_after_morphology.jpg", img)

    # alright .. now we need to extract the foreground -- GrabCut
    mask = np.zeros(img.shape[:2], np.uint8)
    bgdModel = np.zeros((1, 65), np.float64)
    fgdModel = np.zeros((1, 65), np.float64)
    rect = (20, 20, img.shape[1] - 40, img.shape[0] - 40)  # small margin
    cv2.grabCut(img, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
    mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
    img_fg = img * mask2[:, :, np.newaxis]

    img = img_fg
    
    # cv2.imwrite("image_foreground.jpg", img)

    # grayscale and blurring make it better for proper edge detection
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_blur_img = cv2.GaussianBlur(gray_img, (11, 11), 0)

    # cv2.imwrite("image_gray_blur.jpg", gray_blur_img)

    img = gray_blur_img

    # for edge detection we use Canny
    canny_img = cv2.Canny(img, threshold1=5, threshold2=180)
    canny_img_dilated = cv2.dilate(canny_img, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5)))

    # cv2.imwrite("canny_img.jpg", canny_img)
    # cv2.imwrite("canny_img_dilated.jpg", canny_img_dilated)

    img = canny_img_dilated

    # we find contours and keep the largest ones
    contours, _ = cv2.findContours(img, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    pages = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

    # print(type(contours), type(img))
    if not pages:
        raise ValueError("No contours found!")
    for c in pages:
        epsilon = 0.02 * cv2.arcLength(c, True)
        corners = cv2.approxPolyDP(c, epsilon, True) # we find the corners here
        if len(corners) == 4:
            break
    else:
        raise ValueError("No document-like quadrilateral found!")


    corners = sorted(np.concatenate(corners).tolist()) # we arrange the corners 
    corners = order_points(corners)
    destination_corners = find_dest(corners)

    h, w = org_img.shape[:2]
    M = cv2.getPerspectiveTransform(np.float32(corners), np.float32(destination_corners))
    final = cv2.warpPerspective(org_img, M, (destination_corners[2][0], destination_corners[2][1]),
                                flags=cv2.INTER_LINEAR)

    # cv2.imwrite("perpective_transform.jpg", final)

    return final



def main():
    
    img1 = cv2.imread("test_image_2.jpg")
    scanned1 = scan(img1)
    #img2 = cv2.imread("keyboard.jpg")
    #scanned2 = scan(img2)

    cv2.imwrite("final_doc.jpg", scanned1)
    #cv2.imwrite("final_keyboard.jpg", scanned2)

def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    pts = np.array(pts)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]      # top-left
    rect[2] = pts[np.argmax(s)]      # bottom-right
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]   # top-right
    rect[3] = pts[np.argmax(diff)]   # bottom-left
    return rect.astype('int').tolist()

def find_dest(pts):
    (tl, tr, br, bl) = pts
    widthA = np.hypot(br[0] - bl[0], br[1] - bl[1])
    widthB = np.hypot(tr[0] - tl[0], tr[1] - tl[1])
    maxWidth = max(int(widthA), int(widthB))
    heightA = np.hypot(tr[0] - br[0], tr[1] - br[1])
    heightB = np.hypot(tl[0] - bl[0], tl[1] - bl[1])
    maxHeight = max(int(heightA), int(heightB))
    destination_corners = [[0, 0], [maxWidth, 0], [maxWidth, maxHeight], [0, maxHeight]]
    return order_points(destination_corners)

if __name__ == "__main__":
    main()
