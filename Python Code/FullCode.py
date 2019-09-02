import matplotlib.pyplot as plt
import csv
import time
import datetime
import paho.mqtt.client as mqtt
import math
import RPi.GPIO as GPIO


#Declare GPIO
GPIO.setmode(GPIO.BCM)
RELAIS_1_GPIO = 16 #Biru
RELAIS_2_GPIO = 20 #Ijo
RELAIS_3_GPIO = 19 #Merah
RELAIS_4_GPIO = 26 #Kuning
GPIO.setup(RELAIS_1_GPIO, GPIO.OUT) # GPIO Assign mode
GPIO.setup(RELAIS_2_GPIO, GPIO.OUT) # GPIO Assign mode
GPIO.setup(RELAIS_3_GPIO, GPIO.OUT) # GPIO Assign mode
GPIO.setup(RELAIS_4_GPIO, GPIO.OUT) # GPIO Assign mode

#GPIO standby
GPIO.output(RELAIS_1_GPIO, GPIO.HIGH) # out
GPIO.output(RELAIS_2_GPIO, GPIO.HIGH) # out
GPIO.output(RELAIS_3_GPIO, GPIO.HIGH) # out
GPIO.output(RELAIS_4_GPIO, GPIO.HIGH) # out

#Declare the variable
ECstr = ""
ECin = 0
TinggiAirstr = ""
TinggiAirin = 0

###########################DEFINE FUZZY#######################
def EC_fuzzyfication(EC):
    EC_set = []
    if (EC >= 0 and EC <= 0.5):  # Sangat rendah datar (0 - 0.5)
        EC_set.append({"label": "sangat rendah", "nilai": 1})
    elif (EC > 0.5 and EC < 0.85):  # Sangat rendah turun & dibawah optimal naik (0.5 - 0.85)
        EC_set.append({"label": "sangat rendah", "nilai": (0.85 - EC) / (0.85 - 0.5)})
        EC_set.append({"label": "dibawah optimal", "nilai": (EC - 0.5) / (0.85 - 0.5)})
    elif (EC == 0.85):  # dibawah optimal puncak (0.85)
        EC_set.append({"label": "dibawah optimal", "nilai": 1})
    elif (EC > 0.85 and EC < 1.55):  # dibawah optimal turun, optimal naik (0.85 - 1.55)
        EC_set.append({"label": "dibawah optimal", "nilai": (1.55 - EC) / (1.55 - 0.85)})
        EC_set.append({"label": "optimal", "nilai": (EC - 0.85) / (1.55 - 0.85)})
    elif (EC == 1.55):  # optimal puncak (1.55)
        EC_set.append({"label": "optimal", "nilai": 1})
    elif (EC > 1.55 and EC < 2.25):  # optimal turun, diatas optimal naik (1.55 - 2.25)
        EC_set.append({"label": "optimal", "nilai": (2.25 - EC) / (2.25 - 1.55)})
        EC_set.append({"label": "diatas optimal", "nilai": (EC - 1.55) / (2.25 - 1.55)})
    elif (EC == 2.25):  # diatas optimal puncak (2.25)
        EC_set.append({"label": "diatas optimal", "nilai": 1})
    elif (EC > 2.25 and EC < 2.95):  # diatas optimal turun, kelebihan nutrisi naik (2.25 - 2.95)
        EC_set.append({"label": "diatas optimal", "nilai": (2.95 - EC) / (2.95 - 2.25)})
        EC_set.append({"label": "kelebihan nutrisi", "nilai": (EC - 2.25) / (2.95 - 2.25)})
    elif (EC == 2.95):  # kelebihan nutrisi puncak (2.95)
        EC_set.append({"label": "kelebihan nutrisi", "nilai": 1})
    elif (EC > 2.95 and EC < 3.3):  # kelebihan nutrisi turun, berkonsentrasi tinggi naik (2.95 - 3.3)
        EC_set.append({"label": "kelebihan nutrisi", "nilai": (3.3 - EC) / (3.3 - 2.95)})
        EC_set.append({"label": "berkonsentrasi tinggi", "nilai": (EC - 2.95) / (3.3 - 2.95)})
    elif (EC >= 3.3):  # berkonsentrasi tinggi puncak (3.3 - 4)
        EC_set.append({"label": "berkonsentrasi tinggi", "nilai": 1})

    print("EC:")
    print(EC_set)
    return EC_set

