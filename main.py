print("Startup...")
# init
# using Pygame, nfcpy (required pip install)
import tkinter as tk
from datetime import datetime as dt
import nfc
from threading import Thread as th
from time import sleep
from pygame import mixer as mx
from csv import reader as rdr
from csv import writer as wtr
from os import path as pt
from shutil import copy as cp
from shutil import move as mv


tx_title="電算研 会計/出席"
tx_ver="v1.00"

gray="#444444"
white="#ffffff"
great="#008a00"
info="#0070f0"
warn="#807500"
ftal="#cc0000"

AMT = 6000

# flag [main,upd]
FLAG=[True,False]
RPTNUM=[[0,0,0],[0,0]]

# usr_lib
EXT=dict()

# ctdn
CONFIG=60
CNTDN=[False,0,0]
# ReadOK,SID,paid
STID=[False,"",-1]; LATEST=None

# == Card reader ==
class mCardReader(object):
    def on_connect(self, tag):
        global FLAG, EXT, LATEST
        #touched
        stat_update(info,"読み込み中...",
                    "学生証を動かさないでください...","\uf16a")
        # Load Student No. from IC CARD
        try:
            id = tag.identifier
            tag.polling(system_code=0x93B1)
            sc = nfc.tag.tt3.ServiceCode(64, 0x0b)
            bc = nfc.tag.tt3.BlockCode(0, service=0)
            data = tag.read_without_encryption([sc], [bc])

            STID[1] = data.decode('utf-8').lstrip('0').rstrip()[:-2]
            tt = EXT[STID[1]][1]

            if STID[1] in EXT:
                if tt==1:
                    stat_update(warn,"{} さん 支払い済みです".format(EXT[STID[1]][0]),
                                "これ以上の操作は必要ありません","\ue762")
                    LATEST = STID[1] ; mplay("already.mp3")
                elif tt==0 or tt==3:
                    stat_update(warn,"{} さん 出席済みです".format(EXT[STID[1]][0]),
                                "これ以上の操作は必要ありません","\ue762")
                    mplay("already.mp3")
                    if tt == 0 : LATEST = STID[1]
                elif tt== -3:
                    stat_update(great,"{} さん 出席に変更しました".format(EXT[STID[1]][0]),
                                "学生証を離して終了します","\ue762")
                    mplay("great.mp3")
                    logger("+OK+","{} record OK".format(STID[1]))
                    EXT[STID[1]][1] = 3; FLAG[1] = True
                else:
                    stat_update(great,"{} さん こんにちは".format(EXT[STID[1]][0]),
                                "学生証を離すと次へ進みます","\ue10b")
                    mplay("great.mp3")
                    STID[0] = True; checkout(2)
            else:
                stat_update(ftal,"[E13] {} さん 未登録者です".format(STID[1]),
                            "ご利用いただけません","\uee57")
                mplay("forb.mp3")
        except AttributeError:
            mplay("error1.mp3")
            stat_update(warn,"[E10] KIT学生証ではありません",
                        "カードを離してください","\ue1e0")
        except nfc.tag.tt3.Type3TagCommandError:
            mplay("retry.mp3")
            stat_update(warn,"[E11] もう一度やり直してください",
                        "カードを離してください","\uea6a")
        return True

    def read_id(self):
        try:
            stat_update(info,"KIT学生証をかざしてください",
                        "受付できます","\ued5c")
            clf = nfc.ContactlessFrontend('usb')
            try:
                clf.connect(rdwr={'on-connect': self.on_connect})
            finally:
                clf.close()
        except Exception as e:
            print("E01:",e)
            mplay("crit.mp3")
            for i in range(4,-1,-1):
                stat_update(ftal,"[E01] カードリーダー未接続 ({}s)".format(i),
                            "接続を確認してください","\ueb55")
                slp(1)
        slp(.3)
# =================

#tkinter init
root = tk.Tk()
ctrl = tk.Toplevel()
#title setting
root.title(tx_title+" "+tx_ver)
ctrl.title(tx_title+" 判定")
#window size setting
root.geometry("1280x720")
ctrl.geometry("520x640")
#sound setting
mx.init(frequency= 44100)

def slp(time):
	sleep(time if FLAG[0] else 0)

def mplay(addr):
    mx.music.load("snd/"+addr)
    mx.music.play()
		 
def mainSYS():
    global EXT, LATEST
    checkout(2)
    while FLAG[0]:
        STID[0]=False; STID[1]=""; STID[2]=-1
        stat_update(info,"カードリーダ準備中...",
                    "お待ちください","\uf16a")
        if LATEST == None:
            sub_update("待機中")
        else: 
            sub_update("待機中 - 取消可能({})".format(LATEST))
            checkout(0)
    
        mCardReader().read_id()
        if not(STID[0]): continue

        STID[2]=EXT[STID[1]][1]
        CNTDN[0] = True; CNTDN[1] = CONFIG; CNTDN[2] = 0
        checkout(True)
        stat_update(info,"支払い待機中...",
                    "金額は {} 円です".format(AMT),"\ue8ef")
        sub_update("{}({}) さん".format(EXT[STID[1]][0],STID[1]))
        while CNTDN[0]:
            slp(.3)

        EXT[STID[1]][1] = STID[2]
        if STID[2]!=-1 :
            FLAG[1] = True
            LATEST = STID[1]
            
        checkout(2)
        slp(.3)

