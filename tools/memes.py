import random, numpy as np
from PIL import Image, ImageDraw, ImageFont
W,H=1200,675
B='/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf'
R='/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf'
RED=(235,26,41); CY=(0,217,230); WH=(240,240,240); GR=(120,120,120); BK=(10,10,10)
random.seed(7); np.random.seed(7)
F=lambda p,s: ImageFont.truetype(p,s)

def base():
    a=np.random.normal(12,6,(H,W,1)).clip(0,40).repeat(3,2)
    im=Image.fromarray(a.astype('uint8')); d=ImageDraw.Draw(im)
    d.text((24,H-34),'NOW ONLY LIES',font=F(B,16),fill=RED)
    d.text((W-24,H-34),'#FallInNOL',font=F(R,16),fill=GR,anchor='ra')
    return im,d

def gtext(d,xy,t,font,fill=WH,anchor='la',off=3):
    x,y=xy
    d.text((x-off,y),t,font=font,fill=CY,anchor=anchor)
    d.text((x+off,y+1),t,font=font,fill=RED,anchor=anchor)
    d.text((x,y),t,font=font,fill=fill,anchor=anchor)

def wrap(d,t,font,mw):
    out=[];line=''
    for w in t.split():
        c=(line+' '+w).strip()
        if d.textlength(c,font=font)<=mw: line=c
        else: out.append(line); line=w
    out.append(line); return out

# 1 system alert
im,d=base()
bx=(170,120,1030,520)
d.rectangle(bx,fill=(24,24,24),outline=WH,width=3)
d.rectangle((170,120,1030,172),fill=RED)
d.text((190,146),'SYSTEM NOTICE',font=F(B,26),fill=BK,anchor='lm')
d.text((1010,146),'X',font=F(B,26),fill=BK,anchor='rm')
d.text((600,255),"\"this is a scam\"",font=F(B,50),fill=WH,anchor='mm')
gtext(d,(600,330),"= a lie.",F(B,64),RED,'mm')
d.text((600,395),'Reason: read the title.',font=F(R,28),fill=GR,anchor='mm')
for x,t in((420,'OK'),(780,'OK')):
    d.rectangle((x-90,440,x+90,495),fill=WH); d.text((x,468),t,font=F(B,28),fill=BK,anchor='mm')
im.save('m1.png')

# 2 search bar
im,d=base()
d.rounded_rectangle((120,170,1080,260),radius=45,fill=(30,30,30),outline=GR,width=2)
d.text((170,215),'what is NOL',font=F(R,38),fill=WH,anchor='lm')
d.text((1040,215),'⌕',font=F(B,40),fill=GR,anchor='rm')
d.text((150,330),'About 0 results (0.00 seconds)',font=F(R,24),fill=GR)
d.text((150,385),'Did you mean:',font=F(R,30),fill=WH)
gtext(d,(150,430),"don't.",F(B,70),RED,'la')
d.text((150,540),'Rule 5: never explain.',font=F(R,28),fill=GR)
im.save('m2.png')

# 3 page 7 / page 8
im,d=base()
d.text((60,60),'PAGE 7',font=F(B,34),fill=GR)
d.text((60,115),'"The secret is on the next page."',font=F(R,36),fill=WH)
d.text((60,260),'PAGE 8',font=F(B,34),fill=RED)
y=320
for i in range(9):
    h=random.randint(14,40); s=random.randint(-120,160)
    c=random.choice([(235,26,41),(0,217,230),(60,60,60),(240,240,240),(30,30,30)])
    d.rectangle((60+max(s,0),y,W-60+min(s,0),y+h),fill=c); y+=h+random.randint(3,10)
d.text((W//2,610),'…still here?',font=F(B,34),fill=GR,anchor='mm')
im.save('m3.png')

# 4 2x2 grid
im,d=base()
gtext(d,(W//2,60),"THERE'S NO WINNING",F(B,52),WH,'mm',3)
cells=[('Call it a scam',"you're lying"),('Call it genius','you fell in NOL'),('Ignore it','it\'s in your head'),('Google it','you\'re already in')]
for i,(a,b) in enumerate(cells):
    x=60+(i%2)*560; y=130+(i//2)*250
    d.rectangle((x,y,x+520,y+220),fill=(22,22,22),outline=RED if i%2 else GR,width=3)
    d.text((x+260,y+75),a,font=F(R,34),fill=GR,anchor='mm')
    d.text((x+260,y+145),b,font=F(B,40),fill=RED if i%2 else WH,anchor='mm')
im.save('m4.png')

# 5 tiers
im,d=base()
tiers=[('Find the secret',(35,35,35),GR),('Pay for the secret',(55,20,22),WH),('Look for it on page 8',(110,15,22),WH),('There is no secret.',RED,BK)]
for i,(t,bg,fg) in enumerate(tiers):
    y=40+i*150
    d.rectangle((60,y,W-60,y+130),fill=bg)
    d.text((100,y+65),str(i+1),font=F(B,60),fill=fg,anchor='lm')
    d.text((200,y+65),t,font=F(B,44),fill=fg,anchor='lm')
im.save('m5.png')