def ketinggian_air_fuzzyfication(ketinggian_air):
    ketinggian_air_set = []
    if (ketinggian_air >= 0 and ketinggian_air <= 4):  # Sangat rendah datar (0 - 4)
        ketinggian_air_set.append({"label": "sangat rendah", "nilai": 1})
    elif (ketinggian_air > 4 and ketinggian_air < 12):  # Sangat rendah turun & rendah naik (4 - 12)
        ketinggian_air_set.append({"label": "sangat rendah", "nilai": (12 - ketinggian_air) / (12 - 4)})
        ketinggian_air_set.append({"label": "rendah", "nilai": (ketinggian_air - 4) / (12 - 4)})
    elif (ketinggian_air == 12):  # rendah puncak (12)
        ketinggian_air_set.append({"label": "rendah", "nilai": 1})
    elif (ketinggian_air > 12 and ketinggian_air < 20):  # rendah turun, medium naik (12 - 20)
        ketinggian_air_set.append({"label": "rendah", "nilai": (20 - ketinggian_air) / (20 - 12)})
        ketinggian_air_set.append({"label": "sedang", "nilai": (ketinggian_air - 12) / (20 - 12)})
    elif (ketinggian_air == 20):  # medium puncak (20)
        ketinggian_air_set.append({"label": "sedang", "nilai": 1})
    elif (ketinggian_air > 20 and ketinggian_air < 28):  # medium turun, tinggi naik (20 - 28)
        ketinggian_air_set.append({"label": "sedang", "nilai": (28 - ketinggian_air) / (28 - 20)})
        ketinggian_air_set.append({"label": "tinggi", "nilai": (ketinggian_air - 20) / (28 - 20)})
    elif (ketinggian_air == 28):  # tinggi puncak (28)
        ketinggian_air_set.append({"label": "tinggi", "nilai": 1})
    elif (ketinggian_air > 28 and ketinggian_air < 36):  # tinggi turun, sangat tinggi naik (28 - 36)
        ketinggian_air_set.append({"label": "tinggi", "nilai": (36 - ketinggian_air) / (36 - 28)})
        ketinggian_air_set.append({"label": "sangat tinggi", "nilai": (ketinggian_air - 28) / (36 - 28)})
    elif (ketinggian_air >= 36):  # sangat tinggi datar (36 - 50)
        ketinggian_air_set.append({"label": "sangat tinggi", "nilai": 1})

    print("Ketinggian air:")
    print(ketinggian_air_set)
    return ketinggian_air_set