def paymentBT(e):
    global LATEST
    if e==1:
        stat_update(great,"支払いが完了しました",
                    "毎度ありがとうございます","\ue10b")
        print("R:  {} payment OK".format(STID[1]))
        logger("-OK-","{} payment OK".format(STID[1]))
        mplay("ok.mp3")
        CNTDN[1] = 2; STID[2] = 1
    elif e==2:
        stat_update(warn,"未払いで処理されました",
                    "出席を登録しました","\ue7ba")
        print("R:! {} record OK".format(STID[1]))
        logger("WARN","{} record OK".format(STID[1]))
        mplay("error2.mp3")
        CNTDN[1] = 2; STID[2] = 0
    elif e==3:
        stat_update(ftal,"取り消しました",
                    "もう一度 やり直してください","\uea6a")
        print("R:# {} status reseted".format(LATEST))
        logger("#CL#","{} status reseted".format(LATEST))
        mplay("error3.mp3")

        sub_update("取り消しました")
        EXT[LATEST][1] = -1
        FLAG[1] = True
        LATEST = None
    checkout(2)


def checkout(stat):
    if stat == 2:
        cbtn1.config(state=tk.DISABLED)
        cbtn2.config(state=tk.DISABLED)
        cbtn4.config(state=tk.DISABLED)
    elif stat:
        cbtn1.config(state=tk.NORMAL)
        cbtn2.config(state=tk.NORMAL)
        cbtn4.config(state=tk.DISABLED)
    else:
        cbtn1.config(state=tk.DISABLED)
        cbtn2.config(state=tk.DISABLED)
        cbtn4.config(state=tk.NORMAL)
    
def upload():
    global A_NUM,EXT,RPTNUM
    # 前処理
    try:
        # 名簿読み込み
        upld_update("(1/2) List Loading...")
        with open("stat.csv") as f:
            for row in rdr(f):
                EXT = {**EXT, row[0]:[ row[1], int(row[2]) ]}
        print("F: List Load OK")
        cp("stat.csv","stat.csv.old")

        # 事前報告記録を確認
        upld_update("(2/2) Checking external...")
        if pt.isfile("external.csv"):
            with open("external.csv") as f:
                for row in rdr(f):
                    EXT[row[0]][1] = -2
                print("F: External check OK")
            mv("external.csv","external.csv.old")
        else:
            print("F: No external file")

    except Exception as e:
        ex="W: "+str(e)
        print(ex)
        for i in range(len(ex)+1):
            upld_update(ex[i:i+40])
            slp(3 if i == 0 else .3)
    finally:
        FLAG[1] = True
        print("F: Ready")
    
    # メインループ
    while FLAG[0] or FLAG[1]:
        if FLAG[1]:
            try:
                FLAG[1] = False
                RPTNUM=[[0,0,0],[0,0]]
                upld_update("Writing...")
                with open("stat.csv",mode="w",encoding="cp932",newline="") as f:
                    for i in EXT:
                        wtr(f).writerow( [i, EXT[i][0], EXT[i][1]] )
                        if EXT[i][1] == 1 : RPTNUM[0][0] += 1
                        if EXT[i][1] == 0 : RPTNUM[0][1] += 1
                        if EXT[i][1] <= -2: RPTNUM[0][2] -= 1
                        if EXT[i][1] >= 0 : RPTNUM[1][0] += 1
                RPTNUM[0][1] += RPTNUM[0][0]
                RPTNUM[1][1] = len(EXT)
                RPTNUM[0][2] += RPTNUM[1][1]
                upld_update("Write OK")
                
                slp(3)
            except Exception as e:
                ex="E51: "+str(e)
                print(ex)
                for i in range(len(ex)+1):
                    upld_update(ex[i:i+40])
                    slp(3 if i == 0 else .3)
        else:
            upld_update("Ready")
            slp(3) 

def logger(pfix,msg):
    with open("log/{}.log".format(dt.date(dt.now())),mode="a",encoding="cp932") as f:
        f.write("[{}] {} {}\n".format(dt.now().strftime('%H:%M:%S'), pfix, msg))

