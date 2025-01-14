import tkinter as tk
from tkinter import messagebox
import cv2
import os
import csv
import numpy as np
from PIL import Image
import pandas as pd
import datetime
import time

window = tk.Tk()
window.title("Face Recognizer")
window.geometry('1280x720')
window.configure(background='grey')

message = tk.Label(window, text="Face-Recognition-Based-Attendance-Management-System", fg="black", bg="grey", font=('times', 30, 'italic bold underline'))
message.place(x=200, y=20)

lbl = tk.Label(window, text="Enter ID", width=20, height=2, bg="grey", font=('times', 15, 'bold'))
lbl.place(x=400, y=200)

txt = tk.Entry(window, width=20, bg="white", font=('times', 15, 'bold'))
txt.place(x=700, y=215)

lbl2 = tk.Label(window, text="Enter Name", width=20, bg="grey", height=2, font=('times', 15, 'bold'))
lbl2.place(x=400, y=300)

txt2 = tk.Entry(window, width=20, bg="white", font=('times', 15, 'bold'))
txt2.place(x=700, y=315)

lbl3 = tk.Label(window, text="Notification : ", width=20, bg="grey", height=2, font=('times', 15, 'bold'))
lbl3.place(x=400, y=400)

message_label = tk.Label(window, text="", bg="grey", width=30, height=2, activebackground="yellow", font=('times', 15, 'bold'))
message_label.place(x=700, y=400)

lbl4 = tk.Label(window, text="Attendance : ", width=20, bg="grey", height=2, font=('times', 15, 'bold underline'))
lbl4.place(x=400, y=600)

message2 = tk.Label(window, text="", bg="grey", activeforeground="green", width=30, height=2, font=('times', 15, 'bold'))
message2.place(x=700, y=600)

def clear():
    txt.delete(0, 'end')
    message_label.configure(text="")

def clear2():
    txt2.delete(0, 'end')
    message_label.configure(text="")

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False

def TakeImages():
    Id = txt.get()
    name = txt2.get()
    if is_number(Id) and name != "":
        if not os.path.exists('TrainingImage'):
            os.makedirs('TrainingImage')
        
        cam = cv2.VideoCapture(0)
        harcascadePath = "haarcascade_frontalface_default.xml"
        detector = cv2.CascadeClassifier(harcascadePath)
        sampleNum = 0
        while True:
            ret, img = cam.read()
            if not ret:
                messagebox.showerror("Error", "Failed to capture image from webcam.")
                break

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
                sampleNum += 1
                cv2.imwrite(f"TrainingImage/{name}.{Id}.{str(sampleNum)}.jpg", gray[y:y+h, x:x+w])
                cv2.imshow('frame', img)
            if cv2.waitKey(100) & 0xFF == ord('q'):
                break
            elif sampleNum > 60:
                break
        cam.release()
        cv2.destroyAllWindows()
        res = f"Images Saved for ID : {Id} Name : {name}"
        row = [Id, name]
        if not os.path.exists('StudentDetails'):
            os.makedirs('StudentDetails')
        with open('StudentDetails/StudentDetails.csv', 'a+', newline='') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow(row)
        message.configure(text=res)
    else:
        if not is_number(Id):
            res = "Enter Numeric Id"
        elif name == "":
            res = "Enter Alphabetical Name"
        else:
            res = "Invalid Input"
        message.configure(text=res)

def TrainImages():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    harcascadePath = "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(harcascadePath)

    if not os.path.exists('TrainingImage'):
        raise FileNotFoundError("TrainingImage directory not found. Please add images first.")

    faces, Ids = getImagesAndLabels("TrainingImage")
    recognizer.train(faces, np.array(Ids))

    if not os.path.exists('TrainingImageLabel'):
        os.makedirs('TrainingImageLabel')

    recognizer.save("TrainingImageLabel/Trainner.yml")
    if not os.path.isfile("TrainingImageLabel/Trainner.yml"):
        raise IOError("Failed to save the Trainner.yml file.")

    print("Images Trained")

if __name__ == "__main__":
    try:
        TrainImages()
    except Exception as e:
        print(f"Error: {str(e)}")