def inference(EC_set=[], ketinggian_air_set=[]):
    hasil = []
    for fuzz_EC in EC_set:
        for fuzz_air in ketinggian_air_set:
            # Menentukan nilai konjungsi
            nilai = min(fuzz_EC["nilai"], fuzz_air["nilai"])

            # Menentukan label konjungsi #ambil yg dari excel
            if (fuzz_EC["label"] == "sangat rendah" and fuzz_air["label"] == "sangat rendah"):
                hasil.append({"label": "sangat buruk", "nilai": nilai})
            elif (fuzz_EC["label"] == "sangat rendah" and fuzz_air["label"] == "rendah"):
                hasil.append({"label": "sangat buruk", "nilai": nilai})
            elif (fuzz_EC["label"] == "sangat rendah" and fuzz_air["label"] == "sedang"):
                hasil.append({"label": "sangat buruk", "nilai": nilai})
            elif (fuzz_EC["label"] == "sangat rendah" and fuzz_air["label"] == "tinggi"):
                hasil.append({"label": "sangat buruk", "nilai": nilai})
            elif (fuzz_EC["label"] == "sangat rendah" and fuzz_air["label"] == "sangat tinggi"):
                hasil.append({"label": "sangat buruk", "nilai": nilai})
            elif (fuzz_EC["label"] == "dibawah optimal" and fuzz_air["label"] == "sangat rendah"):
                hasil.append({"label": "sangat buruk", "nilai": nilai})
            elif (fuzz_EC["label"] == "dibawah optimal" and fuzz_air["label"] == "rendah"):
                hasil.append({"label": "buruk", "nilai": nilai})
            elif (fuzz_EC["label"] == "dibawah optimal" and fuzz_air["label"] == "sedang"):
                hasil.append({"label": "biasa", "nilai": nilai})
            elif (fuzz_EC["label"] == "dibawah optimal" and fuzz_air["label"] == "tinggi"):
                hasil.append({"label": "buruk", "nilai": nilai})
            elif (fuzz_EC["label"] == "dibawah optimal" and fuzz_air["label"] == "sangat tinggi"):
                hasil.append({"label": "buruk", "nilai": nilai})
            elif (fuzz_EC["label"] == "optimal" and fuzz_air["label"] == "sangat rendah"):
                hasil.append({"label": "sangat buruk", "nilai": nilai})
            elif (fuzz_EC["label"] == "optimal" and fuzz_air["label"] == "rendah"):
                hasil.append({"label": "baik", "nilai": nilai})
            elif (fuzz_EC["label"] == "optimal" and fuzz_air["label"] == "sedang"):
                hasil.append({"label": "sangat baik", "nilai": nilai})
            elif (fuzz_EC["label"] == "optimal" and fuzz_air["label"] == "tinggi"):
                hasil.append({"label": "baik", "nilai": nilai})
            elif (fuzz_EC["label"] == "optimal" and fuzz_air["label"] == "sangat tinggi"):
                hasil.append({"label": "buruk", "nilai": nilai})
            elif (fuzz_EC["label"] == "diatas optimal" and fuzz_air["label"] == "sangat rendah"):
                hasil.append({"label": "sangat buruk", "nilai": nilai})
            elif (fuzz_EC["label"] == "diatas optimal" and fuzz_air["label"] == "rendah"):
                hasil.append({"label": "biasa", "nilai": nilai})
            elif (fuzz_EC["label"] == "diatas optimal" and fuzz_air["label"] == "sedang"):
                hasil.append({"label": "baik", "nilai": nilai})
            elif (fuzz_EC["label"] == "diatas optimal" and fuzz_air["label"] == "tinggi"):
                hasil.append({"label": "biasa", "nilai": nilai})
            elif (fuzz_EC["label"] == "diatas optimal" and fuzz_air["label"] == "sangat tinggi"):
                hasil.append({"label": "buruk", "nilai": nilai})
            elif (fuzz_EC["label"] == "kelebihan nutrisi" and fuzz_air["label"] == "sangat rendah"):
                hasil.append({"label": "sangat buruk", "nilai": nilai})
            elif (fuzz_EC["label"] == "kelebihan nutrisi" and fuzz_air["label"] == "rendah"):
                hasil.append({"label": "buruk", "nilai": nilai})
            elif (fuzz_EC["label"] == "kelebihan nutrisi" and fuzz_air["label"] == "sedang"):
                hasil.append({"label": "biasa", "nilai": nilai})
            elif (fuzz_EC["label"] == "kelebihan nutrisi" and fuzz_air["label"] == "tinggi"):
                hasil.append({"label": "buruk", "nilai": nilai})
            elif (fuzz_EC["label"] == "kelebihan nutrisi" and fuzz_air["label"] == "sangat tinggi"):
                hasil.append({"label": "buruk", "nilai": nilai})
            elif (fuzz_EC["label"] == "berkonsentrasi tinggi" and fuzz_air["label"] == "sangat rendah"):
                hasil.append({"label": "sangat buruk", "nilai": nilai})
            elif (fuzz_EC["label"] == "berkonsentrasi tinggi" and fuzz_air["label"] == "rendah"):
                hasil.append({"label": "buruk", "nilai": nilai})
            elif (fuzz_EC["label"] == "berkonsentrasi tinggi" and fuzz_air["label"] == "sedang"):
                hasil.append({"label": "buruk", "nilai": nilai})
            elif (fuzz_EC["label"] == "berkonsentrasi tinggi" and fuzz_air["label"] == "tinggi"):
                hasil.append({"label": "buruk", "nilai": nilai})
            elif (fuzz_EC["label"] == "berkonsentrasi tinggi" and fuzz_air["label"] == "sangat tinggi"):
                hasil.append({"label": "sangat buruk", "nilai": nilai})
            else:
                print("not graded")

    x = 0
    # Menentukan label disjungsi
    result = [{"label": "sangat buruk", "nilai": 0}, {"label": "buruk", "nilai": 0}, {"label": "biasa", "nilai": 0}, {"label": "baik", "nilai": 0}, {"label": "sangat baik", "nilai": 0}]
    while x < len(hasil):
        # print(hasil[x])
        x += 1
    for hasil in hasil:
        if (hasil["label"] == "sangat buruk"):
            result[0]["nilai"] = max(hasil["nilai"], result[0]["nilai"])
        if (hasil["label"] == "buruk"):
            result[1]["nilai"] = max(hasil["nilai"], result[1]["nilai"])
        if (hasil["label"] == "biasa"):
            result[2]["nilai"] = max(hasil["nilai"], result[2]["nilai"])
        if (hasil["label"] == "baik"):
            result[3]["nilai"] = max(hasil["nilai"], result[3]["nilai"])
        if (hasil["label"] == "sangat baik"):
            result[4]["nilai"] = max(hasil["nilai"], result[4]["nilai"])

    # print(result)
    return result