#tk Alway update
def alway_update():
    if CNTDN[0]:
        if CNTDN[2] >= 10:
            CNTDN[2] = 0
            CNTDN[1] -= 1
            if CNTDN[1] <= 0 : CNTDN[0]=False
        countS.config(text=CNTDN[1])
        CNTDN[2]+=1
    else:
        countS.config(text="")
    dateS.config(text=dt.now().strftime('%Y/%m/%d %H:%M:%S'))
    upldSR.config(text="Amount: {}k  Status: {}/{}/{} ({}/{})".format(
        AMT/1000*RPTNUM[0][0],
        RPTNUM[0][0],RPTNUM[0][1],RPTNUM[0][2],
        RPTNUM[1][0],RPTNUM[1][1]))

    if ctrl != None and not(ctrl.winfo_exists()): root.destroy()
    root.after(100,alway_update)


#Main label update
def stat_update(color,mes,mes2,icon):
    if not(FLAG[0]) : return
    statS.config(text=mes,bg=color)
    statF.config(bg=color)
    mainS.config(text=icon,bg=color)
    mainF.config(bg=color)
    statS2.config(text=mes2,bg=color)
#Sub label update
def upld_update(p1):
	if not(FLAG[0]) : return
	upldSL.config(text=p1)
def sub_update(p1):
    if not(FLAG[0]) : return
    cMtx.config(text=p1)

# Frame init
titleF = tk.Frame(root)
titleF.pack(fill=tk.X)
countF = tk.Frame(titleF)
countF.pack(side=tk.RIGHT)

dateF = tk.Frame(root,bg=gray)
dateF.pack(side= tk.BOTTOM,fill=tk.X)

upldF = tk.Frame(root)
upldF.pack(side= tk.BOTTOM,fill=tk.X)
upldFR =tk.Frame(upldF,bg=gray)
upldFR.pack(side=tk.RIGHT)
upldFL =tk.Frame(upldF,bg=gray)
upldFL.pack(fill=tk.X)

statF = tk.Frame(root,bg=info)
statF.pack(side= tk.BOTTOM,fill=tk.X)

mainF = tk.Frame(root,bg=info)
mainF.pack(fill=tk.BOTH,expand=True)

# ラベル表示
titleS = tk.Label(titleF, text=(tx_title+" "+tx_ver),
    font=("Segoe UI", "32"))
titleS.pack(side=tk.LEFT)

countS = tk.Label(countF, text=("99"),
    font=("Segoe UI", "32"))
countS.pack(side=tk.RIGHT)

dateS = tk.Label(dateF, text="----/--/-- --:--",
    font=("Consolas", "14"),
    fg=white,bg=gray)
dateS.pack(expand=True)

upldSL = tk.Label(upldFL, text="Startup...",
    font=("Consolas","14"),
    fg=white,bg=gray)
upldSL.pack(side=tk.LEFT)
upldSR = tk.Label(upldFR, text="---/---",
    font=("Consolas","14"),
    fg=white,bg=gray)
upldSR.pack(side=tk.RIGHT)


statS2 = tk.Label(statF, text="お待ちください",
    font=("Segoe UI","18"),
    fg=white,bg=info)
statS2.pack(side=tk.BOTTOM,fill=tk.X)
statS = tk.Label(statF, text="起動中",
    font=("Segoe UI","24"),
    fg=white,bg=info)
statS.pack(expand=True)

mainS = tk.Label(mainF,text="\uf16a",
    font=("Segoe MDL2 Assets",220),
    fg=white,bg=info)
mainS.pack(expand=True)

cMtx = tk.Label(ctrl, text="お待ちください",
    font=("Segoe UI","18"))
cMtx.pack(side=tk.TOP,fill=tk.X)

cbtn1 = tk.Button(ctrl, text="支払完了",
    font=("HGS創英角ﾎﾟｯﾌﾟ体",64),
    fg=white,bg=info,command=lambda: paymentBT(1),
    activeforeground=white,activebackground=gray)
cbtn1.pack(side= tk.TOP,fill=tk.BOTH,expand=True)

cbtn4 = tk.Button(ctrl, text="やっぱ 今の無し",
    font=("Segoe UI","24"),
    fg=white,bg=gray,command=lambda: paymentBT(3),
    activeforeground=gray,activebackground=white)
cbtn4.pack(side=tk.BOTTOM,fill=tk.X)

cbtn2 = tk.Button(ctrl, text="未払い",
    font=("HGS創英角ﾎﾟｯﾌﾟ体","76"),
    fg=white,bg=ftal,command=lambda: paymentBT(2),
    activeforeground=white,activebackground=gray)
cbtn2.pack(side=tk.BOTTOM,fill=tk.BOTH)

# alway start
alway_update()

print("----------------\n")

# SYSTEM start
thr1 = th(target=mainSYS)
thr1.start()
thr2 = th(target=upload)
thr2.start()

# Disp start
root.mainloop()

# shutdown
print("\n----------------")
print("Shutdown...")
print("Please disconnect NFC reader.")
FLAG[0] = False

thr2.join(); print("S: Record shutdown OK")
thr1.join(); print("S: NFC shutdown OK")

mx.quit()
print()