def getImagesAndLabels(path):
    if not os.path.exists(path):
        messagebox.showerror("Error", f"{path} directory not found.")
        return [], []
    
    imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
    faces = []
    Ids = []
    
    for imagePath in imagePaths:
        pilImage = Image.open(imagePath).convert('L')
        imageNp = np.array(pilImage, 'uint8')
        Id = int(os.path.split(imagePath)[-1].split(".")[1])
        faces.append(imageNp)
        Ids.append(Id)
    return faces, Ids

def TrackImages():
    try:
        if not os.path.isfile("TrainingImageLabel/Trainner.yml"):
            raise FileNotFoundError("TrainingImageLabel/Trainner.yml not found. Please train the images first.")
        
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read("TrainingImageLabel/Trainner.yml")
        harcascadePath = "haarcascade_frontalface_default.xml"
        faceCascade = cv2.CascadeClassifier(harcascadePath)
        
        if not os.path.isfile('StudentDetails/StudentDetails.csv'):
            raise FileNotFoundError("StudentDetails.csv not found. Please ensure the student details are available.")
        
        df = pd.read_csv('StudentDetails/StudentDetails.csv')
        cam = cv2.VideoCapture(0)
        font = cv2.FONT_HERSHEY_SIMPLEX
        col_names = ['Id', 'Name', 'Date', 'Time']
        attendance = pd.DataFrame(columns=col_names)
        
        while True:
            ret, im = cam.read()
            if not ret:
                raise Exception("Failed to capture image from webcam")
                
            gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
            faces = faceCascade.detectMultiScale(gray, 1.2, 5)
            
            for (x, y, w, h) in faces:
                cv2.rectangle(im, (x, y), (x+w, y+h), (225, 0, 0), 2)
                Id, conf = recognizer.predict(gray[y:y+h, x:x+w])
                if conf < 60:
                    ts = time.time()
                    date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                    timeStamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                    
                    aa = df.loc[df['Id'] == Id]['Name'].values
                    
                    if len(aa) > 0:
                        name = aa[0]
                    else:
                        name = "Unknown"
                    
                    tt = f"{Id}-{name}"
                    attendance.loc[len(attendance)] = [Id, name, date, timeStamp]
                else:
                    Id = 'Unknown'
                    tt = str(Id)
                
                cv2.putText(im, str(tt), (x, y+h), font, 1, (255, 255, 255), 2)
            
            attendance = attendance.drop_duplicates(subset=['Id'], keep='first')
            cv2.imshow('Face Recognition', im)
            if cv2.waitKey(1) == ord('q'):
                break

    except Exception as e:
        message2.configure(text=f"Error: {str(e)}")
        print(f"Error: {str(e)}")
    
    finally:
        cam.release()
        cv2.destroyAllWindows()
        if 'attendance' in locals():
            if not os.path.exists('Attendance'):
                os.makedirs('Attendance')
            ts = time.time()
            date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
            timeStamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
            Hour, Minute, Second = timeStamp.split(":")
            fileName = f"Attendance/Attendance_{date}_{Hour}-{Minute}-{Second}.csv"
            attendance.to_csv(fileName, index=False)
            print("Attendance saved successfully.")
            message2.configure(text=attendance.to_string(index=False))

clearButton = tk.Button(window, text="Clear", command=clear, width=5, height=1, activebackground="Red", font=('times', 15, 'bold'))
clearButton.place(x=950, y=210)

clearButton2 = tk.Button(window, text="Clear", command=clear2, width=5, height=1, activebackground="Red", font=('times', 15, 'bold'))
clearButton2.place(x=950, y=310)

takeImg = tk.Button(window, text="Take Images", command=TakeImages, width=10, height=1, activebackground="Red", font=('times', 15, 'bold'))
takeImg.place(x=200, y=500)

trainImg = tk.Button(window, text="Train Images", command=TrainImages, width=10, height=1, activebackground="Red", font=('times', 15, 'bold'))
trainImg.place(x=500, y=500)

trackImg = tk.Button(window, text="Track Images", command=TrackImages, width=10, height=1, activebackground="Red", font=('times', 15, 'bold'))
trackImg.place(x=800, y=500)

quitWindow = tk.Button(window, text="Quit", command=window.destroy, width=10, height=1, activebackground="Red", font=('times', 15, 'bold'))
quitWindow.place(x=1100, y=500)

window.mainloop()