def deffuzzyfication(infer_set=[]):
    # print(infer_set)
    val = 0
    pembagi = 0
    for result in infer_set:
        pembagi += result["nilai"]
        if (result["label"] == "sangat buruk"):
            val += 0 * result["nilai"]
        elif (result["label"] == "buruk"):
            val += 1 * result["nilai"]
        elif (result["label"] == "biasa"):
            val += 2 * result["nilai"]
        elif (result["label"] == "baik"):
            val += 3 * result["nilai"]
        elif (result["label"] == "sangat baik"):
            val += 4 * result["nilai"]
    # print("val",val)
    # print("pembagi", pembagi)
    return val / pembagi

######################DEFINE CONTROL & PREDICTION###############
def hitungVol(TinggiAirin):
    if (TinggiAirin > 28.5):
        B = TinggiAirin - 28.5
        A = math.sqrt((28.5**2)-(B**2))
        tanTheta = A/B
        theta = math.degrees(math.atan(tanTheta))
        Ajuring = (theta/360)*math.pi*(28.5**2)
        Atriangle = (A*B)/2
        Atembereng = Ajuring - Atriangle
        volume = Atembereng * 92 * 2
        volumeMl = volume*1000
        return volumeMl
    else:
        B = 28.5 - TinggiAirin
        A = math.sqrt((28.5 ** 2) - (B ** 2))
        tanTheta = A/B
        theta = math.degrees(math.atan(tanTheta))
        Ajuring = (theta / 360) * math.pi * (28.5 ** 2)
        Atriangle = (A*B)/2
        Atembereng = Ajuring - Atriangle
        volume = Atembereng * 92 * 2
        volumeMl = volume * 1000
        return volumeMl


def prediksiNutrisi(EC, VolSaatIni):
    ECsaatini = EC
    ECnutrisi = 178.2555
    ECopt = 1.55
    vol = VolSaatIni

    target = (vol * (ECopt - ECsaatini)) / (ECnutrisi - ECsaatini)
    return target


def prediksiAir(EC, VolSaatIni):
    ECsaatini = EC
    ECair = 0.42
    ECopt = 1.55
    vol = VolSaatIni

    target = (vol * (ECopt - ECsaatini)) / (ECair - ECsaatini)
    return target


# durasi dalam milisecontd

def kontrolEC(volEC):
    qtyEC = volEC
    durasiEC = qtyEC/2 #debit pompa = 1ml/s
    print("Ditambahkan cairan nutrisi sebanyak: ", int(volEC), "Mililiter, selama:", int(durasiEC), " second")
    GPIO.output(RELAIS_1_GPIO, GPIO.LOW)  # on
    GPIO.output(RELAIS_2_GPIO, GPIO.LOW)  # on
    time.sleep(durasiEC)
    GPIO.output(RELAIS_1_GPIO, GPIO.HIGH)
    GPIO.output(RELAIS_2_GPIO, GPIO.HIGH)
    return durasiEC


def kontrolAir(volAir):
    qtyAir = volAir
    durasiAir = qtyAir/62.5 #debit pompa = 500ml/8s = 62.5ml/second
    print("Ditambahkan air sebanyak: ", int(volAir), "Mililiter, selama:", int(durasiAir), " second")
    GPIO.output(RELAIS_3_GPIO, GPIO.LOW)  # on
    time.sleep(durasiAir)
    GPIO.output(RELAIS_3_GPIO, GPIO.HIGH)
    return durasiAir

def kontrolDrain(volSaatIni, volTambah):
    volMax = hitungVol(36)
    volBaru = volSaatIni+volTambah
    if (volBaru > volMax):
        penguranganVol = volSaatIni - volTambah
    else:
        penguranganVol = 0
    durasiDrain = penguranganVol/62.5 #debit pompa = 500ml/8s = 62.5ml/second
    print("Drain sebanyak: ", int(penguranganVol), "Mililiter, selama:", int(durasiDrain), " second")
    GPIO.output(RELAIS_4_GPIO, GPIO.LOW)  # on
    time.sleep(durasiDrain)
    GPIO.output(RELAIS_4_GPIO, GPIO.HIGH)
    return durasiDrain




####################DEFINE SAVE DATA TO CSV##########################
def saveinput(currentTimeStart, ECin, TinggiAirin):
    rowIn = [currentTimeStart, ECin, TinggiAirin]
    with open('input.csv', 'a', newline='') as fd:
        writer = csv.writer(fd)
        writer.writerow(rowIn)
    fd.close()

