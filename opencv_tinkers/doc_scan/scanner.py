import cv2
import numpy as np

def order_points(pts):

    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)] # top-left
    rect[2] = pts[np.argmax(s)] # bottom-right
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # top-right
    rect[3] = pts[np.argmax(diff)]  # bottom-left
    return rect

def four_point_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    # Compute new image dimensions
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = int(max(widthA, widthB))
    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = int(max(heightA, heightB))
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped

def scan_doc(input_path, output_path="scanned_document.png", debug=False):
    # 1. Load image and compute ratio of old height to new height
    image = cv2.imread(input_path)
    if image is None:
        raise FileNotFoundError(f"Could not read input image: {input_path}")
    orig = image.copy()
    orig_height = image.shape[0]
    target_height = 500.0
    ratio = orig_height / target_height
    image = cv2.resize(image, (int(image.shape[1] / ratio), int(target_height)))

    # 2. Convert to grayscale and apply bilateral filter to preserve edges
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)

    # 3. Edge detection
    edged = cv2.Canny(gray, 30, 200)

    # 4. Find contours and select the document contour
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
    doc_cnt = None
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            doc_cnt = approx.reshape(4, 2)
            break

    if doc_cnt is None:
        raise ValueError("Could not find a document-like contour. Try a clearer or more zoomed-in photo.")

    # 5. Apply perspective transform
    doc_cnt = doc_cnt * ratio  # scale contour to original image size
    warped = four_point_transform(orig, doc_cnt)

    # 6. Convert to grayscale and apply Otsu's thresholding
    warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    _, scanned = cv2.threshold(warped_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 7. Save result
    cv2.imwrite(output_path, scanned)
    if debug:
        print(f"Scanned document saved as {output_path}")

if __name__ == "__main__":
    # Example usage
    scan_doc("test_image_2.jpg", "scanned_document.png", debug=True)
