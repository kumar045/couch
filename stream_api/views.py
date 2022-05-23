from .models import *
from .serializers import StreamSerializer
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from rest_framework import status
import cv2
import numpy as np
import glob
import random
import base64
from .download import download_image
class StreamAPIView(CreateAPIView):
    serializer_class =StreamSerializer
    queryset = Stream.objects.all()
    def create(self, request, format=None):
        """
                Takes the request from the post and then processes the algorithm to extract the data and return the result in a
                JSON format
                :param request:
                :param format:
                :return:
                """

        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():

            query=self.request.data['query']
           
           
            # print(stream_bytes)

            content = []

            

            # print("main_image_url:::::",stream_bytes)
           
            collection_of_streambytes=self.mainfunc(query)
           

            # add result to the dictionary and revert as response
            mydict = {
                'status': True,
                'response':
                    {

                        'collection_of_streambytes': collection_of_streambytes,
                    }
            }
            content.append(mydict)
            # print(content)

            return Response(content, status=status.HTTP_200_OK)
        errors = serializer.errors

        response_text = {
                "status": False,
                "response": errors
            }
        return Response(response_text, status=status.HTTP_400_BAD_REQUEST)
    

    def mainfunc(self,query):
        # Constants.
        INPUT_WIDTH = 640
        INPUT_HEIGHT = 640
        SCORE_THRESHOLD = 0.5
        NMS_THRESHOLD = 0.45
        CONFIDENCE_THRESHOLD = 0.45

        # Text parameters.
        FONT_FACE = cv2.FONT_HERSHEY_SIMPLEX
        FONT_SCALE = 0.7
        THICKNESS = 1

        # Colors
        BLACK  = (0,0,0)
        BLUE   = (255,178,50)
        YELLOW = (0,255,255)
        RED = (0,0,255)
            
        mydict={}
        def draw_label(input_image, label, left, top):
            """Draw text onto image at location."""
            
            # Get text size.
            text_size = cv2.getTextSize(label, FONT_FACE, FONT_SCALE, THICKNESS)
            dim, baseline = text_size[0], text_size[1]
            # Use text size to create a BLACK rectangle. 
            cv2.rectangle(input_image, (left, top), (left + dim[0], top + dim[1] + baseline), BLACK, cv2.FILLED);
            # Display text inside the rectangle.
            cv2.putText(input_image, label, (left, top + dim[1]), FONT_FACE, FONT_SCALE, YELLOW, THICKNESS, cv2.LINE_AA)


        def pre_process(input_image, net):
            # Create a 4D blob from a frame.
            blob = cv2.dnn.blobFromImage(input_image, 1/255, (INPUT_WIDTH, INPUT_HEIGHT), [0,0,0], 1, crop=False)

            # Sets the input to the network.
            net.setInput(blob)

            # Runs the forward pass to get output of the output layers.
            output_layers = net.getUnconnectedOutLayersNames()
            outputs = net.forward(output_layers)
            # print(outputs[0].shape)

            return outputs


        def post_process(input_image, outputs,j):
            # Lists to hold respective values while unwrapping.
            class_ids = []
            confidences = []
            boxes = []

            # Rows.
            rows = outputs[0].shape[1]

            image_height, image_width = input_image.shape[:2]

            # Resizing factor.
            x_factor = image_width / INPUT_WIDTH
            y_factor =  image_height / INPUT_HEIGHT

            # Iterate through 25200 detections.
            for r in range(rows):
                row = outputs[0][0][r]
                confidence = row[4]

                # Discard bad detections and continue.
                if confidence >= CONFIDENCE_THRESHOLD:
                    classes_scores = row[5:]

                    # Get the index of max class score.
                    class_id = np.argmax(classes_scores)

                    #  Continue if the class score is above threshold.
                    if (classes_scores[class_id] > SCORE_THRESHOLD):
                        confidences.append(confidence)
                        class_ids.append(class_id)

                        cx, cy, w, h = row[0], row[1], row[2], row[3]

                        left = int((cx - w/2) * x_factor)
                        top = int((cy - h/2) * y_factor)
                        width = int(w * x_factor)
                        height = int(h * y_factor)
                    
                        box = np.array([left, top, width, height])
                        boxes.append(box)

            # Perform non maximum suppression to eliminate redundant overlapping boxes with
            # lower confidences.
            indices = cv2.dnn.NMSBoxes(boxes, confidences, CONFIDENCE_THRESHOLD, NMS_THRESHOLD)
            for i in indices:
                box = boxes[i]
                left = box[0]
                top = box[1]
                width = box[2]
                height = box[3]
            
                label = "{}:{:.2f}".format(classes[class_ids[i]], confidences[i])
                if classes[class_ids[i]]=="couch":
                    cv2.rectangle(input_image, (left, top), (left + width, top + height), BLUE, 3*THICKNESS)
                    draw_label(input_image, label, left, top)
                    n=random.randint(0,1000)
                    # print(left,top,width,height)
                    # pil_image=Image.fromarray(input_image)
                    # img_res = pil_image.crop((left, top, left + width, top + height))
                    croped=input_image[top:top+height,left:left+width]
                    hsv = cv2.cvtColor(croped, cv2.COLOR_BGR2HSV)
                    lower_range = np.array([0,0,0])
                    upper_range = np.array([180,255,30])
                    mask = cv2.inRange(hsv, lower_range, upper_range)
                    th, threshed = cv2.threshold(mask, 100, 255,cv2.THRESH_BINARY|cv2.THRESH_OTSU)
                    # findcontours
                    cnts = cv2.findContours(threshed, cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)[-2]
  
                    if cnts :
                        retval, buffer = cv2.imencode('.jpg', input_image)
                        jpg_as_text = base64.b64encode(buffer)
                        
                        mydict[j]=jpg_as_text
        

        # Load class names.
        classesFile = "coco.names"
        classes = None
        with open(classesFile, 'rt') as f:
            classes = f.read().rstrip('\n').split('\n')

        # Give the weight files to the model and load the network using them.
        modelWeights = "models/yolov5s.onnx"
        net = cv2.dnn.readNet(modelWeights)
        list_of_url=download_image(query)
        
        for i,j in zip(glob.glob("input/*"),list_of_url):
            
            # print(i)
            # Load image.
            frame = cv2.imread(i)

            # Process image.
            detections = pre_process(frame, net)
            post_process(frame.copy(), detections,j)
        return mydict