def saveoutput(currentTimeEnd, outEC, outAir):
    rowOut = [currentTimeEnd, outEC, outAir]
    with open('output.csv', 'a', newline='') as fd:
        writer = csv.writer(fd)
        writer.writerow(rowOut)
    fd.close()

#########################PLOT DATA##################################
def plotinput():
    x = []
    y = []

    with open('input.csv', 'r') as csvfile:
        plots = csv.reader(csvfile, delimiter=',')
        for row in plots:
            x.append(int(row[0]))
            y.append(int(row[1]))

    plt.plot(x, y, marker='o')

    plt.title('Data from the CSV File: People and Expenses')

    plt.xlabel('Number of People')
    plt.ylabel('Expenses')

    plt.show()


##########################DEFINE MQTT##########################
#mqtt_topics = ["input/EC", "input/tinggiAir"]

#define callback
def on_message(client, userdata, message):
    time.sleep(1)
    print("received message =",str(message.payload.decode("utf-8")))
    
def on_connect(client, userdata, flags, rc):
    print("Connected with code:" +str(rc))
    #for topic in mqtt_topics:
    #    client.subscribe(topic)
    client.subscribe("input/#")
        
# EC
def on_message_EC(mosq, obj, msg):
    #print("EC = "+str(msg.payload.decode("utf-8")))
    global ECstr
    global ECin
    ECstr = str(msg.payload.decode("utf-8"))
    ECin = float(ECstr)

    
# Tinggi Air
def on_message_tinggiAir(mosq, obj, msg):
    #print("Tinggi Air= "+str(msg.payload.decode("utf-8")))
    global TinggiAirstr
    global TinggiAirin
    TinggiAirstr = str(msg.payload.decode("utf-8"))
    TinggiAirin = float(TinggiAirstr)


############################## MAIN PROGRAM #####################################
#currentTimeStart = currentDT.strftime("%H:%M:%S")
#print(currentTimeStart)
client = mqtt.Client()
client.on_connect = on_connect
client.message_callback_add("input/EC", on_message_EC)
client.message_callback_add("input/tinggiAir", on_message_tinggiAir)
client.on_message = on_message

client.connect("postman.cloudmqtt.com", 16478, 60)
client.username_pw_set("umekqjds", "_788BdDux1m4")


#client.loop_forever()
client.loop_start()                                          
#time.sleep(1)
while True:
    if (ECin != 0 and TinggiAirin != 0):
        currentDT = datetime.datetime.now()
        currentTimeStart = currentDT.strftime("%d-%m-%Y %H:%M:%S")
        print(currentTimeStart)
        saveinput(currentTimeStart, ECin, TinggiAirin)
        #plotinput()
        print("EC: ", ECin)
        print("Tinggi air: ", TinggiAirin)
        nilai = deffuzzyfication(
            inference(EC_fuzzyfication(ECin), ketinggian_air_fuzzyfication(TinggiAirin)))
        print("y*= ", nilai)

        VolSaatIni = hitungVol(TinggiAirin)
        targetAir = 0
        targetEC = 0

        if (nilai <= 3.2):
            print("")
            print("Cairan yang ditampung harus dikontrol: ")
            print("")
            if (ECin < 1.55):
                targetNutrisi = prediksiNutrisi(ECin, VolSaatIni)
            elif (ECin > 1.55):
                targetAir = prediksiAir(ECin, VolSaatIni)

            # fase kontrol
            if (ECin < 1.55):
                print("Tambah cairan nutrisi")
                outEC = kontrolEC(targetNutrisi)
                outAir = 0
                outDrain = kontrolDrain(VolSaatIni, targetNutrisi)
            elif (ECin > 1.55):
                print("Tambah air")
                outEC = 0
                outAir = kontrolAir(targetAir)
                outDrain = kontrolDrain(VolSaatIni, targetAir)
            print("")
            currentDT = datetime.datetime.now()
            currentTimeEnd = currentDT.strftime("%d-%m-%Y %H:%M:%S")
            print(currentTimeEnd)
            saveoutput(currentTimeEnd, outEC, outAir)


        else:
            print("")
            print("Cairan tak perlu dikontrol")
            outEC = 0
            outAir = 0
            outDrain = 0
            currentDT = datetime.datetime.now()
            currentTimeEnd = currentDT.strftime("%d-%m-%Y %H:%M:%S")
            print(currentTimeEnd)
            saveoutput(currentTimeEnd, outEC, outAir)
    time.sleep(30) #Setting delay disini
    
client.loop_stop()
client.disconnect()

