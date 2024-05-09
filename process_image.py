# import the necessary packages
import numpy as np
# import pytesseract
import argparse
import imutils
import cv2
from PIL import Image
import tempfile

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True,
	help="path to input image to be OCR'd")
args = vars(ap.parse_args())

# print_dpi = 300

# new_filename = 'STM_topography_resized.png'

# img = Image.open(args["image"])
# print(f'{img.size=}')
# width, height = img.size

# # new_size = int(print_dpi * print_size)
# # img = img.resize((new_size, new_size), resample=Image.BICUBIC)
# # img.show()
# img.save(new_filename, dpi=(print_dpi, print_dpi))

# def set_image_dpi():
#   image_resize = Image.open(args["image"])
#   temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
#   temp_filename = temp_file.name
#   image_resize.save(temp_filename, dpi=(300, 300))
#   return temp_filename

# load the input image and convert it to grayscale
img = cv2.imread(args["image"])
# gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# norm_img = np.zeros((image.shape[0], image.shape[1]))
# img = cv2.normalize(gray, norm_img, 0, 255, cv2.NORM_MINMAX)
# contrast = cv2.convertScaleAbs(img, 3, 0)
# cv2.imwrite("processed.jpg", contrast)

# converting to LAB color space
lab= cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
l_channel, a, b = cv2.split(lab)

# Applying CLAHE to L-channel
# feel free to try different values for the limit and grid size:
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
cl = clahe.apply(l_channel)

# merge the CLAHE enhanced L-channel with the a and b channel
limg = cv2.merge((cl,a,b))

# Converting image from LAB Color model to BGR color spcae
enhanced_img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

# Stacking the original image with the enhanced image
result = np.hstack((img, enhanced_img))

gray = cv2.cvtColor(enhanced_img, cv2.COLOR_BGR2GRAY)
cv2.imwrite("processed.jpg", gray)

# noised = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 15)
# # sobely = cv2.Sobel(noised,cv2.CV_64F,0,1,ksize=9)
# # contrast = cv2.convertScaleAbs(noised, 2.2, 0)
# dpi = set_image_dpi()
# cv2.imwrite("processed.jpg", dpi)

# img = np.array(image, dtype=np.uint8)

# #convert to greyscale
# img_grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# #remove noise
# img_smooth = cv2.GaussianBlur(img_grey, (13,13), 0)
# contrast = cv2.convertScaleAbs(img_smooth, 2.2, 1)
# sobely = cv2.Sobel(img_smooth,cv2.CV_64F,0,1,ksize=9)
# graySobel = cv2.convertScaleAbs(sobely)
# thres = cv2.adaptiveThreshold(graySobel, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#                           cv2.THRESH_BINARY, 73, 2)

# cv2.imwrite("processed.jpg", contrast)

# threshold the image using Otsu's thresholding method
# thresh = cv2.threshold(gray, 0, 255,
# 	cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]



# # apply a distance transform which calculates the distance to the
# # closest zero pixel for each pixel in the input image
# dist = cv2.distanceTransform(thresh, cv2.DIST_L2, 5)

# # normalize the distance transform such that the distances lie in
# # the range [0, 1] and then convert the distance transform back to
# # an unsigned 8-bit integer in the range [0, 255]
# dist = cv2.normalize(dist, dist, 0, 1.0, cv2.NORM_MINMAX)
# dist = (dist * 255).astype("uint8")
# cv2.imshow("Dist", dist)

# # threshold the distance transform using Otsu's method
# dist = cv2.threshold(dist, 0, 255,
# 	cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
# cv2.imshow("Dist Otsu", dist)

# # apply an "opening" morphological operation to disconnect components
# # in the image
# kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
# opening = cv2.morphologyEx(dist, cv2.MORPH_OPEN, kernel)
# cv2.imshow("Opening", opening)

# # find contours in the opening image, then initialize the list of
# # contours which belong to actual characters that we will be OCR'ing
# cnts = cv2.findContours(opening.copy(), cv2.RETR_EXTERNAL,
# 	cv2.CHAIN_APPROX_SIMPLE)
# cnts = imutils.grab_contours(cnts)
# chars = []

# # loop over the contours
# for c in cnts:
# 	# compute the bounding box of the contour
# 	(x, y, w, h) = cv2.boundingRect(c)
	
# 	# check if contour is at least 35px wide and 100px tall, and if
# 	# so, consider the contour a digit
# 	if w >= 35 and h >= 100:
# 		chars.append(c)
		
# # compute the convex hull of the characters
# chars = np.vstack([chars[i] for i in range(0, len(chars))])
# hull = cv2.convexHull(chars)

# # allocate memory for the convex hull mask, draw the convex hull on
# # the image, and then enlarge it via a dilation
# mask = np.zeros(image.shape[:2], dtype="uint8")
# cv2.drawContours(mask, [hull], -1, 255, -1)
# mask = cv2.dilate(mask, None, iterations=2)
# cv2.imshow("Mask", mask)

# # take the bitwise of the opening image and the mask to reveal *just*
# # the characters in the image
# final = cv2.bitwise_and(opening, opening, mask=mask)


# # show the final output image
# cv2.imshow("Final", final)
# cv2.waitKey(0)