import tkinter as tk
from PIL import Image,ImageTk
from tkinter import ttk
import os, json
import ip
import image2globalcoords

false = False
global coords
global count 
count = 1 
global img_name

def on_configure(event):
    # update scrollregion after starting 'mainloop'
    # when all widgets are in canvas
    canvas.configure(scrollregion=canvas.bbox('all'))

shapes = ['None','Circle','Semicircle','Quarter_Circle','Triangle','Square','Rectangle','Trapezoid','Pentagon','Hexagon','Heptagon','Octagon','Star','Cross']
types = ['Standard','Emergent','Off-Axis']
coords = []

obj = {
    "alphanumeric": None,
    "alphanumeric_color": None,
    "autonomous": false,
    "latitude": None,
    "longitude": None,
    "mission": None,
    "orientation": None,
    "shape": None,
    "shape_color": None,
    "type": "Standard"
}


def next_img():
        global img_name
        img_name = next(imgs)
        var.set(img_name)
        img_label.image = ImageTk.PhotoImage(Image.open(img_name).resize((820,616)))
        img_label.create_image(3280//8,2464//8,image=img_label.image)
        img_label.bind("<Button-1>",save_coords)
        with open(img_name.split('.')[0]+'.json','rb') as infile:
                tele = json.load(infile)
        heading = tele['heading']
        lat = tele['latitude']
        lon = tele['longitude']


def submit(name):
        global img_name
        coords = []
        next_img()
def save_coords(event):
        global img_name
        click_loc = [event.x, event.y]
        print ("you clicked on", click_loc)
        loc = ip.geoloc(event.x, event.y, lat, lon, heading)
        obj["latitude"] = loc[0]
        obj["longitude"] = loc[1]
        print(click_loc)
        coords.append(click_loc)

def crop(name):
        global count
        global coords
        global img_name
        img = cv2.imread(name)
        img = cv2.resize(img,(3280//4,2464//4))
        final = img[coords[0][1]-15:coords[0][1]+15,coords[0][0]-15:coords[0][0]+15]
        final = cv2.resize(final,(100,100))
        cv2.imwrite('post/'+str(count)+'.jpg',final)
        obj["alphanumeric"] = e1.get().upper()
        obj["alphanumeric_color"] = e2.get().upper()
        obj["autonomous"] = false
        obj["mission"] = 3
        obj["orientation"] = e4.get().upper()
        obj["shape"] = variable.get().upper()
        obj["shape_color"] = e3.get().upper()
        obj["type"] = variable1.get().upper()
        print(obj)
        with open('post/'+str(count)+'.json','wb') as outfile:
                json.dump(obj, outfile)
        count += 1
        coords = []

def _on_mousewheel(event):
    canvas.yview_scroll(-1*(event.delta), "units")


root = tk.Tk()

# --- create canvas with scrollbar ---

canvas = tk.Canvas(root)
canvas.pack(side=tk.LEFT)
canvas.bind_all("<MouseWheel>", _on_mousewheel)

scrollbar = tk.Scrollbar(root, command=canvas.yview)
scrollbar.pack(side=tk.LEFT, fill='y')

canvas.configure(yscrollcommand = scrollbar.set)

# update scrollregion after starting 'mainloop'
# when all widgetss are in canvas
canvas.bind('<Configure>', on_configure)

# --- put frame in canvas ---

frame = tk.Frame(canvas)
canvas.create_window((3280//8, 2464//8), window=frame, anchor='nw')

# --- add widgets in frame ---
img_dir = os.getcwd()+"/odlcs"
os.chdir(img_dir)
img_list = []
for entry in os.listdir(img_dir):
    if entry.endswith('.jpg'):
        img_list.append(entry)
imgs = iter(img_list)
img_name = next(imgs)
with open(img_name.split('.')[0]+'.json','rb') as infile:
    tele = json.load(infile)

heading = tele['heading']
lat = tele['latitude']
lon = tele['longitude']
img = ImageTk.PhotoImage(Image.open(img_name).resize((820,616)))
img_label=tk.Canvas(root, width = 3280//4, height = 2464//4)
img_label.pack()
img_label.image = img
img_label.create_image(3280//8,2464//8,image=img_label.image)
img_label.bind("<Button-1>",save_coords)

var = tk.StringVar()
var.set(img_name)
l0 = tk.Label(frame,textvariable=var).pack()

l1 = tk.Label(frame,text="Alphanumeric")
l1.pack()
e1 = tk.Entry(frame,text="Alphanumeric")
e1.pack()

l2 = tk.Label(frame,text="Alphanumeric Colour")
l2.pack()
e2 = tk.Entry(frame,text="Alphanumeric Colour")
e2.pack()


variable = tk.StringVar(frame)
variable.set(shapes[0]) # default value

s = tk.Label(frame,text="Shape").pack()
w = ttk.OptionMenu(frame, variable, *shapes)
w.pack()


variable1 = tk.StringVar(frame)
variable1.set(types[0]) # default value

s1 = tk.Label(frame,text="Type")
s1.pack()
w1 = ttk.OptionMenu(frame, variable1, *types)
w1.pack()


l3 = tk.Label(frame,text="Shape Colour")
l3.pack()
e3 = tk.Entry(frame,text="Shape Colour")
e3.pack()


l4 = tk.Label(frame,text="Orientation")
l4.pack()
e4 = tk.Entry(frame,text="Orientation")
e4.pack()


b1 = ttk.Button(frame,text="Submit",command=lambda:submit(img_name)).pack()
b2 = ttk.Button(frame,text="Skip",command=lambda:next_img()).pack()
b3 = ttk.Button(frame,text="Crop",command=lambda:crop(img_name)).pack()


# --- start program ---

root.mainloop()